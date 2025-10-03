"""
EAIP Chart Processor
处理 EAIP 航图数据:解压、重命名、分类、索引
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import Logger

logger = Logger.get_logger("ChartProcessor")

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


@dataclass
class ChartFile:
    """航图文件数据模型"""
    name: str
    path: str
    chart_type: str
    icao: str

    @property
    def full_path(self) -> Path:
        """获取完整路径"""
        return Path(self.path) / self.name


class ChartProcessor:
    """航图处理服务"""

    CHART_TYPES = [
        "ADC", "APDC", "GMC", "DGS", "AOC", "PATC", "FDA",
        "ATCMAS", "SID", "STAR", "WAYPOINT LIST",
        "DATABASE CODING TABLE", "IAC", "ATCSMAC"
    ]

    SPECIAL_CHART_TYPES = ["WAYPOINT LIST", "GMC", "APDC", "DATABASE CODING TABLE"]

    def __init__(self, data_path: Path, dir_name: str = "EAIP", max_workers: int = 4) -> None:
        """
        初始化航图处理器

        Args:
            data_path: 数据根目录
            dir_name: EAIP 目录名称
            max_workers: 最大工作线程数
        """
        self.data_path = data_path
        self.dir_name = dir_name
        self.max_workers = max(1, max_workers)  # 至少1个线程
        self.terminal_path = data_path / "Data" / dir_name / "Terminal"
        self.enroute_path = data_path / "Data" / dir_name / "ENROUTE"
        self.ad_json_path = data_path / "Data" / "JsonPath" / "AD.JSON"
        self.enr_json_path = data_path / "Data" / "JsonPath" / "ENR.JSON"

        logger.debug(f"初始化 ChartProcessor: data_path={data_path}, dir_name={dir_name}, max_workers={self.max_workers}")
        logger.debug(f"Terminal 路径: {self.terminal_path}")
        logger.debug(f"ENROUTE 路径: {self.enroute_path}")
        logger.debug(f"AD.JSON 路径: {self.ad_json_path}")
        logger.debug(f"ENR.JSON 路径: {self.enr_json_path}")

    def validate_paths(self) -> bool:
        """验证路径有效性"""
        logger.debug(f"验证路径: data_path={self.data_path}")

        if not self.data_path.exists():
            logger.error(f"数据目录不存在: {self.data_path}")
            return False

        logger.debug(f"数据目录存在: {self.data_path}")

        if not self.terminal_path.exists():
            logger.warning(f"Terminal目录不存在: {self.terminal_path}")
            # 尝试创建
            self.terminal_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"已创建 Terminal 目录: {self.terminal_path}")

        if not self.enroute_path.exists():
            logger.warning(f"ENROUTE目录不存在: {self.enroute_path}")
            # 尝试创建
            self.enroute_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"已创建 ENROUTE 目录: {self.enroute_path}")

        return True

    def merge_pdfs(self, folder_path: Path, chart_type: str) -> Optional[Path]:
        """
        合并指定类型的PDF文件

        Args:
            folder_path: PDF 文件所在文件夹
            chart_type: 航图类型

        Returns:
            合并后的 PDF 路径，失败返回 None
        """
        if fitz is None:
            print("[ERROR] PyMuPDF 未安装，无法合并 PDF")
            return None

        if not folder_path.exists() or not folder_path.is_dir():
            print(f"[WARNING] 文件夹不存在: {folder_path}")
            return None

        pdf_files = sorted(folder_path.glob("*.pdf"))
        if not pdf_files:
            print(f"[WARNING] 没有找到PDF文件: {folder_path}")
            return None

        try:
            merged_doc = fitz.open()
            for pdf_path in pdf_files:
                with fitz.open(str(pdf_path)) as doc:
                    merged_doc.insert_pdf(doc)

            merged_path = folder_path / f"{chart_type}-MERGED.pdf"
            merged_doc.save(str(merged_path))
            merged_doc.close()

            print(f"[SUCCESS] PDF 合并成功: {merged_path}")
            return merged_path

        except Exception as e:
            print(f"[ERROR] 合并 PDF 失败: {e}")
            return None

    def merge_special_charts(self, airport_path: Path) -> None:
        """合并特殊类型图表"""
        for chart_type in self.SPECIAL_CHART_TYPES:
            type_folder = airport_path / chart_type
            if type_folder.exists() and type_folder.is_dir():
                print(f"[INFO] 处理特殊图表: {chart_type} at {type_folder}")
                self.merge_pdfs(type_folder, chart_type)

    @staticmethod
    def get_icao_from_path(path: Path) -> Optional[str]:
        """从路径提取ICAO代码或航路图标识"""
        for i, part in enumerate(path.parts):
            if "GeneralDoc" in part:
                return "GeneralDoc"
            if "Terminal" in part and i + 1 < len(path.parts):
                return path.parts[i + 1]
            if "ENROUTE" in part:
                return "ENROUTE"
        return None

    def rename_chart_files(self) -> None:
        """重命名航图文件（基于 AD.JSON 和 ENR.JSON）"""
        # 处理机场航图
        self._rename_airport_charts()
        # 处理航路图
        self._rename_enroute_charts()

    def _rename_airport_charts(self) -> None:
        """重命名机场航图文件（基于 AD.JSON）"""
        logger.debug(f"开始重命名机场航图文件，JSON路径: {self.ad_json_path}")

        if not self.ad_json_path.exists():
            logger.warning(f"AD.JSON 文件不存在: {self.ad_json_path}")
            return

        try:
            with open(self.ad_json_path, "r", encoding="utf-8") as file:
                chart_data = json.load(file)
            logger.info(f"读取机场航图数据: {len(chart_data)} 条记录")

            renamed_count = 0
            for chart in chart_data:
                if not chart.get("pdfPath"):
                    continue

                old_path = self.data_path / chart["pdfPath"].lstrip("/")
                icao = self.get_icao_from_path(old_path)

                if not icao or icao == "ENROUTE":
                    logger.debug(f"跳过非机场航图: {old_path}")
                    continue

                new_name = (chart["name"].replace(":", "-")
                           .replace("/", "-")
                           .replace("\\", "-") + ".pdf")

                directory = self.terminal_path / icao
                new_path = directory / new_name

                if old_path.exists():
                    try:
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        old_path.rename(new_path)
                        renamed_count += 1
                        logger.debug(f"重命名机场航图: {old_path.name} -> {icao}/{new_name}")
                    except OSError as e:
                        logger.error(f"重命名失败: {old_path}, {e}")
                else:
                    logger.debug(f"文件不存在: {old_path}")

            logger.info(f"机场航图重命名完成，共处理 {renamed_count} 个文件")

        except Exception as e:
            logger.error(f"机场航图重命名过程失败: {e}", exc_info=True)

    def _rename_enroute_charts(self) -> None:
        """重命名航路图文件（基于 ENR.JSON）"""
        logger.debug(f"开始重命名航路图文件，JSON路径: {self.enr_json_path}")

        if not self.enr_json_path.exists():
            logger.warning(f"ENR.JSON 文件不存在: {self.enr_json_path}")
            return

        try:
            with open(self.enr_json_path, "r", encoding="utf-8") as file:
                chart_data = json.load(file)
            logger.info(f"读取航路图数据: {len(chart_data)} 条记录")

            renamed_count = 0
            for chart in chart_data:
                if not chart.get("pdfPath"):
                    continue

                old_path = self.data_path / chart["pdfPath"].lstrip("/")

                new_name = (chart["name"].replace(":", "-")
                           .replace("/", "-")
                           .replace("\\", "-") + ".pdf")

                new_path = self.enroute_path / new_name

                if old_path.exists():
                    try:
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        old_path.rename(new_path)
                        renamed_count += 1
                        logger.debug(f"重命名航路图: {old_path.name} -> ENROUTE/{new_name}")
                    except OSError as e:
                        logger.error(f"重命名失败: {old_path}, {e}")
                else:
                    logger.debug(f"文件不存在: {old_path}")

            logger.info(f"航路图重命名完成，共处理 {renamed_count} 个文件")

        except Exception as e:
            logger.error(f"航路图重命名过程失败: {e}", exc_info=True)

    def organize_airport_files(self) -> None:
        """整理机场文件到分类文件夹"""
        logger.debug("开始整理机场文件")

        try:
            if not self.terminal_path.exists():
                logger.error(f"Terminal 目录不存在: {self.terminal_path}")
                return

            airports = [d for d in self.terminal_path.iterdir() if d.is_dir()]
            logger.info(f"开始整理机场文件，机场数量: {len(airports)}")

            moved_count = 0
            for airport in airports:
                airport_path = self.terminal_path / airport.name
                pdf_files = list(airport_path.glob("*.pdf"))
                logger.debug(f"处理机场 {airport.name}，PDF 文件数: {len(pdf_files)}")

                for pdf_file in pdf_files:
                    for chart_type in self.CHART_TYPES:
                        if chart_type in pdf_file.name:
                            type_folder = airport_path / chart_type
                            type_folder.mkdir(parents=True, exist_ok=True)
                            new_path = type_folder / pdf_file.name
                            pdf_file.rename(new_path)
                            moved_count += 1
                            logger.debug(f"移动文件: {pdf_file.name} -> {chart_type}/")
                            break

            logger.info(f"整理完成，共移动 {moved_count} 个文件")

        except Exception as e:
            logger.error(f"整理文件失败: {e}", exc_info=True)

    def _generate_airport_index(self, airport_path: Path) -> tuple:
        """
        为单个机场生成索引（用于多线程）

        Args:
            airport_path: 机场目录路径

        Returns:
            (机场名称, 图表数量)
        """
        airport_name = airport_path.name
        logger.debug(f"处理机场 {airport_name}")

        try:
            self.merge_special_charts(airport_path)

            index_entries: List[Dict[str, str]] = []
            chart_id = 1

            # 处理根目录下的PDF文件
            root_pdfs = list(airport_path.glob("*.pdf"))
            logger.debug(f"  根目录 PDF: {len(root_pdfs)} 个")

            for pdf_file in root_pdfs:
                path = pdf_file.name.replace("\\", "/")
                index_entries.append({
                    "id": str(chart_id),
                    "code": "general",
                    "name": pdf_file.name,
                    "path": path,
                    "sort": "general"
                })
                chart_id += 1

            # 处理子文件夹中的PDF文件
            folders = [f for f in airport_path.iterdir() if f.is_dir()]
            logger.debug(f"  子文件夹: {len(folders)} 个")

            for folder in folders:
                folder_pdfs = list(folder.glob("*.pdf"))
                logger.debug(f"    {folder.name}: {len(folder_pdfs)} 个 PDF")

                for pdf_file in folder_pdfs:
                    path = f"{folder.name}/{pdf_file.name}".replace("\\", "/")
                    # 提取 code（去掉机场代码前缀）
                    code = pdf_file.name.split(folder.name)[0]
                    if f"{airport_name}-" in code:
                        code = code.split(f"{airport_name}-")[-1]

                    index_entries.append({
                        "id": str(chart_id),
                        "code": code.strip(),
                        "name": pdf_file.name,
                        "path": path,
                        "sort": folder.name
                    })
                    chart_id += 1

            # 保存索引文件
            index_file = airport_path / "index.json"
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index_entries, f, ensure_ascii=False, indent=4)

            return (airport_name, len(index_entries))

        except Exception as e:
            logger.error(f"生成机场索引失败 {airport_name}: {e}", exc_info=True)
            return (airport_name, 0)

    def generate_index(self) -> None:
        """生成航图索引 (index.json)"""
        logger.debug("开始生成航图索引")

        try:
            # 生成机场索引（使用多线程）
            if self.terminal_path.exists():
                airports = [d for d in self.terminal_path.iterdir() if d.is_dir()]
                logger.info(f"找到 {len(airports)} 个机场目录")

                # 使用线程池并行处理机场索引
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    logger.info(f"使用 {self.max_workers} 个线程并行生成机场索引")
                    futures = [executor.submit(self._generate_airport_index, airport) for airport in airports]

                    total_charts = 0
                    for future in as_completed(futures):
                        airport_name, chart_count = future.result()
                        total_charts += chart_count
                        logger.info(f"机场索引生成完成: {airport_name}, 图表数量: {chart_count}")

                logger.info(f"所有机场索引生成完成，总图表数: {total_charts}")
            else:
                logger.warning(f"Terminal 目录不存在: {self.terminal_path}")

            # 生成航路图索引
            if self.enroute_path.exists():
                logger.debug("生成航路图索引")
                index_entries: List[Dict[str, str]] = []
                chart_id = 1

                # 处理 ENROUTE 目录下的所有 PDF 文件
                enroute_pdfs = list(self.enroute_path.glob("*.pdf"))
                logger.debug(f"  航路图 PDF: {len(enroute_pdfs)} 个")

                for pdf_file in enroute_pdfs:
                    index_entries.append({
                        "id": str(chart_id),
                        "code": "enroute",
                        "name": pdf_file.name,
                        "path": pdf_file.name.replace("\\", "/"),
                        "sort": "enroute"
                    })
                    chart_id += 1

                # 保存航路图索引文件
                index_file = self.enroute_path / "index.json"
                with open(index_file, "w", encoding="utf-8") as f:
                    json.dump(index_entries, f, ensure_ascii=False, indent=4)

                logger.info(f"航路图索引生成完成，图表数量: {len(index_entries)}")
            else:
                logger.warning(f"ENROUTE 目录不存在: {self.enroute_path}")

        except Exception as e:
            logger.error(f"生成索引失败: {e}", exc_info=True)

    def process(self, actions: Optional[List[str]] = None) -> None:
        """
        处理航图数据

        Args:
            actions: 要执行的操作列表 ["rename", "organize", "index"]
        """
        valid_actions = ["rename", "organize", "index"]
        actions_to_run = actions if actions else valid_actions

        logger.info(f"开始处理航图，操作: {actions_to_run}")

        if not isinstance(actions_to_run, list):
            logger.error(f"参数类型错误: {actions_to_run}")
            return

        invalid_actions = [act for act in actions_to_run if act not in valid_actions]
        if invalid_actions:
            logger.error(f"存在无效的操作: {invalid_actions}")
            return

        if not self.validate_paths():
            logger.error("路径验证失败，停止处理")
            return

        try:
            for action in actions_to_run:
                logger.info(f"执行操作: {action}")
                if action == "rename":
                    self.rename_chart_files()
                elif action == "organize":
                    self.organize_airport_files()
                elif action == "index":
                    self.generate_index()

            logger.info(f"处理完成: {actions_to_run}")

        except Exception as e:
            logger.error(f"处理过程出错: {e}", exc_info=True)
