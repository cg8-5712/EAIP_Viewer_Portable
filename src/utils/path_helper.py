"""
Path Helper - 路径解析工具
用于处理开发环境和打包环境中的路径差异
"""

import sys
from pathlib import Path


def get_app_root() -> Path:
    """
    获取应用程序根目录

    Returns:
        应用程序根目录路径

    说明:
        - 打包环境: 返回可执行文件所在目录
        - 开发环境: 返回项目根目录
    """
    if getattr(sys, "frozen", False):
        # 打包环境：使用可执行文件所在目录
        app_root = Path(sys.executable).parent
    else:
        # 开发环境：向上两级到项目根目录
        # path_helper.py -> utils/ -> src/ -> project_root/
        app_root = Path(__file__).parent.parent.parent

    return app_root


def get_config_dir() -> Path:
    """
    获取配置目录

    Returns:
        配置目录路径
    """
    config_dir = get_app_root() / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """
    获取数据目录

    Returns:
        数据目录路径
    """
    data_dir = get_app_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cache_dir() -> Path:
    """
    获取缓存目录

    Returns:
        缓存目录路径
    """
    cache_dir = get_app_root() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_logs_dir() -> Path:
    """
    获取日志目录

    Returns:
        日志目录路径
    """
    logs_dir = get_app_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def resolve_relative_path(relative_path: str) -> Path:
    """
    解析相对路径为绝对路径

    Args:
        relative_path: 相对路径（相对于应用根目录）

    Returns:
        绝对路径

    示例:
        resolve_relative_path("./config/settings.json")
        resolve_relative_path("data/2505/Terminal")
    """
    path = Path(relative_path)

    # 如果已经是绝对路径，直接返回
    if path.is_absolute():
        return path

    # 相对路径，基于应用根目录解析
    return get_app_root() / path


def get_config_file_path() -> Path:
    """
    获取配置文件路径

    Returns:
        settings.json 的完整路径
    """
    return get_config_dir() / "settings.json"
