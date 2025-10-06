"""
PDF Handler - 处理 PDF 缩略图生成
注意：PDF 显示由 QML 的 QtQuick.Pdf 模块直接处理，此类仅用于缩略图生成
"""

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

try:
    import pymupdf as fitz  # PyMuPDF 新版本导入方式
except ImportError:
    try:
        import fitz  # PyMuPDF 旧版本导入方式
    except ImportError:
        fitz = None  # PyMuPDF 未安装


class PdfHandler(QObject):
    """PDF 处理器 - 主要负责缩略图生成"""

    # 信号定义
    thumbnailGenerated = Signal(str, QImage)  # 文件路径, 缩略图

    def __init__(self, parent=None):
        super().__init__(parent)

        # 从配置获取缓存路径
        from utils.config import Config

        config = Config()
        cache_path_str = config.getCachePath()

        # 缩略图缓存目录
        self._thumbnail_dir = Path(cache_path_str) / "thumbnails"
        self._thumbnail_dir.mkdir(parents=True, exist_ok=True)
        print(f"[PdfHandler] 使用缩略图目录: {self._thumbnail_dir}")

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
