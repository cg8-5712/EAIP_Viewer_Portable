"""
PDF Viewer Controller - 纯PDF文档查看控制器
不依赖图片转换，直接通过Qt PDF模块显示
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot


class PdfViewerController(QObject):
    """PDF查看器控制器 - 管理PDF文档的显示和交互"""

    # 信号定义
    pdfLoaded = Signal(str)  # PDF加载成功，参数：文件路径
    pdfError = Signal(str)  # PDF加载错误，参数：错误信息
    pageChanged = Signal(int)  # 页面改变，参数：当前页码

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_pdf_path = ""
        self._current_page = 0
        self._page_count = 0
        self._zoom_factor = 1.0

        print("[PdfViewerController] 初始化完成")

    @Slot(str, result=str)
    def normalizePdfPath(self, file_path: str) -> str:
        """
        规范化PDF文件路径为Qt可用的URL格式

        Args:
            file_path: 文件路径

        Returns:
            规范化的URL字符串
        """
        if not file_path:
            return ""

        try:
            # 转换为Path对象
            path = Path(file_path)

            # 检查文件是否存在
            if not path.exists():
                print(f"[PdfViewerController] 文件不存在: {file_path}")
                return ""

            # 转换为绝对路径
            abs_path = path.resolve()

            # 创建QUrl对象
            url = QUrl.fromLocalFile(str(abs_path))

            # 返回URL字符串
            url_string = url.toString()
            print(f"[PdfViewerController] 路径规范化:")
            print(f"  输入: {file_path}")
            print(f"  输出: {url_string}")

            return url_string

        except Exception as e:
            print(f"[PdfViewerController] 路径规范化失败: {e}")
            return ""

    @Slot(str)
    def loadPdf(self, file_path: str):
        """
        加载PDF文档

        Args:
            file_path: PDF文件路径
        """
        print(f"[PdfViewerController] 加载PDF: {file_path}")

        try:
            # 验证文件
            path = Path(file_path)
            if not path.exists():
                error_msg = f"文件不存在: {file_path}"
                print(f"[PdfViewerController] {error_msg}")
                self.pdfError.emit(error_msg)
                return

            if not path.is_file():
                error_msg = f"不是有效的文件: {file_path}"
                print(f"[PdfViewerController] {error_msg}")
                self.pdfError.emit(error_msg)
                return

            # 检查文件扩展名
            if path.suffix.lower() not in [".pdf"]:
                error_msg = f"不支持的文件格式: {path.suffix}"
                print(f"[PdfViewerController] {error_msg}")
                self.pdfError.emit(error_msg)
                return

            # 更新状态
            self._current_pdf_path = str(path.resolve())
            self._current_page = 0

            # 发射加载信号
            normalized_path = self.normalizePdfPath(self._current_pdf_path)
            self.pdfLoaded.emit(normalized_path)

            print(f"[PdfViewerController] PDF加载成功: {self._current_pdf_path}")

        except Exception as e:
            error_msg = f"加载PDF失败: {str(e)}"
            print(f"[PdfViewerController] {error_msg}")
            self.pdfError.emit(error_msg)

    @Slot()
    def clearPdf(self):
        """清空当前PDF"""
        print("[PdfViewerController] 清空PDF")
        self._current_pdf_path = ""
        self._current_page = 0
        self._page_count = 0
        self.pdfLoaded.emit("")

    @Slot(int)
    def setCurrentPage(self, page: int):
        """
        设置当前页码

        Args:
            page: 页码（从0开始）
        """
        if page != self._current_page:
            self._current_page = page
            self.pageChanged.emit(page)
            print(f"[PdfViewerController] 页面切换到: {page + 1}")

    @Slot(int)
    def setPageCount(self, count: int):
        """
        设置总页数

        Args:
            count: 总页数
        """
        self._page_count = count
        print(f"[PdfViewerController] 文档总页数: {count}")

    @Slot(float)
    def setZoomFactor(self, factor: float):
        """
        设置缩放因子

        Args:
            factor: 缩放因子
        """
        self._zoom_factor = factor
        print(f"[PdfViewerController] 缩放因子: {factor * 100:.0f}%")

    @Slot(str, result=bool)
    def isValidPdfPath(self, file_path: str) -> bool:
        """
        检查是否为有效的PDF文件路径

        Args:
            file_path: 文件路径

        Returns:
            是否有效
        """
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and path.suffix.lower() == ".pdf"
        except Exception:
            return False

    @Slot(result=str)
    def getCurrentPdfPath(self) -> str:
        """
        获取当前PDF路径

        Returns:
            当前PDF路径
        """
        return self._current_pdf_path

    @Slot(result=int)
    def getCurrentPage(self) -> int:
        """
        获取当前页码

        Returns:
            当前页码（从0开始）
        """
        return self._current_page

    @Slot(result=int)
    def getPageCount(self) -> int:
        """
        获取总页数

        Returns:
            总页数
        """
        return self._page_count

    # Properties
    @Property(str, notify=pdfLoaded)
    def currentPdfPath(self):
        """当前PDF路径属性"""
        return self._current_pdf_path

    @Property(int, notify=pageChanged)
    def currentPage(self):
        """当前页码属性"""
        return self._current_page

    @Property(int)
    def pageCount(self):
        """总页数属性"""
        return self._page_count
