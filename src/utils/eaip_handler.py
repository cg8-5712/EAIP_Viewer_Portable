"""
EAIP Handler - EAIP 数据查询和处理核心
"""

import io
import json
import re
from pathlib import Path
from typing import Union, List, Dict, Optional, Any
from PIL import Image
from utils.logger import Logger

logger = Logger.get_logger("EaipHandler")

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from utils.chart_processor import ChartProcessor


class EaipHandler:
    """EAIP 数据处理器"""

    def __init__(self, data_path: Path, airac_period: str = "2505", dir_name: str = "EAIP"):
        """
        初始化 EAIP 处理器

        Args:
            data_path: 数据根目录
            airac_period: AIRAC 周期（如 "2505"）
            dir_name: EAIP 文件夹名称
        """
        self.data_path = data_path
        self.airac_period = airac_period
        self.dir_name = dir_name
        self.base_path = data_path / airac_period
        # 更新为新的路径结构（导入后已移动到根目录）
        self.terminal_path = self.base_path / "Terminal"

    def auto_detect_dir_name(self) -> Optional[str]:
        """自动检测 EAIP 文件夹名称"""
        try:
            target_path = self.base_path / "Data"
            logger.debug(f"自动检测 EAIP 目录: {target_path}")

            if not target_path.exists():
                logger.error(f"数据目录不存在: {target_path}")
                return None

            # 查找 EAIP 开头的文件夹
            all_dirs = list(target_path.iterdir())
            logger.debug(f"Data 目录下共有 {len(all_dirs)} 个项目")

            eaip_dirs = [d for d in all_dirs if d.is_dir() and d.name.startswith("EAIP")]

            logger.debug(f"找到 {len(eaip_dirs)} 个 EAIP 文件夹")
            if eaip_dirs:
                logger.debug(f"EAIP 文件夹列表: {[d.name for d in eaip_dirs]}")

            if not eaip_dirs:
                logger.warning(f"未找到 EAIP 文件夹: {target_path}")
                return None

            detected_dir = eaip_dirs[0].name
            logger.info(f"检测到 EAIP 文件夹: {detected_dir}")
            return detected_dir

        except Exception as e:
            logger.error(f"自动检测失败: {e}", exc_info=True)
            return None

    def update_period(self, period: str) -> Dict[str, Any]:
        """
        更新 AIRAC 周期

        Args:
            period: AIRAC 周期（如 "2505"）

        Returns:
            更新结果字典
        """
        if not period.isdigit() or len(period) != 4:
            return {"success": False, "message": "Invalid period format"}

        try:
            self.airac_period = period
            self.base_path = self.data_path / period

            # 更新为新的路径结构
            self.terminal_path = self.base_path / "Terminal"

            # 检查路径是否存在
            if not self.base_path.exists():
                return {"success": False, "message": f"数据目录不存在: {self.base_path}"}

            if not self.terminal_path.exists():
                return {"success": False, "message": f"Terminal 目录不存在: {self.terminal_path}"}

            # 检查是否需要生成索引
            need_update = False
            for airport_dir in self.terminal_path.iterdir():
                if airport_dir.is_dir():
                    index_path = airport_dir / "index.json"
                    if not index_path.exists():
                        need_update = True
                        break

            # 如果需要，执行处理
            if need_update:
                print("[INFO] 检测到缺少索引文件，开始处理...")
                processor = ChartProcessor(self.base_path, self.dir_name)
                processor.process(["rename", "organize", "index"])

            # 统计信息
            airports = [d for d in self.terminal_path.iterdir() if d.is_dir()]
            total_charts = 0
            airport_info = []

            for airport in airports:
                index_path = airport / "index.json"
                if index_path.exists():
                    with open(index_path, "r", encoding="utf-8") as f:
                        charts = json.load(f)
                        chart_count = len(charts)
                        total_charts += chart_count
                        airport_info.append({"icao": airport.name, "charts": chart_count})

            return {
                "success": True,
                "airac_period": self.airac_period,
                "dir_name": self.dir_name,
                "total_airports": len(airports),
                "total_charts": total_charts,
                "airports": airport_info,
            }

        except Exception as e:
            print(f"[ERROR] 更新周期失败: {e}")
            return {"success": False, "message": f"更新失败: {e}"}

    def get_chart_list(
        self, icao: str, search_type: str = None, code: str = None, filename: str = None
    ) -> Optional[List[Dict]]:
        """
        获取航图列表

        Args:
            icao: 机场 ICAO 代码
            search_type: 搜索类型（跑道号或航图类型）
            code: 航图代码
            filename: 文件名关键字

        Returns:
            航图列表或 None
        """
        try:
            airport_path = self.terminal_path / icao
            if not airport_path.exists():
                return None

            index_path = airport_path / "index.json"
            if not index_path.exists():
                return None

            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 筛选
            if code:
                data = [x for x in data if x.get("code", "").upper() == code.upper()]
            elif filename:
                data = [x for x in data if filename.lower() in x["name"].lower()]
            elif search_type:
                if re.match(r"^\d{2}[LRC]?$", search_type):  # 跑道号
                    data = [x for x in data if search_type in x["name"]]
                else:  # 航图类型
                    data = [x for x in data if x["sort"] == search_type]

            return data if data else None

        except Exception as e:
            print(f"[ERROR] 获取航图列表失败: {e}")
            return None

    def get_chart(self, icao: str, doc_id: str) -> Union[str, bytes]:
        """
        通过 ID 获取航图

        Args:
            icao: 机场 ICAO 代码
            doc_id: 航图 ID

        Returns:
            图片字节或错误信息
        """
        try:
            airport_path = self.terminal_path / icao
            if not airport_path.exists():
                return f"No charts found for airport {icao}"

            index_path = airport_path / "index.json"
            if not index_path.exists():
                return "Index file not found"

            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            chart = next((x for x in data if str(x["id"]) == str(doc_id)), None)
            if not chart:
                return f"Chart with ID {doc_id} not found"

            pdf_path = airport_path / chart["path"]
            if not pdf_path.exists():
                return "Chart file does not exist"

            return self.convert_pdf_to_image(pdf_path)

        except Exception as e:
            print(f"[ERROR] 获取航图失败: {e}")
            return f"Failed to get chart: {e}"

    def get_chart_by_code(self, icao: str, code: str) -> Union[str, bytes]:
        """
        通过代码获取航图

        Args:
            icao: 机场 ICAO 代码
            code: 航图代码

        Returns:
            图片字节或错误信息
        """
        try:
            airport_path = self.terminal_path / icao
            if not airport_path.exists():
                return f"No charts found for airport {icao}"

            index_path = airport_path / "index.json"
            if not index_path.exists():
                return "Index file not found"

            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            chart = next((x for x in data if x.get("code", "").upper() == code.upper()), None)
            if not chart:
                return f"Chart with code {code} not found"

            pdf_path = airport_path / chart["path"]
            if not pdf_path.exists():
                return "Chart file does not exist"

            return self.convert_pdf_to_image(pdf_path)

        except Exception as e:
            print(f"[ERROR] 获取航图失败: {e}")
            return f"Failed to get chart: {e}"

    def convert_pdf_to_image(self, pdf_path: Path, zoom: float = 2.8) -> bytes:
        """
        将 PDF 转换为图片（或直接返回 PDF）

        Args:
            pdf_path: PDF 文件路径
            zoom: 缩放比例

        Returns:
            图片字节数据或 PDF 字节数据
        """
        if fitz is None:
            raise Exception("PyMuPDF 未安装，无法转换 PDF")

        try:
            doc = fitz.open(str(pdf_path))

            # 如果 ≥3 页，直接返回 PDF
            if len(doc) >= 3:
                doc.close()
                with open(pdf_path, "rb") as f:
                    return f.read()

            # <3 页时，将每页渲染为图片并拼接
            mat = fitz.Matrix(zoom, zoom)
            images = []

            for page in doc:
                pix = page.get_pixmap(matrix=mat, colorspace="rgb", alpha=False, annots=True)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)

            doc.close()

            # 拼接图片
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)

            combined = Image.new("RGB", (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height

            img_bytes_io = io.BytesIO()
            combined.save(img_bytes_io, format="PNG")
            return img_bytes_io.getvalue()

        except Exception as e:
            print(f"[ERROR] PDF 转换失败: {e}")
            raise Exception(f"PDF to image conversion failed: {e}")
