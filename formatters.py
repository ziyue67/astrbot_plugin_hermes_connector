"""
输出格式化工具
"""

import html
import re
from typing import Any


def format_session_list(sessions: list[dict]) -> str:
    """格式化会话列表为美观的文本"""
    if not sessions:
        return "📭 当前没有 Hermes 会话。"
    
    lines = [
        "📋 **Hermes 会话列表**",
        "",
        f"| # | 标题 | 预览 | 最近活跃 | ID",
        "|---|------|------|----------|---"
    ]
    
    for i, s in enumerate(sessions, 1):
        title = s.get("title") or "—"
        preview = s.get("preview") or "—"
        last_active = s.get("last_active") or "—"
        sid = s.get("id", "")[:12] + "..."
        
        # 截断长文本
        if len(title) > 20:
            title = title[:18] + "…"
        if len(preview) > 30:
            preview = preview[:28] + "…"
        
        lines.append(f"| {i} | {title} | {preview} | {last_active} | `{sid}`")
    
    return "\n".join(lines)


def format_session_status(session_id: str, detail: dict | None = None) -> str:
    """格式化单个会话的详细信息"""
    if not detail:
        return f"📊 **会话** `{session_id[:16]}...`\n(无法获取详细信息)"
    
    model = detail.get("model") or "unknown"
    msg_count = detail.get("message_count", 0)
    started = detail.get("started_at")
    title = detail.get("title") or "未命名"
    source = detail.get("source") or "unknown"
    
    parts = [
        f"📊 **Hermes 会话详情**",
        f"",
        f"- **会话ID**: `{session_id}`",
        f"- **标题**: {title}",
        f"- **模型**: {model}",
        f"- **消息数**: {msg_count}",
        f"- **来源**: {source}",
    ]
    
    if started:
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(started)
            parts.append(f"- **创建时间**: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception:
            pass
    
    return "\n".join(parts)


def format_response(session_id: str, response: str, is_new: bool = False) -> str:
    """格式化 Hermes 回复"""
    prefix = "🆕 **新会话**" if is_new else "💬 **回复**"
    return (
        f"{prefix}: `{session_id[:16]}...`\n\n"
        f"{response}"
    )


def truncate(text: str, max_len: int = 1500) -> str:
    """截断长文本"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n\n…(截断，共 {len(text)} 字符)"


def escape_markdown(text: str) -> str:
    """转义 Markdown 特殊字符（用于 Telegram 等平台）"""
    # 保留代码块
    text = re.sub(r"(```)", "```", text)
    # 转义其他特殊字符
    special_chars = r"\_*[]()~`>#+-=|{}!"
    for c in special_chars:
        text = text.replace(c, "\\" + c)
    return text


def format_error(error: str) -> str:
    """格式化错误消息"""
    return f"❌ **Hermes 错误**: {error}"


def format_file_list(files: list[str], path: str = "") -> str:
    """格式化文件列表"""
    if not files:
        return f"📁 `{path}`\n(空目录)"
    
    lines = [f"📁 **{path}**", ""]
    for f in files[:30]:
        lines.append(f"- {f}")
    if len(files) > 30:
        lines.append(f"\n…还有 {len(files) - 30} 个文件")
    
    return "\n".join(lines)


def format_help() -> str:
    """格式化帮助信息"""
    return """🤖 **Hermes Agent 远程控制** - 帮助

**会话管理:**
• `/hermes list` — 查看所有会话
• `/hermes sw <序号或ID>` — 切换当前会话
• `/hermes status [序号]` — 查看会话状态
• `/hermes msg [轮数]` — 查看最近消息
• `/hermes rename <名称>` — 重命名当前会话

**消息发送:**
• `/hermes to <序号> <内容>` — 发送到指定会话
• `> 内容` — 快捷发送到当前会话
• `>N 内容` — 发送到第 N 个会话

**会话创建:**
• `/hermes create <提示词>` — 创建新会话
• `/hermes create <提示词> --model <模型>` — 指定模型创建

**其他:**
• `/hermes health` — 检查 Hermes 连接状态
• `/hermes help` — 显示此帮助
"""
