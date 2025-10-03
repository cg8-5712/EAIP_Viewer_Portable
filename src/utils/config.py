"""
Configuration Manager - 配置管理
"""

from PySide6.QtCore import QObject, Signal, Property, Slot
from pathlib import Path
import json
import os
from typing import Any, Dict


class Config(QObject):
    """配置管理器"""

    configChanged = Signal(str, object)  # 配置项名称, 新值

    # 默认配置
    DEFAULT_CONFIG = {
        "data_path": "./data",
        "cache_path": "./cache",
        "max_pins": 10,
        "pdf_render_dpi": 150,
        "language": "zh_CN",
        "theme": {
            "mode": "light",
            "accent_color": "aviation_blue"
        },
        "splash_screen": {
            "enabled": True,
            "min_display_time": 1500
        },
        "import": {
            "max_workers": "auto",  # "auto" 或具体数字
            "auto_workers_ratio": 0.5  # 自动模式下使用 CPU 线程数的比例（默认50%）
        }
    }

    def __init__(self, config_file: str = "./config/settings.json", parent=None):
        super().__init__(parent)
        self._config_file = Path(config_file)
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self):
        """从文件加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                    # 合并默认配置（处理新增的配置项）
                    self._config = self._merge_config(self.DEFAULT_CONFIG, self._config)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            # 使用默认配置
            self._config = self.DEFAULT_CONFIG.copy()
            # 创建配置文件
            self.save()

    def save(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self._config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存配置失败: {e}")

    def _merge_config(self, default: dict, user: dict) -> dict:
        """
        合并配置（保留用户配置，添加默认配置中的新项）

        Args:
            default: 默认配置
            user: 用户配置

        Returns:
            合并后的配置
        """
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键，如 "theme.mode"）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        # 遍历到倒数第二层
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value
        self.configChanged.emit(key, value)

    def reset(self):
        """重置为默认配置"""
        self._config = self.DEFAULT_CONFIG.copy()
        self.save()

    # QML 属性
    @Property(str)
    def language(self):
        return self.get('language', 'zh_CN')

    @language.setter
    def language(self, value: str):
        self.set('language', value)
        self.save()

    @Property(str)
    def themeMode(self):
        return self.get('theme.mode', 'light')

    @themeMode.setter
    def themeMode(self, value: str):
        self.set('theme.mode', value)
        self.save()

    @Property(str)
    def accentColor(self):
        return self.get('theme.accent_color', 'aviation_blue')

    @accentColor.setter
    def accentColor(self, value: str):
        self.set('theme.accent_color', value)
        self.save()

    @Property(int)
    def maxPins(self):
        return self.get('max_pins', 10)

    @maxPins.setter
    def maxPins(self, value: int):
        self.set('max_pins', value)
        self.save()

    @Property(bool)
    def splashScreenEnabled(self):
        return self.get('splash_screen.enabled', True)

    @splashScreenEnabled.setter
    def splashScreenEnabled(self, value: bool):
        self.set('splash_screen.enabled', value)
        self.save()

    @Slot(result=int)
    def getImportWorkers(self) -> int:
        """
        获取导入操作的工作线程数

        Returns:
            工作线程数
        """
        cpu_count = os.cpu_count() or 4  # 默认 4 核
        max_allowed = int(cpu_count * 0.7)  # 最多70%

        max_workers = self.get('import.max_workers', 'auto')

        if max_workers == 'auto':
            # 自动模式：使用配置的比例
            ratio = self.get('import.auto_workers_ratio', 0.5)
            workers = max(1, int(cpu_count * ratio))
        else:
            # 手动设置
            workers = int(max_workers)

        # 确保不超过最大限制
        workers = min(workers, max_allowed)
        workers = max(1, workers)  # 至少1个线程

        return workers

    @Slot(int)
    def setImportWorkers(self, workers: int):
        """
        设置导入操作的工作线程数

        Args:
            workers: 工作线程数，0 表示自动
        """
        if workers == 0:
            self.set('import.max_workers', 'auto')
        else:
            cpu_count = os.cpu_count() or 4
            max_allowed = int(cpu_count * 0.7)
            workers = min(workers, max_allowed)
            workers = max(1, workers)
            self.set('import.max_workers', workers)
        self.save()

    @Slot(result=int)
    def getMaxImportWorkers(self) -> int:
        """获取最大允许的导入线程数（CPU线程数的70%）"""
        cpu_count = os.cpu_count() or 4
        return int(cpu_count * 0.7)

    @Slot(result=int)
    def getCpuCount(self) -> int:
        """获取CPU线程数"""
        return os.cpu_count() or 4
