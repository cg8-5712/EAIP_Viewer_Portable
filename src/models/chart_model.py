"""
Chart data model
"""

from typing import Any, Dict, List

from PySide6.QtCore import Property, QAbstractListModel, QObject, Qt, Signal


class Chart:
    """单个航图数据类"""

    def __init__(self, chart_id: str, name: str, category: str, file_path: str, **kwargs):
        self.chart_id = chart_id  # 航图ID
        self.name = name  # 航图名称，如 "AD 1.1"
        self.category = category  # 分类，如 "AD", "SID", "STAR"
        self.file_path = file_path  # PDF 文件路径
        self.airport_code = kwargs.get("airport_code", "")  # 所属机场代码
        self.thumbnail = kwargs.get("thumbnail", "")  # 缩略图路径
        self.metadata = kwargs.get("metadata", {})  # 其他元数据

    def __repr__(self):
        return f"Chart({self.chart_id}, {self.name}, {self.category})"


class ChartModel(QAbstractListModel):
    """航图列表模型，用于 QML ListView"""

    ChartIdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3
    FilePathRole = Qt.UserRole + 4
    AirportCodeRole = Qt.UserRole + 5
    ThumbnailRole = Qt.UserRole + 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._charts: List[Chart] = []

    def rowCount(self, parent=None):
        return len(self._charts)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._charts):
            return None

        chart = self._charts[index.row()]

        if role == self.ChartIdRole:
            return chart.chart_id
        elif role == self.NameRole:
            return chart.name
        elif role == self.CategoryRole:
            return chart.category
        elif role == self.FilePathRole:
            return chart.file_path
        elif role == self.AirportCodeRole:
            return chart.airport_code
        elif role == self.ThumbnailRole:
            return chart.thumbnail

        return None

    def roleNames(self):
        return {
            self.ChartIdRole: b"chartId",
            self.NameRole: b"name",
            self.CategoryRole: b"category",
            self.FilePathRole: b"filePath",
            self.AirportCodeRole: b"airportCode",
            self.ThumbnailRole: b"thumbnail",
        }

    def addChart(self, chart: Chart):
        """添加航图"""
        self.beginInsertRows(self.index(len(self._charts)), len(self._charts), len(self._charts))
        self._charts.append(chart)
        self.endInsertRows()

    def loadCharts(self, charts_data: List[Dict[str, Any]]):
        """从数据字典列表加载航图"""
        self.beginResetModel()
        self._charts.clear()
        for data in charts_data:
            chart = Chart(
                chart_id=data.get("chart_id", ""),
                name=data.get("name", ""),
                category=data.get("category", ""),
                file_path=data.get("file_path", ""),
                airport_code=data.get("airport_code", ""),
                thumbnail=data.get("thumbnail", ""),
                metadata=data.get("metadata", {}),
            )
            self._charts.append(chart)
        self.endResetModel()

    def filterByCategory(self, category: str):
        """按分类筛选航图"""
        filtered_data = [chart for chart in self._charts if chart.category == category]
        return filtered_data

    def clear(self):
        """清空所有航图数据"""
        self.beginResetModel()
        self._charts.clear()
        self.endResetModel()
