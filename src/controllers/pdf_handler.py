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
    pageImageReady = Signal(str)  # 页面图片文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_document = None
        self._current_page = 0
        self._zoom_level = 1.0
        self._rotation = 0
        self._render_counter = 0  # 渲染计数器，用于生成唯一文件名

        # 从配置获取缓存路径
        from utils.config import Config
        config = Config()
        cache_path_str = config.getCachePath()
        self._temp_dir = Path(cache_path_str) / "pdf_render"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

        # 缩略图缓存目录
        self._thumbnail_dir = Path(cache_path_str) / "thumbnails"
        self._thumbnail_dir.mkdir(parents=True, exist_ok=True)
        print(f"[PdfHandler] 使用缓存目录: {self._temp_dir}")
        print(f"[PdfHandler] 使用缩略图目录: {self._thumbnail_dir}")

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

    @Slot(str, float, result=str)
    def renderPdfToImage(self, file_path: str, zoom: float = 1.0) -> str:
        """
        渲染 PDF 第一页为图片并返回临时文件路径

        Args:
            file_path: PDF 文件路径
            zoom: 缩放比例

        Returns:
            临时图片文件路径
        """
        print("=" * 70)
        print(f"[PdfHandler] renderPdfToImage 被调用")
        print(f"[PdfHandler] 文件路径: {file_path}")
        print(f"[PdfHandler] 路径类型: {type(file_path)}")
        print(f"[PdfHandler] 路径长度: {len(file_path) if file_path else 0}")
        print(f"[PdfHandler] 缩放比例: {zoom}")

        if fitz is None:
            print("[ERROR] PyMuPDF 未安装，无法渲染 PDF")
            return ""

        try:
            from pathlib import Path
            pdf_path = Path(file_path)
            print(f"[PdfHandler] 转换为 Path: {pdf_path}")
            print(f"[PdfHandler] 文件存在: {pdf_path.exists()}")

            if not pdf_path.exists():
                print(f"[ERROR] PDF 文件不存在: {file_path}")
                return ""

            print(f"[PdfHandler] 开始打开 PDF 文档...")
            # 打开 PDF 文档
            doc = fitz.open(file_path)
            print(f"[PdfHandler] PDF 文档已打开")
            print(f"[PdfHandler] 页数: {doc.page_count}")

            page = doc[0]  # 第一页
            print(f"[PdfHandler] 获取第一页成功")
            print(f"[PdfHandler] 页面尺寸: {page.rect.width} x {page.rect.height}")

            # 应用缩放
            mat = fitz.Matrix(zoom, zoom)
            print(f"[PdfHandler] 缩放矩阵已创建: {zoom}")

            # 渲染为图像
            print(f"[PdfHandler] 开始渲染图像...")
            pix = page.get_pixmap(matrix=mat)
            print(f"[PdfHandler] 图像渲染完成")
            print(f"[PdfHandler] 图像尺寸: {pix.width} x {pix.height}")

            # 转换为 QImage
            img_data = pix.samples
            from PySide6.QtGui import QImage
            img = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            print(f"[PdfHandler] QImage 创建成功")
            print(f"[PdfHandler] QImage 尺寸: {img.width()} x {img.height()}")

            # 保存到临时文件（使用计数器生成唯一文件名避免缓存）
            self._render_counter += 1
            temp_file = self._temp_dir / f"page_{self._render_counter}.png"
            print(f"[PdfHandler] 临时文件路径: {temp_file}")
            print(f"[PdfHandler] 临时目录存在: {self._temp_dir.exists()}")

            success = img.save(str(temp_file))
            print(f"[PdfHandler] 图片保存结果: {success}")
            print(f"[PdfHandler] 保存后文件存在: {temp_file.exists()}")

            if temp_file.exists():
                print(f"[PdfHandler] 文件大小: {temp_file.stat().st_size} 字节")

            doc.close()
            print(f"[PdfHandler] PDF 文档已关闭")

            # 返回文件路径（使用 file:/// 格式）
            result_path = str(temp_file).replace("\\", "/")
            print(f"[PdfHandler] 返回路径: {result_path}")
            print("=" * 70)
            return result_path

        except Exception as e:
            print(f"[ERROR] 渲染 PDF 失败: {e}")
            import traceback
            traceback.print_exc()
            print("=" * 70)
            return ""

    @Slot(str, result=str)
    def getPdfSize(self, file_path: str) -> str:
        """
        获取PDF原始尺寸（第一页）

        Args:
            file_path: PDF文件路径

        Returns:
            尺寸字符串 "width,height"，失败返回空字符串
        """
        if fitz is None:
            print("[ERROR] PyMuPDF 未安装")
            return ""

        try:
            from pathlib import Path
            pdf_path = Path(file_path)

            if not pdf_path.exists():
                print(f"[ERROR] PDF 文件不存在: {file_path}")
                return ""

            doc = fitz.open(file_path)
            page = doc[0]
            width = page.rect.width
            height = page.rect.height
            doc.close()

            result = f"{width},{height}"
            print(f"[PdfHandler] getPdfSize: {file_path} -> {result}")
            return result

        except Exception as e:
            print(f"[ERROR] 获取PDF尺寸失败: {e}")
            return ""

    @Slot(str, str, result=str)
    def generateChartThumbnail(self, file_path: str, chart_id: str) -> str:
        """
        生成航图缩略图（按需生成，用于列表显示）

        Args:
            file_path: PDF文件路径
            chart_id: 航图ID，用于命名缩略图文件

        Returns:
            缩略图文件路径，失败返回空字符串
        """
        if fitz is None:
            print("[ERROR] PyMuPDF 未安装，无法生成缩略图")
            return ""

        try:
            from pathlib import Path

            # 检查缓存是否已存在
            thumbnail_file = self._thumbnail_dir / f"{chart_id}.png"
            if thumbnail_file.exists():
                print(f"[PdfHandler] 缩略图已存在: {thumbnail_file}")
                return str(thumbnail_file).replace("\\", "/")

            # 检查PDF文件是否存在
            pdf_path = Path(file_path)
            if not pdf_path.exists():
                print(f"[ERROR] PDF 文件不存在: {file_path}")
                return ""

            print(f"[PdfHandler] 开始生成缩略图: {chart_id}")

            # 打开PDF文档
            doc = fitz.open(file_path)
            page = doc[0]  # 第一页

            # 计算缩放比例（生成约60像素宽的缩略图）
            target_width = 60
            zoom = target_width / page.rect.width
            mat = fitz.Matrix(zoom, zoom)

            print(f"[PdfHandler] 缩略图缩放比例: {zoom}")

            # 渲染缩略图
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.samples

            # 转换为 QImage
            img = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            # 保存缩略图
            success = img.save(str(thumbnail_file))
            doc.close()

            if success:
                print(f"[PdfHandler] 缩略图生成成功: {thumbnail_file}")
                return str(thumbnail_file).replace("\\", "/")
            else:
                print(f"[ERROR] 缩略图保存失败")
                return ""

        except Exception as e:
            print(f"[ERROR] 生成缩略图失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
