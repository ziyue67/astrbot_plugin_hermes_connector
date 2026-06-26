"""
待审批权限请求管理
管理 Hermes 远程操作的审批队列，支持 LLM 工具和指令触发
"""

import asyncio
import uuid
import time
import logging

logger = logging.getLogger("astrbot")


class PendingManager:
    """管理待审批的 Hermes 操作请求"""

    def __init__(self):
        # pending[window_id] = {request_id: request_data}
        self.pending: dict[str, dict[str, dict]] = {}
        self._next_index: int = 1
        self._freed_indices: list[int] = []
    
    def allocate_index(self) -> int:
        """分配一个审批序号"""
        if self._freed_indices:
            return self._freed_indices.pop(0)
        idx = self._next_index
        self._next_index += 1
        return idx
    
    def free_index(self, index: int):
        """释放一个序号供复用"""
        if index not in self._freed_indices:
            self._freed_indices.append(index)
            self._freed_indices.sort()
    
    def add_request(self, window_id: str, tool_name: str, args: dict,
                    timeout: float = 120.0) -> tuple[str, asyncio.Future, int]:
        """
        添加一个审批请求。
        
        Returns:
            (request_id, future, index)
        """
        req_id = f"hermes_{uuid.uuid4().hex[:8]}"
        future = asyncio.Future()
        index = self.allocate_index()
        
        request = {
            "tool": tool_name,
            "arguments": args,
            "type": "hermes_tool",
            "future": future,
            "index": index,
            "created_at": time.time(),
            "timeout": timeout,
        }
        
        if window_id not in self.pending:
            self.pending[window_id] = {}
        self.pending[window_id][req_id] = request
        
        logger.debug(f"审批请求已添加: window={window_id[:12]} tool={tool_name} idx={index}")
        return req_id, future, index
    
    def remove_entry(self, window_id: str, req_id: str):
        """移除一个待审批条目"""
        if window_id in self.pending and req_id in self.pending[window_id]:
            req = self.pending[window_id][req_id]
            idx = req.get("index", 0)
            if idx > 0:
                self.free_index(idx)
            del self.pending[window_id][req_id]
            if not self.pending[window_id]:
                del self.pending[window_id]
    
    def get_pending_for_window(self, window_id: str) -> dict[str, dict]:
        """获取指定窗口的待审批请求"""
        return self.pending.get(window_id, {})
    
    def flatten_pending(self, window_id: str | None = None) -> list[tuple[str, str, dict]]:
        """
        展平待审批请求为 [(window_id, req_id, req), ...]
        如果 window_id 为 None，返回所有窗口的请求
        """
        items = []
        targets = [window_id] if window_id else list(self.pending.keys())
        for wid in targets:
            if wid in self.pending:
                for rid, req in self.pending[wid].items():
                    items.append((wid, rid, req))
        return items
    
    async def require_approval(self, window_id: str, tool_name: str,
                                args: dict, event_sender,
                                timeout: float = 60.0) -> tuple[bool, str]:
        """
        请求用户审批，等待结果。
        
        Returns:
            (approved, reason)
            approved=True: 用户批准
            reason: "approved" / "denied" / "timeout" / "notification_failed"
        """
        req_id, future, index = self.add_request(window_id, tool_name, args, timeout)
        
        # 计算统计信息
        items = self.flatten_pending(window_id)
        total = len(items)
        
        # 构建通知消息
        args_str = ", ".join(f"{k}={v}" for k, v in args.items())
        msg = (
            f"🛡️ **操作审批请求**\n"
            f"操作: {tool_name}\n"
            f"参数: {args_str}\n\n"
            f"共 {total} 个待审批，此请求序号 {index}\n\n"
            f"审批指令:\n"
            f"  `/hermes a` — 全部批准\n"
            f"  `/hermes allow {index}` — 批准此请求\n"
            f"  `/hermes deny` — 全部拒绝\n"
            f"  `/hermes deny {index}` — 拒绝此请求\n"
            f"  `/hermes pending` — 查看待审批列表"
        )
        
        notification_sent = False
        try:
            await event_sender(msg)
            notification_sent = True
        except Exception as e:
            logger.warning(f"审批通知发送失败: {e}")
        
        if not notification_sent:
            self.remove_entry(window_id, req_id)
            return False, "notification_failed"
        
        try:
            approved = await asyncio.wait_for(future, timeout=timeout)
            return (True, "approved") if approved else (False, "denied")
        except asyncio.TimeoutError:
            self.remove_entry(window_id, req_id)
            logger.warning(f"审批超时: {tool_name} ({timeout}s)")
            return False, "timeout"
        except asyncio.CancelledError:
            self.remove_entry(window_id, req_id)
            return False, "cancelled"
    
    async def approve_all(self, window_id: str, event_sender=None) -> str | None:
        """
        批准指定窗口的所有非 question 请求。
        """
        items = self.flatten_pending(window_id)
        if not items:
            return None
        
        regular = [(wid, rid, req) for wid, rid, req in items
                   if req.get("type") not in ("question",)]
        if not regular:
            return None
        
        # 先设置 Future 结果
        for wid, rid, req in regular:
            future = req.get("future")
            if future and not future.done():
                future.set_result(True)
        
        # 清理条目
        success_count = 0
        for wid, rid, _ in regular:
            self.remove_entry(wid, rid)
            success_count += 1
        
        return f"✅ 已批准 {success_count} 项" if success_count > 0 else None
    
    async def approve_single(self, window_id: str, index: int) -> bool:
        """批准指定序号的请求"""
        items = self.flatten_pending(window_id)
        for wid, rid, req in items:
            if req.get("index") == index:
                future = req.get("future")
                if future and not future.done():
                    future.set_result(True)
                self.remove_entry(wid, rid)
                return True
        return False
    
    async def deny_all(self, window_id: str) -> str | None:
        """拒绝指定窗口的所有请求"""
        items = self.flatten_pending(window_id)
        if not items:
            return None
        
        for wid, rid, req in items:
            future = req.get("future")
            if future and not future.done():
                future.set_result(False)
            self.remove_entry(wid, rid)
        
        return f"❌ 已拒绝 {len(items)} 项"
    
    async def deny_single(self, window_id: str, index: int) -> bool:
        """拒绝指定序号的请求"""
        items = self.flatten_pending(window_id)
        for wid, rid, req in items:
            if req.get("index") == index:
                future = req.get("future")
                if future and not future.done():
                    future.set_result(False)
                self.remove_entry(wid, rid)
                return True
        return False
    
    def get_summary(self, window_id: str) -> str:
        """获取待审批列表的文本摘要"""
        items = self.flatten_pending(window_id)
        if not items:
            return "📭 当前没有待审批的请求。"
        
        lines = ["🛡️ **待审批请求**:", ""]
        for wid, rid, req in items:
            idx = req.get("index", "?")
            tool = req.get("tool", "?")
            args = req.get("arguments", {})
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            created = req.get("created_at", 0)
            age = int(time.time() - created) if created else 0
            lines.append(f"  #{idx} | {tool} | {args_str[:60]} | {age}s")
        
        lines.extend([
            "",
            f"共 {len(items)} 项待审批",
            "`/hermes a` — 全部批准  |  `/hermes deny` — 全部拒绝",
        ])
        return "\n".join(lines)
