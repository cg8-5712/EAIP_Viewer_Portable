"""
App Controller - 主控制器，协调各个组件
"""

from PySide6.QtCore import Property, QObject, Signal, Slot

from controllers.data_manager import DataManager
from controllers.pdf_handler import PdfHandler
from models import AirportModel, ChartModel, PinModel
from utils.config import Config
from utils.logger import Logger

logger = Logger.get_logger("AppController")


class AppController(QObject):
    """应用主控制器"""

    # 信号定义
    initialized = Signal()
    currentViewChanged = Signal(str)  # 当前视图名称

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("初始化 AppController")

        # 配置管理
        self._config = Config()
        logger.debug(f"配置加载完成")

        # 数据管理
        self._data_manager = DataManager(self)

        # PDF 处理
        self._pdf_handler = PdfHandler(self)

        # 数据模型
        self._airport_model = AirportModel(self)
        self._chart_model = ChartModel(self)
        self._pin_model = PinModel(max_pins=self._config.get("max_pins", 10), parent=self)

        # 当前状态
        self._current_view = "airportList"  # 当前视图
        self._current_airport = ""  # 当前选中的机场
        self._current_category = ""  # 当前选中的分类

        logger.info("AppController 初始化完成")

        # 连接信号
        self._connectSignals()

    def _connectSignals(self):
        """连接信号和槽"""
        # 数据导入完成后，加载到模型
        self._data_manager.airportsLoaded.connect(self._onAirportsLoaded)

    @Slot(list)
    def _onAirportsLoaded(self, airports_data):
        """机场数据加载完成"""
        self._airport_model.loadAirports(airports_data)

    @Slot()
    def initialize(self):
        """初始化应用"""
        logger.info("开始初始化应用")
        # 加载保存的机场数据
        self._data_manager.loadSavedAirports()

        # 加载保存的固定航图
        pinned_charts = self._config.get("pinned_charts", [])
        self._pin_model.loadPinnedCharts(pinned_charts)

        logger.info("应用初始化完成")
        self.initialized.emit()

    @Slot(str)
    def importData(self, zip_path: str):
        """
        导入数据

        Args:
            zip_path: 压缩包路径
        """
        self._data_manager.importDataFromZip(zip_path)

    @Slot(str)
    def selectAirport(self, airport_code: str):
        """
        选择机场

        Args:
            airport_code: 机场代码
        """
        self._current_airport = airport_code
        self._current_category = ""
        self._chart_model.clear()

        # 切换到航图查看页面
        self._current_view = "chartViewer"
        self.currentViewChanged.emit(self._current_view)

    @Slot(str)
    def selectCategory(self, category: str):
        """
        选择航图分类

        Args:
            category: 分类名称
        """
        self._current_category = category

        # 加载该分类的航图
        charts_data = self._data_manager.loadChartsForAirport(self._current_airport, category)
        self._chart_model.loadCharts(charts_data)

    @Slot(str)
    def openChart(self, file_path: str):
        """
        打开航图

        Args:
            file_path: 航图文件路径
        """
        self._pdf_handler.loadPdf(file_path)

    @Slot(dict)
    def pinChart(self, chart_data: dict):
        """
        固定航图

        Args:
            chart_data: 航图数据字典
        """
        success = self._pin_model.pinChart(chart_data)
        if success:
            # 保存到配置
            self._savePinnedCharts()

    @Slot(str)
    def unpinChart(self, chart_id: str):
        """
        取消固定航图

        Args:
            chart_id: 航图ID
        """
        success = self._pin_model.unpinChart(chart_id)
        if success:
            # 保存到配置
            self._savePinnedCharts()

    @Slot(str, result=bool)
    def isPinned(self, chart_id: str) -> bool:
        """
        检查航图是否已固定

        Args:
            chart_id: 航图ID

        Returns:
            是否已固定
        """
        return self._pin_model.isPinned(chart_id)

    @Slot(str)
    def openPinnedChart(self, file_path: str):
        """
        打开固定的航图

        Args:
            file_path: 航图文件路径
        """
        print(f"[AppController] 打开固定航图: {file_path}")
        # 使用 PDF Handler 加载 PDF
        self._pdf_handler.loadPdf(file_path)

    @Slot(str, str, result=str)
    def generateThumbnail(self, file_path: str, chart_id: str) -> str:
        """
        生成航图缩略图

        Args:
            file_path: 航图文件路径
            chart_id: 航图ID

        Returns:
            缩略图文件路径
        """
        return self._pdf_handler.generateChartThumbnail(file_path, chart_id)

    def _savePinnedCharts(self):
        """保存固定航图到配置"""
        pinned_charts = self._pin_model.getPinnedCharts()
        self._config.set("pinned_charts", pinned_charts)
        self._config.save()

    @Slot()
    def goBack(self):
        """返回上一页"""
        if self._current_view == "chartViewer":
            self._current_view = "airportList"
            self._current_airport = ""
            self._current_category = ""
            self._chart_model.clear()
            self.currentViewChanged.emit(self._current_view)

    # Properties
    @Property(QObject, constant=True)
    def dataManager(self):
        return self._data_manager

    @Property(QObject, constant=True)
    def pdfHandler(self):
        return self._pdf_handler

    @Property(QObject, constant=True)
    def airportModel(self):
        return self._airport_model

    @Property(QObject, constant=True)
    def chartModel(self):
        return self._chart_model

    @Property(QObject, constant=True)
    def pinModel(self):
        return self._pin_model

    @Property(QObject, constant=True)
    def config(self):
        return self._config

    @Property(str, notify=currentViewChanged)
    def currentView(self):
        return self._current_view

    @Property(str)
    def currentAirport(self):
        return self._current_airport

    @Property(str)
    def currentCategory(self):
        return self._current_category
