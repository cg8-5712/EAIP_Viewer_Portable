"""
Data Manager - 处理数据导入、解析和保存
"""

from PySide6.QtCore import QObject, Signal, Slot, Property
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
from utils.zip_extractor import ZipExtractor
from utils.chart_processor import ChartProcessor
from utils.eaip_handler import EaipHandler


class DataManager(QObject):
    """数据管理器"""

    # 信号定义
    dataImportStarted = Signal()
    dataImportProgress = Signal(int, str)  # 进度百分比, 状态信息
    dataImportCompleted = Signal(bool, str)  # 成功/失败, 消息
    airportsLoaded = Signal(list)  # 机场数据加载完成
    periodUpdated = Signal(dict)  # AIRAC 周期更新完成

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_path = Path("./data")
        self._extractor = ZipExtractor()
        self._eaip_handler: Optional[EaipHandler] = None
        self._airac_period = "2505"  # 默认周期
        self._dir_name = "EAIP"  # 默认目录名

        # 初始化 EAIP 处理器
        self._initialize_eaip_handler()

    def _initialize_eaip_handler(self):
        """初始化 EAIP 处理器"""
        try:
            self._eaip_handler = EaipHandler(
                self._data_path,
                self._airac_period,
                self._dir_name
            )
        except Exception as e:
            print(f"[WARNING] EAIP 处理器初始化失败: {e}")

    @Slot(str)
    def importDataFromZip(self, zip_path: str):
        """
        从压缩包导入 EAIP 数据

        Args:
            zip_path: 压缩包文件路径
        """
        self.dataImportStarted.emit()

        try:
            # 1. 解压文件 (20%)
            self.dataImportProgress.emit(20, "正在解压文件...")
            extract_path = self._data_path / self._airac_period
            self._extractor.extract(zip_path, str(extract_path))

            # 2. 处理 EAIP 数据 (40%)
            self.dataImportProgress.emit(40, "正在处理航图数据...")

            # 自动检测 EAIP 目录
            if self._eaip_handler:
                detected_dir = self._eaip_handler.auto_detect_dir_name()
                if detected_dir:
                    self._dir_name = detected_dir
                    self._eaip_handler.dir_name = detected_dir
                    self._eaip_handler.terminal_path = extract_path / "Data" / detected_dir / "Terminal"

            # 3. 使用 ChartProcessor 处理数据 (60%)
            self.dataImportProgress.emit(60, "正在重命名和分类航图...")
            processor = ChartProcessor(extract_path, self._dir_name)
            processor.process(["rename", "organize"])

            # 4. 生成索引 (80%)
            self.dataImportProgress.emit(80, "正在生成索引...")
            processor.process(["index"])

            # 5. 加载机场数据 (100%)
            self.dataImportProgress.emit(100, "导入完成")
            airports_data = self.loadSavedAirports()

            self.dataImportCompleted.emit(True, f"成功导入 {len(airports_data)} 个机场数据")
            self.airportsLoaded.emit(airports_data)

        except Exception as e:
            self.dataImportCompleted.emit(False, f"导入失败: {str(e)}")

    @Slot(str, result=dict)
    def updateAiracPeriod(self, period: str) -> Dict[str, Any]:
        """
        更新 AIRAC 周期

        Args:
            period: AIRAC 周期（如 "2505"）

        Returns:
            更新结果
        """
        if not self._eaip_handler:
            return {"success": False, "message": "EAIP 处理器未初始化"}

        result = self._eaip_handler.update_period(period)
        if result.get("success"):
            self._airac_period = period
            self._dir_name = result.get("dir_name", "EAIP")
            self.periodUpdated.emit(result)

        return result

    def _parseAirportsData(self, data_path: Path) -> List[Dict[str, Any]]:
        """
        解析机场数据（从 EAIP Terminal 目录）

        Args:
            data_path: 数据目录路径

        Returns:
            机场数据列表
        """
        airports = []

        # 扫描 Terminal 目录
        terminal_path = data_path / "Data" / self._dir_name / "Terminal"
        if not terminal_path.exists():
            print(f"[WARNING] Terminal 目录不存在: {terminal_path}")
            return airports

        for airport_dir in terminal_path.iterdir():
            if not airport_dir.is_dir():
                continue

            icao = airport_dir.name
            index_file = airport_dir / "index.json"

            # 读取索引获取航图分类
            categories = []
            chart_count = 0

            if index_file.exists():
                try:
                    with open(index_file, "r", encoding="utf-8") as f:
                        charts = json.load(f)
                        chart_count = len(charts)
                        # 提取所有分类
                        categories = list(set(chart.get("sort", "general") for chart in charts))
                except Exception as e:
                    print(f"[ERROR] 读取索引失败 {icao}: {e}")

            airports.append({
                'code': icao,
                'name_zh': f'{icao} 机场',
                'name_en': f'{icao} Airport',
                'categories': categories,
                'chart_count': chart_count
            })

        return airports

    def _saveAirportsData(self, airports_data: List[Dict[str, Any]]):
        """
        保存机场数据到本地

        Args:
            airports_data: 机场数据列表
        """
        save_path = self._data_path / "airports.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump({
                'version': '1.0',
                'airac_period': self._airac_period,
                'dir_name': self._dir_name,
                'airports': airports_data
            }, f, ensure_ascii=False, indent=2)

    @Slot(result=list)
    def loadSavedAirports(self) -> List[Dict[str, Any]]:
        """
        加载已保存的机场数据

        Returns:
            机场数据列表
        """
        # 优先从 Terminal 目录加载最新数据
        terminal_path = self._data_path / self._airac_period / "Data" / self._dir_name / "Terminal"
        if terminal_path.exists():
            airports = self._parseAirportsData(self._data_path / self._airac_period)
            if airports:
                self.airportsLoaded.emit(airports)
                return airports

        # 否则从保存的 JSON 加载
        save_path = self._data_path / "airports.json"
        if not save_path.exists():
            return []

        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 更新周期信息
                self._airac_period = data.get('airac_period', self._airac_period)
                self._dir_name = data.get('dir_name', self._dir_name)
                airports = data.get('airports', [])
                self.airportsLoaded.emit(airports)
                return airports
        except Exception as e:
            print(f"加载机场数据失败: {e}")
            return []

    @Slot(str, str, result=list)
    def loadChartsForAirport(self, airport_code: str, category: str = "") -> List[Dict[str, Any]]:
        """
        加载指定机场的航图数据（使用 EAIP Handler）

        Args:
            airport_code: 机场代码
            category: 分类（可选）

        Returns:
            航图数据列表
        """
        if not self._eaip_handler:
            return []

        charts = self._eaip_handler.get_chart_list(
            icao=airport_code,
            search_type=category if category else None
        )

        return charts if charts else []

    @Slot(str, str, result=str)
    def getChartByCode(self, airport_code: str, chart_code: str) -> str:
        """
        通过代码获取航图路径

        Args:
            airport_code: 机场代码
            chart_code: 航图代码

        Returns:
            航图文件路径
        """
        if not self._eaip_handler:
            return ""

        try:
            # 获取航图数据
            result = self._eaip_handler.get_chart_by_code(airport_code, chart_code)
            if isinstance(result, bytes):
                # 如果是图片数据，需要保存到临时文件
                temp_path = self._data_path / "cache" / f"{airport_code}_{chart_code}.png"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, 'wb') as f:
                    f.write(result)
                return str(temp_path)
            else:
                return result  # 错误信息
        except Exception as e:
            return f"获取航图失败: {e}"
