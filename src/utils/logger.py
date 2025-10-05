"""
日志模块 - 统一日志管理
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    """日志管理器"""

    _loggers = {}

    @staticmethod
    def setup(log_dir: str = "logs", level: int = logging.DEBUG):
        """
        配置日志系统

        Args:
            log_dir: 日志目录
            level: 日志级别
        """
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 创建日志文件名（按日期）
        log_file = log_path / f"eaip_viewer_{datetime.now().strftime('%Y%m%d')}.log"

        # 配置根日志
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # 清除已有的处理器
        root_logger.handlers.clear()

        # 文件处理器（支持轮转，最大 10MB，保留 5 个备份）
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(level)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 日志格式
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        logging.info("=" * 60)
        logging.info("EAIP Viewer 启动")
        logging.info(f"日志文件: {log_file}")
        logging.info("=" * 60)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 模块名称

        Returns:
            日志记录器
        """
        if name not in Logger._loggers:
            Logger._loggers[name] = logging.getLogger(name)
        return Logger._loggers[name]
