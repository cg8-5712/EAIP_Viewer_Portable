"""
EAIP Chart Processor
处理 EAIP 航图数据：解压、重命名、分类、索引
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import re

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

    def __init__(self, data_path: Path, dir_name: str = "EAIP") -> None:
        """
        初始化航图处理器

        Args:
            data_path: 数据根目录
            dir_name: EAIP 目录名称
        """
        self.data_path = data_path
        self.dir_name = dir_name
        self.terminal_path = data_path / "Data" / dir_name / "Terminal"
        self.json_path = data_path / "Data" / "JsonPath" / "AD.JSON"

    def validate_paths(self) -> bool:
        """验证路径有效性"""
        if not self.data_path.exists():
            print(f"[ERROR] 数据目录不存在: {self.data_path}")
            return False

        if not self.terminal_path.exists():
            print(f"[WARNING] Terminal目录不存在: {self.terminal_path}")
            # 尝试创建
            self.terminal_path.mkdir(parents=True, exist_ok=True)

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
        """从路径提取ICAO代码"""
        for i, part in enumerate(path.parts):
            if "GeneralDoc" in part:
                return "GeneralDoc"
            if "Terminal" in part and i + 1 < len(path.parts):
                return path.parts[i + 1]
        return None

    def rename_chart_files(self) -> None:
        """重命名航图文件（基于 AD.JSON）"""
        if not self.json_path.exists():
            print(f"[WARNING] AD.JSON 文件不存在: {self.json_path}")
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                chart_data = json.load(file)
            print(f"[INFO] 读取航图数据: {self.json_path}")

            for chart in chart_data:
                if not chart.get("pdfPath"):
                    continue

                old_path = self.data_path / chart["pdfPath"].lstrip("/")
                icao = self.get_icao_from_path(old_path)

                if not icao:
                    print(f"[WARNING] 无法确定 ICAO 代码: {old_path}")
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
                        print(f"[SUCCESS] 重命名: {old_path.name} -> {new_path}")
                    except OSError as e:
                        print(f"[ERROR] 重命名失败: {old_path}, {e}")
                else:
                    print(f"[WARNING] 文件不存在: {old_path}")

        except Exception as e:
            print(f"[ERROR] 重命名过程失败: {e}")

    def organize_airport_files(self) -> None:
        """整理机场文件到分类文件夹"""
        try:
            if not self.terminal_path.exists():
                print(f"[ERROR] Terminal 目录不存在: {self.terminal_path}")
                return

            airports = [d for d in self.terminal_path.iterdir() if d.is_dir()]
            print(f"[INFO] 开始整理机场文件，机场数量: {len(airports)}")

            for airport in airports:
                airport_path = self.terminal_path / airport.name
                for pdf_file in airport_path.glob("*.pdf"):
                    for chart_type in self.CHART_TYPES:
                        if chart_type in pdf_file.name:
                            type_folder = airport_path / chart_type
                            type_folder.mkdir(parents=True, exist_ok=True)
                            new_path = type_folder / pdf_file.name
                            pdf_file.rename(new_path)
                            print(f"[SUCCESS] 移动文件: {pdf_file.name} -> {chart_type}/")
                            break

        except Exception as e:
            print(f"[ERROR] 整理文件失败: {e}")

    def generate_index(self) -> None:
        """生成航图索引 (index.json)"""
        try:
            if not self.terminal_path.exists():
                print(f"[ERROR] Terminal 目录不存在: {self.terminal_path}")
                return

            airports = [d for d in self.terminal_path.iterdir() if d.is_dir()]

            for airport in airports:
                airport_path = self.terminal_path / airport.name
                self.merge_special_charts(airport_path)

                index_entries: List[Dict[str, str]] = []
                chart_id = 1

                # 处理根目录下的PDF文件
                for pdf_file in airport_path.glob("*.pdf"):
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
                for folder in airport_path.iterdir():
                    if not folder.is_dir():
                        continue

                    for pdf_file in folder.glob("*.pdf"):
                        path = f"{folder.name}/{pdf_file.name}".replace("\\", "/")
                        # 提取 code（去掉机场代码前缀）
                        code = pdf_file.name.split(folder.name)[0]
                        if f"{airport.name}-" in code:
                            code = code.split(f"{airport.name}-")[-1]

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

                print(f"[SUCCESS] 索引生成完成: {airport.name}, 图表数量: {len(index_entries)}")

        except Exception as e:
            print(f"[ERROR] 生成索引失败: {e}")

    def process(self, actions: Optional[List[str]] = None) -> None:
        """
        处理航图数据

        Args:
            actions: 要执行的操作列表 ["rename", "organize", "index"]
        """
        valid_actions = ["rename", "organize", "index"]
        actions_to_run = actions if actions else valid_actions

        if not isinstance(actions_to_run, list):
            print(f"[ERROR] 参数类型错误: {actions_to_run}")
            return

        invalid_actions = [act for act in actions_to_run if act not in valid_actions]
        if invalid_actions:
            print(f"[ERROR] 存在无效的操作: {invalid_actions}")
            return

        if not self.validate_paths():
            print("[ERROR] 路径验证失败，停止处理")
            return

        try:
            for action in actions_to_run:
                print(f"[INFO] 执行 {action} 操作...")
                if action == "rename":
                    self.rename_chart_files()
                elif action == "organize":
                    self.organize_airport_files()
                elif action == "index":
                    self.generate_index()

            print(f"[SUCCESS] 处理完成: {actions_to_run}")

        except Exception as e:
            print(f"[ERROR] 处理过程出错: {e}")
