"""日志和错误处理配置。"""

import logging
import sys

from backend.config import settings


def setup_logging() -> None:
    """配置全局日志。"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """获取日志器。"""
    return logging.getLogger(name)
