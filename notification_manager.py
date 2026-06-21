"""
通知管理器
将 Hermes 事件推送到 AstrBot 聊天窗口
"""

import logging
from typing import Any

from astrbot.api import logger
from astrbot.api.message_components import Plain

logger = logging.getLogger("astrbot")


class NotificationManager:
    """管理通知推送和消息分发"""
    
    def __init__(self, context, state_mgr):
        self.context = context
        self.state_mgr = state_mgr
    
    async def push_notification(self, text: str, session_id: str | None = None) -> None:
        """
        推送通知到合适的聊天窗口。
        目前采用简单模式: 仅记录日志。
        未来可以扩展到按绑定规则推送到特定窗口。
        """
        if not text:
            return
        
        logger.info(f"[Hermes 通知] session={session_id}: {text[:100]}...")
    
    async def send_to_window(self, window_id: str, text: str) -> None:
        """
        发送消息到指定聊天窗口。
        通过 AstrBot 的 context.send_message() 实现。
        """
        if not text:
            return
        
        try:
            # 查找对应的平台会话
            from astrbot.core.star.star_handler import star_handlers_registry
            # 遍历平台实例，找到匹配的窗口
            for platform in getattr(self.context, '_platform_manager', {}).get('platform_insts', []):
                try:
                    sessions = getattr(platform, 'sessions', {})
                    for session in sessions.values():
                        if getattr(session, 'session_id', None) == window_id:
                            from astrbot.api.event import MessageChain
                            await platform.send_by_session(
                                session, 
                                [Plain(text)]
                            )
                            return
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"发送到窗口失败: {e}")
