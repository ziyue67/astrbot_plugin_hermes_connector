"""
状态管理器
管理每个聊天窗口的当前会话、绑定关系
"""

import logging
from typing import Any

logger = logging.getLogger("astrbot")


class WindowState:
    """单个聊天窗口的状态"""
    
    def __init__(self, window_id: str):
        self.window_id = window_id
        self.current_session_id: str | None = None
        self.current_session_idx: int | None = None  # 最近一次 list 中的序号
        
    def to_dict(self) -> dict:
        return {
            "window_id": self.window_id,
            "current_session_id": self.current_session_id,
            "current_session_idx": self.current_session_idx,
        }


class StateManager:
    """管理所有聊天窗口的 Hermes 会话状态"""
    
    def __init__(self):
        self._windows: dict[str, WindowState] = {}
        self._sessions_cache: list[dict] = []
        self._hermes_health: dict | None = None
        
    def get_or_create_window(self, window_id: str) -> WindowState:
        """获取或创建窗口状态"""
        if window_id not in self._windows:
            self._windows[window_id] = WindowState(window_id)
        return self._windows[window_id]
    
    def set_current_session(self, window_id: str, session_id: str, idx: int | None = None):
        """设置当前窗口的活跃会话"""
        state = self.get_or_create_window(window_id)
        state.current_session_id = session_id
        state.current_session_idx = idx
        logger.debug(f"窗口 {window_id[:20]}... 切换到会话 {session_id[:16]}...")
    
    def get_current_session(self, window_id: str) -> str | None:
        """获取当前窗口的活跃会话 ID"""
        return self._windows.get(window_id, None) and self._windows[window_id].current_session_id
    
    def update_sessions_cache(self, sessions: list[dict]):
        """更新全局会话缓存"""
        self._sessions_cache = sessions
    
    def get_sessions_cache(self) -> list[dict]:
        return self._sessions_cache
    
    def get_session_by_idx(self, idx: int) -> dict | None:
        """通过序号（1-based）获取会话"""
        if 1 <= idx <= len(self._sessions_cache):
            return self._sessions_cache[idx - 1]
        return None
    
    def find_session_by_id_prefix(self, prefix: str) -> dict | None:
        """通过 ID 前缀查找会话"""
        for s in self._sessions_cache:
            sid = s.get("id", "")
            if sid.startswith(prefix):
                return s
        return None
    
    def set_hermes_health(self, health: dict | None):
        self._hermes_health = health
    
    def get_hermes_health(self) -> dict | None:
        return self._hermes_health
    
    def to_dict(self) -> dict:
        return {
            "windows": {k: v.to_dict() for k, v in self._windows.items()},
            "sessions_count": len(self._sessions_cache),
        }
