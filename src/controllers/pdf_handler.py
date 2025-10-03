"""
PDF Handler - 处理 PDF 文件的渲染和操作
"""

from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl
from PySide6.QtGui import QImage, QPixmap
from pathlib import Path

try:
    import pymupdf as fitz  # PyMuPDF 新版本导入方式
except ImportError:
    try:
        import fitz  # PyMuPDF 旧版本导入方式
    except ImportError:
        fitz = None  # PyMuPDF 未安装


class PdfHandler(QObject):
    """PDF 处理器"""

    # 信号定义
    pdfLoaded = Signal(bool, str)  # 成功/失败, 消息
    pageRendered = Signal(QImage)  # 页面渲染完成
    thumbnailGenerated = Signal(str, QImage)  # 文件路径, 缩略图

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_document = None
        self._current_page = 0
        self._zoom_level = 1.0
        self._rotation = 0

    @Slot(str)
    def loadPdf(self, file_path: str):
        """
        加载 PDF 文件

        Args:
            file_path: PDF 文件路径
        """
        if fitz is None:
            self.pdfLoaded.emit(False, "PyMuPDF 未安装，无法加载 PDF")
            return

        try:
            # 关闭之前的文档
            if self._current_document:
                self._current_document.close()

            # 打开新文档
            self._current_document = fitz.open(file_path)
            self._current_page = 0
            self.pdfLoaded.emit(True, f"已加载 {self._current_document.page_count} 页")

            # 渲染第一页
            self.renderCurrentPage()

        except Exception as e:
            self.pdfLoaded.emit(False, f"加载失败: {str(e)}")

    @Slot()
    def renderCurrentPage(self):
        """渲染当前页"""
        if not self._current_document or fitz is None:
            return

        try:
            page = self._current_document[self._current_page]

            # 应用缩放和旋转
            mat = fitz.Matrix(self._zoom_level, self._zoom_level)
            if self._rotation != 0:
                mat = mat.prerotate(self._rotation)

            # 渲染为图像
            pix = page.get_pixmap(matrix=mat)

            # 转换为 QImage
            img_data = pix.samples
            img = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            self.pageRendered.emit(img)

        except Exception as e:
            print(f"渲染页面失败: {e}")

    @Slot(int)
    def goToPage(self, page_number: int):
        """
        跳转到指定页

        Args:
            page_number: 页码（从0开始）
        """
        if not self._current_document:
            return

        if 0 <= page_number < self._current_document.page_count:
            self._current_page = page_number
            self.renderCurrentPage()

    @Slot()
    def nextPage(self):
        """下一页"""
        if self._current_document and self._current_page < self._current_document.page_count - 1:
            self._current_page += 1
            self.renderCurrentPage()

    @Slot()
    def previousPage(self):
        """上一页"""
        if self._current_document and self._current_page > 0:
            self._current_page -= 1
            self.renderCurrentPage()

    @Slot(float)
    def setZoom(self, zoom: float):
        """
        设置缩放级别

        Args:
            zoom: 缩放比例（1.0 = 100%）
        """
        self._zoom_level = max(0.1, min(5.0, zoom))  # 限制在 10% - 500%
        self.renderCurrentPage()

    @Slot()
    def zoomIn(self):
        """放大"""
        self.setZoom(self._zoom_level * 1.25)

    @Slot()
    def zoomOut(self):
        """缩小"""
        self.setZoom(self._zoom_level / 1.25)

    @Slot()
    def zoomFit(self):
        """适应窗口"""
        # TODO: 根据窗口大小计算合适的缩放比例
        self.setZoom(1.0)

    @Slot(int)
    def rotate(self, degrees: int):
        """
        旋转页面

        Args:
            degrees: 旋转角度（90, 180, 270）
        """
        self._rotation = (self._rotation + degrees) % 360
        self.renderCurrentPage()

    @Slot(str, result=str)
    def generateThumbnail(self, file_path: str, size: int = 200) -> str:
        """
        生成 PDF 缩略图

        Args:
            file_path: PDF 文件路径
            size: 缩略图大小（像素）

        Returns:
            缩略图保存路径
        """
        if fitz is None:
            return ""

        try:
            doc = fitz.open(file_path)
            page = doc[0]  # 第一页

            # 计算缩放比例
            zoom = size / max(page.rect.width, page.rect.height)
            mat = fitz.Matrix(zoom, zoom)

            # 渲染缩略图
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.samples
            img = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            # 保存缩略图
            thumbnail_path = Path(file_path).with_suffix('.thumb.png')
            img.save(str(thumbnail_path))

            doc.close()

            self.thumbnailGenerated.emit(file_path, img)
            return str(thumbnail_path)

        except Exception as e:
            print(f"生成缩略图失败: {e}")
            return ""

    @Property(int)
    def currentPage(self):
        """当前页码"""
        return self._current_page

    @Property(int)
    def pageCount(self):
        """总页数"""
        return self._current_document.page_count if self._current_document else 0

    @Property(float)
    def zoomLevel(self):
        """当前缩放级别"""
        return self._zoom_level
