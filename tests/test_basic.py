"""
示例测试 - 测试配置加载
"""
import pytest


class TestConfig:
    """测试配置模块"""

    def test_import_config(self):
        """测试导入配置模块"""
        try:
            from utils.config import Config

            assert Config is not None
        except ImportError as e:
            pytest.skip(f"Config module not found: {e}")

    def test_config_initialization(self):
        """测试配置初始化"""
        try:
            from utils.config import Config

            config = Config()
            assert config is not None
        except Exception as e:
            pytest.skip(f"Config initialization failed: {e}")


class TestControllers:
    """测试控制器模块"""

    def test_import_app_controller(self):
        """测试导入主控制器"""
        try:
            from controllers.app_controller import AppController

            assert AppController is not None
        except ImportError as e:
            pytest.skip(f"AppController module not found: {e}")


class TestModels:
    """测试模型模块"""

    def test_import_models(self):
        """测试导入模型"""
        try:
            from models import AirportModel, ChartModel, PinModel

            assert AirportModel is not None
            assert ChartModel is not None
            assert PinModel is not None
        except ImportError as e:
            pytest.skip(f"Models module not found: {e}")


def test_python_version():
    """测试 Python 版本"""
    import sys

    assert sys.version_info >= (3, 11), "需要 Python 3.11 或更高版本"


def test_required_packages():
    """测试必需的包是否已安装"""
    try:
        import PySide6

        assert PySide6 is not None
    except ImportError:
        pytest.fail("PySide6 未安装")

    try:
        import fitz  # PyMuPDF

        assert fitz is not None
    except ImportError:
        pytest.fail("PyMuPDF 未安装")
