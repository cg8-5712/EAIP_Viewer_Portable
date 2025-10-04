"""
Pin model for managing pinned charts
"""

from PySide6.QtCore import QObject, Signal, Property, Slot, QAbstractListModel, Qt
from typing import List, Dict, Any


class PinnedChart:
    """固定航图数据类"""

    def __init__(self, chart_id: str, name: str, file_path: str, **kwargs):
        self.chart_id = chart_id  # 航图ID
        self.name = name  # 航图名称
        self.file_path = file_path  # PDF 文件路径
        self.airport_code = kwargs.get('airport_code', '')  # 所属机场代码
        self.category = kwargs.get('category', '')  # 分类
        self.thumbnail = kwargs.get('thumbnail', '')  # 缩略图路径
        self.pinned_at = kwargs.get('pinned_at', '')  # 固定时间

    def __repr__(self):
        return f"PinnedChart({self.chart_id}, {self.name})"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于保存"""
        return {
            'chart_id': self.chart_id,
            'name': self.name,
            'file_path': self.file_path,
            'airport_code': self.airport_code,
            'category': self.category,
            'thumbnail': self.thumbnail,
            'pinned_at': self.pinned_at
        }


class PinModel(QAbstractListModel):
    """固定航图列表模型"""

    ChartIdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    FilePathRole = Qt.UserRole + 3
    AirportCodeRole = Qt.UserRole + 4
    CategoryRole = Qt.UserRole + 5
    ThumbnailRole = Qt.UserRole + 6

    maxPinsChanged = Signal(int)

    def __init__(self, max_pins: int = 10, parent=None):
        super().__init__(parent)
        self._pinned_charts: List[PinnedChart] = []
        self._max_pins = max_pins

    def rowCount(self, parent=None):
        return len(self._pinned_charts)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._pinned_charts):
            return None

        chart = self._pinned_charts[index.row()]

        if role == self.ChartIdRole:
            return chart.chart_id
        elif role == self.NameRole:
            return chart.name
        elif role == self.FilePathRole:
            return chart.file_path
        elif role == self.AirportCodeRole:
            return chart.airport_code
        elif role == self.CategoryRole:
            return chart.category
        elif role == self.ThumbnailRole:
            return chart.thumbnail

        return None

    def roleNames(self):
        return {
            self.ChartIdRole: b'chartId',
            self.NameRole: b'name',
            self.FilePathRole: b'filePath',
            self.AirportCodeRole: b'airportCode',
            self.CategoryRole: b'category',
            self.ThumbnailRole: b'thumbnail'
        }

    @Property(int, notify=maxPinsChanged)
    def maxPins(self):
        return self._max_pins

    @maxPins.setter
    def maxPins(self, value: int):
        if self._max_pins != value:
            self._max_pins = value
            self.maxPinsChanged.emit(value)
            # 如果超出最大数量，移除多余的
            if len(self._pinned_charts) > value:
                self.beginRemoveRows(self.index(value), value, len(self._pinned_charts) - 1)
                self._pinned_charts = self._pinned_charts[:value]
                self.endRemoveRows()

    @Slot(dict, result=bool)
    def pinChart(self, chart_data: Dict[str, Any]) -> bool:
        """固定航图"""
        # 检查是否已经固定
        for chart in self._pinned_charts:
            if chart.chart_id == chart_data.get('chart_id'):
                return False

        # 检查是否达到最大数量
        if len(self._pinned_charts) >= self._max_pins:
            return False

        # 添加新的固定航图
        pinned_chart = PinnedChart(
            chart_id=chart_data.get('chart_id', ''),
            name=chart_data.get('name', ''),
            file_path=chart_data.get('file_path', ''),
            airport_code=chart_data.get('airport_code', ''),
            category=chart_data.get('category', ''),
            thumbnail=chart_data.get('thumbnail', ''),
            pinned_at=chart_data.get('pinned_at', '')
        )

        self.beginInsertRows(self.index(len(self._pinned_charts)), len(self._pinned_charts), len(self._pinned_charts))
        self._pinned_charts.append(pinned_chart)
        self.endInsertRows()

        return True

    @Slot(str, result=bool)
    def unpinChart(self, chart_id: str) -> bool:
        """取消固定航图"""
        for i, chart in enumerate(self._pinned_charts):
            if chart.chart_id == chart_id:
                self.beginRemoveRows(self.index(i), i, i)
                self._pinned_charts.pop(i)
                self.endRemoveRows()
                return True
        return False

    @Slot(str, result=bool)
    def isPinned(self, chart_id: str) -> bool:
        """检查航图是否已固定"""
        return any(chart.chart_id == chart_id for chart in self._pinned_charts)

    def getPinnedCharts(self) -> List[Dict[str, Any]]:
        """获取所有固定航图的字典列表"""
        return [chart.to_dict() for chart in self._pinned_charts]

    def loadPinnedCharts(self, charts_data: List[Dict[str, Any]]):
        """从数据字典列表加载固定航图"""
        self.beginResetModel()
        self._pinned_charts.clear()
        for data in charts_data[:self._max_pins]:  # 限制最大数量
            chart = PinnedChart(
                chart_id=data.get('chart_id', ''),
                name=data.get('name', ''),
                file_path=data.get('file_path', ''),
                airport_code=data.get('airport_code', ''),
                category=data.get('category', ''),
                thumbnail=data.get('thumbnail', ''),
                pinned_at=data.get('pinned_at', '')
            )
            self._pinned_charts.append(chart)
        self.endResetModel()

    def clear(self):
        """清空所有固定航图"""
        self.beginResetModel()
        self._pinned_charts.clear()
        self.endResetModel()
