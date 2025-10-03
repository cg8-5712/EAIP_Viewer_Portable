"""
Data Manager - 处理数据导入、解析和保存
"""

from PySide6.QtCore import QObject, Signal, Slot, Property
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
from utils.zip_extractor import ZipExtractor
from utils.chart_processor import ChartProcessor
from utils.eaip_handler import EaipHandler
from utils.logger import Logger

logger = Logger.get_logger("DataManager")


class DataManager(QObject):
    """数据管理器"""

    # 信号定义
    dataImportStarted = Signal()
    dataImportProgress = Signal(int, str)  # 进度百分比, 状态信息
    dataImportCompleted = Signal(bool, str)  # 成功/失败, 消息
    airportsLoaded = Signal(list)  # 机场数据加载完成
    periodUpdated = Signal(dict)  # AIRAC 周期更新完成

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("初始化 DataManager")
        self._data_path = Path("./data")
        self._extractor = ZipExtractor()
        self._eaip_handler: Optional[EaipHandler] = None
        self._airac_period = "2505"  # 默认周期
        self._dir_name = "EAIP"  # 默认目录名

        # 初始化 EAIP 处理器
        self._initialize_eaip_handler()
        logger.info("DataManager 初始化完成")

    def _initialize_eaip_handler(self):
        """初始化 EAIP 处理器"""
        try:
            logger.debug(f"初始化 EAIP 处理器: period={self._airac_period}, dir={self._dir_name}")
            self._eaip_handler = EaipHandler(
                self._data_path,
                self._airac_period,
                self._dir_name
            )
            logger.info("EAIP 处理器初始化成功")
        except Exception as e:
            logger.warning(f"EAIP 处理器初始化失败: {e}")

    @Slot(str)
    def importDataFromZip(self, zip_path: str):
        """
        从压缩包导入 EAIP 数据

        Args:
            zip_path: 压缩包文件路径
        """
        logger.info(f"开始导入数据: {zip_path}")
        self.dataImportStarted.emit()

        # 解压到临时目录
        temp_extract_path = self._data_path / "temp_extract"

        try:
            # 1. 解压文件 (20%)
            logger.debug("解压文件中...")
            self.dataImportProgress.emit(20, "正在解压文件...")

            try:
                self._extractor.extract(zip_path, str(temp_extract_path))
                logger.info(f"文件解压完成: {temp_extract_path}")
            except FileNotFoundError as e:
                error_msg = "找不到指定的 ZIP 文件，请检查文件路径"
                logger.error(f"{error_msg}: {e}")
                self.dataImportCompleted.emit(False, error_msg)
                return
            except OSError as e:
                # 磁盘空间不足或其他 IO 错误
                error_msg = str(e)
                if "磁盘空间不足" in error_msg or "No space left on device" in error_msg:
                    user_msg = "❌ 磁盘空间不足，无法完成数据导入\n\n请释放磁盘空间后重试"
                    logger.error(f"磁盘空间不足: {e}")
                else:
                    user_msg = f"❌ 解压失败: {error_msg}\n\n已自动清理不完整的文件"
                    logger.error(f"解压失败: {e}")
                self.dataImportCompleted.emit(False, user_msg)
                return
            except Exception as e:
                error_msg = f"❌ 解压失败: {str(e)}\n\n已自动清理不完整的文件"
                logger.error(f"解压异常: {e}", exc_info=True)
                self.dataImportCompleted.emit(False, error_msg)
                return

            # 2. 检测解压后的根文件夹和 AIRAC 周期 (30%)
            logger.debug("检测解压后的文件结构...")
            self.dataImportProgress.emit(30, "正在检测数据结构...")

            # 查找解压后的根文件夹
            extracted_items = list(temp_extract_path.iterdir())
            logger.debug(f"解压后的顶层项目: {[item.name for item in extracted_items]}")

            if not extracted_items:
                error_msg = "❌ 解压后未找到任何文件，压缩包可能为空"
                logger.error(error_msg)
                self._cleanup_temp(temp_extract_path)
                self.dataImportCompleted.emit(False, error_msg)
                return

            # 找到根文件夹（通常是第一个文件夹，名称可能包含 EAIP 和周期信息）
            root_folder = None
            for item in extracted_items:
                if item.is_dir():
                    root_folder = item
                    break

            if not root_folder:
                error_msg = "❌ 解压后未找到数据文件夹"
                logger.error(error_msg)
                self._cleanup_temp(temp_extract_path)
                self.dataImportCompleted.emit(False, error_msg)
                return

            logger.info(f"检测到根文件夹: {root_folder.name}")

            # 从根文件夹名提取 AIRAC 周期（例如 EAIP2025-11 -> 2511）
            detected_period = self._extract_airac_period(root_folder.name)
            if detected_period:
                logger.info(f"从文件夹名检测到 AIRAC 周期: {detected_period}")
                self._airac_period = detected_period
            else:
                logger.warning(f"无法从文件夹名 {root_folder.name} 提取 AIRAC 周期，使用默认值")

            # 最终存储路径
            final_path = self._data_path / self._airac_period
            logger.debug(f"最终存储路径: {final_path}")

            # 移动根文件夹到最终位置
            if final_path.exists():
                logger.warning(f"目标路径已存在，将被覆盖: {final_path}")
                import shutil
                shutil.rmtree(final_path)

            root_folder.rename(final_path)
            logger.info(f"数据已移动到: {final_path}")

            # 清理临时目录
            self._cleanup_temp(temp_extract_path)

            # 3. 处理 EAIP 数据 (40%)
            logger.debug("处理航图数据...")
            self.dataImportProgress.emit(40, "正在处理航图数据...")

            # 自动检测 EAIP 目录名
            if self._eaip_handler:
                self._eaip_handler.airac_period = self._airac_period
                self._eaip_handler.base_path = final_path
                detected_dir = self._eaip_handler.auto_detect_dir_name()
                if detected_dir:
                    logger.info(f"检测到 EAIP 目录: {detected_dir}")
                    self._dir_name = detected_dir
                    self._eaip_handler.dir_name = detected_dir
                    self._eaip_handler.terminal_path = final_path / "Data" / detected_dir / "Terminal"

            # 4. 使用 ChartProcessor 处理数据 (60%)
            logger.debug("重命名和分类航图...")
            self.dataImportProgress.emit(60, "正在重命名和分类航图...")
            processor = ChartProcessor(final_path, self._dir_name)
            processor.process(["rename", "organize"])
            logger.info("航图重命名和分类完成")

            # 5. 生成索引 (80%)
            logger.debug("生成索引...")
            self.dataImportProgress.emit(80, "正在生成索引...")
            processor.process(["index"])
            logger.info("索引生成完成")

            # 6. 加载机场数据 (100%)
            logger.debug("加载机场数据...")
            self.dataImportProgress.emit(100, "导入完成")
            airports_data = self.loadSavedAirports()

            logger.info(f"数据导入成功: {len(airports_data)} 个机场")
            self.dataImportCompleted.emit(True, f"✅ 成功导入 {len(airports_data)} 个机场数据\n\nAIRAC 周期: {self._airac_period}")
            self.airportsLoaded.emit(airports_data)

        except Exception as e:
            # 其他未预料的错误，尝试清理
            logger.error(f"导入失败: {e}", exc_info=True)

            # 清理临时目录
            self._cleanup_temp(temp_extract_path)

            error_msg = f"❌ 导入失败: {str(e)}\n\n已自动清理临时文件"
            self.dataImportCompleted.emit(False, error_msg)

    def _extract_airac_period(self, folder_name: str) -> Optional[str]:
        """
        从文件夹名提取 AIRAC 周期

        Args:
            folder_name: 文件夹名称，如 "EAIP2025-11"

        Returns:
            AIRAC 周期，如 "2511"，失败返回 None
        """
        import re

        # 尝试匹配 YYYY-MM 格式
        match = re.search(r'(\d{4})-(\d{1,2})', folder_name)
        if match:
            year = match.group(1)
            month = match.group(2).zfill(2)
            # 转换为 YYMM 格式
            period = year[2:] + month
            logger.debug(f"从 {folder_name} 提取周期: {period}")
            return period

        # 尝试匹配 YYMM 格式
        match = re.search(r'(\d{4})', folder_name)
        if match and len(match.group(1)) == 4:
            period = match.group(1)
            logger.debug(f"从 {folder_name} 提取周期: {period}")
            return period

        logger.warning(f"无法从 {folder_name} 提取 AIRAC 周期")
        return None

    def _cleanup_temp(self, temp_path: Path):
        """清理临时目录"""
        if temp_path.exists():
            logger.debug(f"清理临时目录: {temp_path}")
            try:
                import shutil
                shutil.rmtree(temp_path)
                logger.info("临时目录清理完成")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")

    @Slot(str, result=dict)
    def updateAiracPeriod(self, period: str) -> Dict[str, Any]:
        """
        更新 AIRAC 周期

        Args:
            period: AIRAC 周期（如 "2505"）

        Returns:
            更新结果
        """
        if not self._eaip_handler:
            return {"success": False, "message": "EAIP 处理器未初始化"}

        result = self._eaip_handler.update_period(period)
        if result.get("success"):
            self._airac_period = period
            self._dir_name = result.get("dir_name", "EAIP")
            self.periodUpdated.emit(result)

        return result

    def _parseAirportsData(self, data_path: Path) -> List[Dict[str, Any]]:
        """
        解析机场数据（从 EAIP Terminal 目录）

        Args:
            data_path: 数据目录路径

        Returns:
            机场数据列表
        """
        logger.debug(f"开始解析机场数据: {data_path}")
        airports = []

        # 扫描 Terminal 目录
        terminal_path = data_path / "Data" / self._dir_name / "Terminal"
        logger.debug(f"Terminal 路径: {terminal_path}")

        if not terminal_path.exists():
            logger.warning(f"Terminal 目录不存在: {terminal_path}")
            return airports

        logger.debug(f"Terminal 目录存在: {terminal_path}")

        # 列出所有目录
        all_items = list(terminal_path.iterdir())
        logger.debug(f"Terminal 目录下的项目数: {len(all_items)}")

        for airport_dir in all_items:
            if not airport_dir.is_dir():
                logger.debug(f"跳过非目录项: {airport_dir.name}")
                continue

            icao = airport_dir.name
            index_file = airport_dir / "index.json"
            logger.debug(f"处理机场: {icao}, 索引文件: {index_file}")

            # 读取索引获取航图分类
            categories = []
            chart_count = 0

            if index_file.exists():
                try:
                    with open(index_file, "r", encoding="utf-8") as f:
                        charts = json.load(f)
                        chart_count = len(charts)
                        # 提取所有分类
                        categories = list(set(chart.get("sort", "general") for chart in charts))
                    logger.debug(f"  {icao}: {chart_count} 个航图, 分类: {categories}")
                except Exception as e:
                    logger.error(f"读取索引失败 {icao}: {e}")
            else:
                logger.warning(f"  {icao}: 索引文件不存在")

            airports.append({
                'code': icao,
                'name_zh': f'{icao} 机场',
                'name_en': f'{icao} Airport',
                'categories': categories,
                'chart_count': chart_count
            })

        logger.info(f"解析机场数据完成，共 {len(airports)} 个机场")
        return airports

    def _saveAirportsData(self, airports_data: List[Dict[str, Any]]):
        """
        保存机场数据到本地

        Args:
            airports_data: 机场数据列表
        """
        save_path = self._data_path / "airports.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump({
                'version': '1.0',
                'airac_period': self._airac_period,
                'dir_name': self._dir_name,
                'airports': airports_data
            }, f, ensure_ascii=False, indent=2)

    @Slot(result=list)
    def loadSavedAirports(self) -> List[Dict[str, Any]]:
        """
        加载已保存的机场数据

        Returns:
            机场数据列表
        """
        logger.debug("开始加载机场数据")

        # 优先从 Terminal 目录加载最新数据
        terminal_path = self._data_path / self._airac_period / "Data" / self._dir_name / "Terminal"
        logger.debug(f"检查 Terminal 目录: {terminal_path}")

        if terminal_path.exists():
            logger.info(f"从 Terminal 目录加载机场数据: {terminal_path}")
            airports = self._parseAirportsData(self._data_path / self._airac_period)
            if airports:
                logger.info(f"加载成功: {len(airports)} 个机场")
                self.airportsLoaded.emit(airports)
                return airports
            else:
                logger.warning("Terminal 目录存在但未找到机场数据")
        else:
            logger.debug(f"Terminal 目录不存在: {terminal_path}")

        # 否则从保存的 JSON 加载
        save_path = self._data_path / "airports.json"
        logger.debug(f"尝试从 JSON 文件加载: {save_path}")

        if not save_path.exists():
            logger.warning(f"机场数据文件不存在: {save_path}")
            return []

        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 更新周期信息
                self._airac_period = data.get('airac_period', self._airac_period)
                self._dir_name = data.get('dir_name', self._dir_name)
                airports = data.get('airports', [])
                logger.info(f"从 JSON 加载成功: {len(airports)} 个机场")
                self.airportsLoaded.emit(airports)
                return airports
        except Exception as e:
            logger.error(f"加载机场数据失败: {e}", exc_info=True)
            return []

    @Slot(str, str, result=list)
    def loadChartsForAirport(self, airport_code: str, category: str = "") -> List[Dict[str, Any]]:
        """
        加载指定机场的航图数据（使用 EAIP Handler）

        Args:
            airport_code: 机场代码
            category: 分类（可选）

        Returns:
            航图数据列表
        """
        if not self._eaip_handler:
            return []

        charts = self._eaip_handler.get_chart_list(
            icao=airport_code,
            search_type=category if category else None
        )

        return charts if charts else []

    @Slot(str, str, result=str)
    def getChartByCode(self, airport_code: str, chart_code: str) -> str:
        """
        通过代码获取航图路径

        Args:
            airport_code: 机场代码
            chart_code: 航图代码

        Returns:
            航图文件路径
        """
        if not self._eaip_handler:
            return ""

        try:
            # 获取航图数据
            result = self._eaip_handler.get_chart_by_code(airport_code, chart_code)
            if isinstance(result, bytes):
                # 如果是图片数据，需要保存到临时文件
                temp_path = self._data_path / "cache" / f"{airport_code}_{chart_code}.png"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, 'wb') as f:
                    f.write(result)
                return str(temp_path)
            else:
                return result  # 错误信息
        except Exception as e:
            return f"获取航图失败: {e}"
