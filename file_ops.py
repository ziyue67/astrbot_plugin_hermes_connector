"""
文件操作
通过 Hermes CLI 进行文件查询和下载
"""

import logging
from typing import Any

from .hermes_cli_client import chat, HermesCliError

logger = logging.getLogger("astrbot")


async def list_files(path: str = ".", session_id: str | None = None,
                     binary: str | None = None) -> list[str]:
    """
    列出指定路径的文件（通过 Hermes 读取）
    """
    try:
        result = await chat(
            f"List files in directory: {path}. "
            f"Return ONLY the file names, one per line. "
            f"Do not include any other text.",
            session_id=session_id,
            timeout=30,
            binary=binary,
        )
        lines = [l.strip() for l in result["response"].split("\n") if l.strip()]
        return [l for l in lines if not l.startswith("total ") and "drwx" not in l and "Permission denied" not in l]
    except Exception as e:
        logger.warning(f"列出文件失败: {e}")
        return []


async def search_files(keyword: str, path: str = ".",
                       binary: str | None = None) -> list[str]:
    """
    搜索文件（通过 Hermes 执行 find/rg）
    """
    try:
        result = await chat(
            f"Search for files matching '{keyword}' under path {path}. "
            f"Return ONLY matching file paths, one per line.",
            timeout=30,
            binary=binary,
        )
        lines = [l.strip() for l in result["response"].split("\n") if l.strip()]
        return lines
    except Exception as e:
        logger.warning(f"搜索文件失败: {e}")
        return []


async def read_file_content(path: str, session_id: str | None = None,
                             binary: str | None = None) -> str | None:
    """
    读取文件内容（通过 Hermes 读取）
    """
    try:
        result = await chat(
            f"Read the content of file: {path}",
            session_id=session_id,
            timeout=30,
            binary=binary,
        )
        return result["response"]
    except Exception as e:
        logger.warning(f"读取文件失败: {e}")
        return None
