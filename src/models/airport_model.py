"""
Airport data model
"""

from typing import Any, Dict, List

from PySide6.QtCore import Property, QAbstractListModel, QObject, Qt, Signal


class Airport:
    """单个机场数据类"""

    def __init__(self, code: str, name_zh: str, name_en: str, **kwargs):
        self.code = code  # ICAO 代码，如 ZBAA
        self.name_zh = name_zh  # 中文名称
        self.name_en = name_en  # 英文名称
        self.categories = kwargs.get("categories", [])  # 航图分类列表
        self.metadata = kwargs.get("metadata", {})  # 其他元数据

    def __repr__(self):
        return f"Airport({self.code}, {self.name_zh})"


class AirportModel(QAbstractListModel):
    """机场列表模型，用于 QML ListView"""

    CodeRole = Qt.UserRole + 1
    NameZhRole = Qt.UserRole + 2
    NameEnRole = Qt.UserRole + 3
    CategoriesRole = Qt.UserRole + 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._airports: List[Airport] = []

    def rowCount(self, parent=None):
        return len(self._airports)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._airports):
            return None

        airport = self._airports[index.row()]

        if role == self.CodeRole:
            return airport.code
        elif role == self.NameZhRole:
            return airport.name_zh
        elif role == self.NameEnRole:
            return airport.name_en
        elif role == self.CategoriesRole:
            return airport.categories

        return None

    def roleNames(self):
        return {
            self.CodeRole: b"code",
            self.NameZhRole: b"nameZh",
            self.NameEnRole: b"nameEn",
            self.CategoriesRole: b"categories",
        }

    def addAirport(self, airport: Airport):
        """添加机场"""
        self.beginInsertRows(
            self.index(len(self._airports)), len(self._airports), len(self._airports)
        )
        self._airports.append(airport)
        self.endInsertRows()

    def loadAirports(self, airports_data: List[Dict[str, Any]]):
        """从数据字典列表加载机场"""
        self.beginResetModel()
        self._airports.clear()
        for data in airports_data:
            airport = Airport(
                code=data.get("code", ""),
                name_zh=data.get("name_zh", ""),
                name_en=data.get("name_en", ""),
                categories=data.get("categories", []),
                metadata=data.get("metadata", {}),
            )
            self._airports.append(airport)
        self.endResetModel()

    def clear(self):
        """清空所有机场数据"""
        self.beginResetModel()
        self._airports.clear()
        self.endResetModel()
