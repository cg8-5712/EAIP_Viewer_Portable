"""
Data Manager - 处理数据导入、解析和保存
"""

from PySide6.QtCore import QObject, Signal, Slot, Property
from pathlib import Path
import json
from typing import Dict, List, Any
from utils.zip_extractor import ZipExtractor


class DataManager(QObject):
    """数据管理器"""

    # 信号定义
    dataImportStarted = Signal()
    dataImportProgress = Signal(int, str)  # 进度百分比, 状态信息
    dataImportCompleted = Signal(bool, str)  # 成功/失败, 消息
    airportsLoaded = Signal(list)  # 机场数据加载完成

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_path = Path("./data")
        self._extractor = ZipExtractor()

    @Slot(str)
    def importDataFromZip(self, zip_path: str):
        """
        从压缩包导入数据

        Args:
            zip_path: 压缩包文件路径
        """
        self.dataImportStarted.emit()

        try:
            # 1. 解压文件 (20%)
            self.dataImportProgress.emit(20, "正在解压文件...")
            extract_path = self._data_path / "extracted"
            self._extractor.extract(zip_path, str(extract_path))

            # 2. 用户提供的数据处理 (40%)
            self.dataImportProgress.emit(40, "正在处理数据...")
            # TODO: 这里调用用户提供的数据处理函数
            # processed_data = user_provided_processor(extract_path)

            # 3. 解析数据结构 (60%)
            self.dataImportProgress.emit(60, "正在解析数据结构...")
            airports_data = self._parseAirportsData(extract_path)

            # 4. 保存到本地 (80%)
            self.dataImportProgress.emit(80, "正在保存数据...")
            self._saveAirportsData(airports_data)

            # 5. 完成 (100%)
            self.dataImportProgress.emit(100, "导入完成")
            self.dataImportCompleted.emit(True, f"成功导入 {len(airports_data)} 个机场数据")
            self.airportsLoaded.emit(airports_data)

        except Exception as e:
            self.dataImportCompleted.emit(False, f"导入失败: {str(e)}")

    def _parseAirportsData(self, data_path: Path) -> List[Dict[str, Any]]:
        """
        解析机场数据

        Args:
            data_path: 数据目录路径

        Returns:
            机场数据列表
        """
        airports = []

        # 读取 metadata.json（如果存在）
        metadata_file = data_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata.get('airports', [])

        # 否则扫描 airports 目录
        airports_dir = data_path / "airports"
        if airports_dir.exists():
            for airport_dir in airports_dir.iterdir():
                if airport_dir.is_dir():
                    airport_code = airport_dir.name
                    # 扫描航图分类
                    categories = [d.name for d in airport_dir.iterdir() if d.is_dir()]

                    airports.append({
                        'code': airport_code,
                        'name_zh': f'{airport_code} 机场',  # 默认值
                        'name_en': f'{airport_code} Airport',
                        'categories': categories
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
                'airports': airports_data
            }, f, ensure_ascii=False, indent=2)

    @Slot(result=list)
    def loadSavedAirports(self) -> List[Dict[str, Any]]:
        """
        加载已保存的机场数据

        Returns:
            机场数据列表
        """
        save_path = self._data_path / "airports.json"
        if not save_path.exists():
            return []

        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                airports = data.get('airports', [])
                self.airportsLoaded.emit(airports)
                return airports
        except Exception as e:
            print(f"加载机场数据失败: {e}")
            return []

    @Slot(str, str, result=list)
    def loadChartsForAirport(self, airport_code: str, category: str = "") -> List[Dict[str, Any]]:
        """
        加载指定机场的航图数据

        Args:
            airport_code: 机场代码
            category: 分类（可选）

        Returns:
            航图数据列表
        """
        charts = []
        airport_path = self._data_path / "extracted" / "airports" / airport_code

        if not airport_path.exists():
            return []

        # 如果指定了分类，只加载该分类
        if category:
            category_path = airport_path / category
            if category_path.exists():
                charts.extend(self._scanChartsInCategory(category_path, airport_code, category))
        else:
            # 加载所有分类
            for category_dir in airport_path.iterdir():
                if category_dir.is_dir():
                    charts.extend(self._scanChartsInCategory(category_dir, airport_code, category_dir.name))

        return charts

    def _scanChartsInCategory(self, category_path: Path, airport_code: str, category: str) -> List[Dict[str, Any]]:
        """
        扫描分类目录中的航图文件

        Args:
            category_path: 分类目录路径
            airport_code: 机场代码
            category: 分类名称

        Returns:
            航图数据列表
        """
        charts = []
        for chart_file in category_path.glob("*.pdf"):
            chart_id = f"{airport_code}_{category}_{chart_file.stem}"
            charts.append({
                'chart_id': chart_id,
                'name': chart_file.stem,
                'category': category,
                'file_path': str(chart_file),
                'airport_code': airport_code,
                'thumbnail': ''  # TODO: 生成缩略图
            })

        return charts
