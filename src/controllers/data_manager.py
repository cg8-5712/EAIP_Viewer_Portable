"""
Data Manager - 处理数据导入、解析和保存
"""

from PySide6.QtCore import QObject, Signal, Slot, Property, QThread
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
from utils.zip_extractor import ZipExtractor
from utils.chart_processor import ChartProcessor
from utils.eaip_handler import EaipHandler
from utils.logger import Logger

logger = Logger.get_logger("DataManager")


class ImportWorker(QThread):
    """导入工作线程"""

    # 信号定义
    progressUpdate = Signal(int, int, int, str, str)  # 当前步骤, 总步骤数, 进度%, 步骤名称, 任务详情
    importFinished = Signal(bool, str, list, int)  # 成功/失败, 消息, 机场数据, 航路图数量

    def __init__(self, zip_path: str, data_path: Path, extractor: ZipExtractor,
                 airac_period: str, dir_name: str, max_workers: int = 4, parent=None):
        super().__init__(parent)
        self.zip_path = zip_path
        self.data_path = data_path
        self.extractor = extractor
        self.airac_period = airac_period
        self.dir_name = dir_name
        self.max_workers = max_workers
        self.eaip_handler = None

    def run(self):
        """执行导入操作"""
        temp_extract_path = self.data_path / "temp_extract"
        total_steps = 6

        try:
            # 1. 解压文件
            logger.debug("解压文件中...")
            self.progressUpdate.emit(1, total_steps, 0, "解压", f"开始解压: {Path(self.zip_path).name}")

            def extract_progress(current, total):
                """解压进度回调"""
                percent = int((current / total) * 100) if total > 0 else 0
                self.progressUpdate.emit(1, total_steps, percent, "解压", f"解压中: {current}/{total} 个文件")

            try:
                self.extractor.extract(self.zip_path, str(temp_extract_path), progress_callback=extract_progress)
                self.progressUpdate.emit(1, total_steps, 100, "解压", "解压完成")
                logger.info(f"文件解压完成: {temp_extract_path}")
            except FileNotFoundError as e:
                error_msg = "找不到指定的 ZIP 文件，请检查文件路径"
                logger.error(f"{error_msg}: {e}")
                self.importFinished.emit(False, error_msg, [], 0)
                return
            except OSError as e:
                error_msg = str(e)
                if "磁盘空间不足" in error_msg or "No space left on device" in error_msg:
                    user_msg = "❌ 磁盘空间不足，无法完成数据导入\n\n请释放磁盘空间后重试"
                    logger.error(f"磁盘空间不足: {e}")
                else:
                    user_msg = f"❌ 解压失败: {error_msg}\n\n已自动清理不完整的文件"
                    logger.error(f"解压失败: {e}")
                self.importFinished.emit(False, user_msg, [], 0)
                return
            except Exception as e:
                error_msg = f"❌ 解压失败: {str(e)}\n\n已自动清理不完整的文件"
                logger.error(f"解压异常: {e}", exc_info=True)
                self.importFinished.emit(False, error_msg, [], 0)
                return

            # 2. 检测解压后的根文件夹和 AIRAC 周期
            logger.debug("检测解压后的文件结构...")
            self.progressUpdate.emit(2, total_steps, 0, "检测数据结构", "开始分析文件结构")

            extracted_items = list(temp_extract_path.iterdir())
            logger.debug(f"解压后的顶层项目: {[item.name for item in extracted_items]}")

            if not extracted_items:
                error_msg = "❌ 解压后未找到任何文件，压缩包可能为空"
                logger.error(error_msg)
                self._cleanup_temp(temp_extract_path)
                self.importFinished.emit(False, error_msg, [], 0)
                return

            self.progressUpdate.emit(2, total_steps, 30, "检测数据结构", "查找数据文件夹")

            root_folder = None
            for item in extracted_items:
                if item.is_dir():
                    root_folder = item
                    break

            if not root_folder:
                error_msg = "❌ 解压后未找到数据文件夹"
                logger.error(error_msg)
                self._cleanup_temp(temp_extract_path)
                self.importFinished.emit(False, error_msg, [], 0)
                return

            logger.info(f"检测到根文件夹: {root_folder.name}")
            self.progressUpdate.emit(2, total_steps, 50, "检测数据结构", f"找到根文件夹: {root_folder.name}")

            # 提取 AIRAC 周期
            detected_period = self._extract_airac_period(root_folder.name)
            if detected_period:
                logger.info(f"从文件夹名检测到 AIRAC 周期: {detected_period}")
                self.airac_period = detected_period
                self.progressUpdate.emit(2, total_steps, 70, "检测数据结构", f"检测到 AIRAC 周期: {detected_period}")
            else:
                logger.warning(f"无法从文件夹名 {root_folder.name} 提取 AIRAC 周期，使用默认值")
                self.progressUpdate.emit(2, total_steps, 70, "检测数据结构", f"使用默认 AIRAC 周期: {self.airac_period}")

            # 移动到最终位置
            final_path = self.data_path / self.airac_period
            logger.debug(f"最终存储路径: {final_path}")

            if final_path.exists():
                logger.warning(f"目标路径已存在，将被覆盖: {final_path}")
                import shutil
                shutil.rmtree(final_path)

            self.progressUpdate.emit(2, total_steps, 85, "检测数据结构", f"移动数据到: {final_path.name}")
            root_folder.rename(final_path)
            logger.info(f"数据已移动到: {final_path}")

            self._cleanup_temp(temp_extract_path)
            self.progressUpdate.emit(2, total_steps, 100, "检测数据结构", "数据结构检测完成")

            # 3. 处理 EAIP 数据
            logger.debug("处理航图数据...")
            self.progressUpdate.emit(3, total_steps, 0, "处理航图数据", "初始化 EAIP 处理器")

            # 自动检测 EAIP 目录名
            from utils.eaip_handler import EaipHandler
            self.eaip_handler = EaipHandler(self.data_path, self.airac_period, self.dir_name)
            self.eaip_handler.base_path = final_path
            self.progressUpdate.emit(3, total_steps, 30, "处理航图数据", "检测 EAIP 目录结构")

            detected_dir = self.eaip_handler.auto_detect_dir_name()
            if detected_dir:
                logger.info(f"检测到 EAIP 目录: {detected_dir}")
                self.dir_name = detected_dir
                self.eaip_handler.dir_name = detected_dir
                self.eaip_handler.terminal_path = final_path / "Data" / detected_dir / "Terminal"
                self.progressUpdate.emit(3, total_steps, 100, "处理航图数据", f"检测到 EAIP 目录: {detected_dir}")
            else:
                self.progressUpdate.emit(3, total_steps, 100, "处理航图数据", f"使用默认 EAIP 目录: {self.dir_name}")

            # 4. 使用 ChartProcessor 处理数据
            logger.debug("重命名和分类航图...")
            self.progressUpdate.emit(4, total_steps, 0, "重命名航图", "开始处理航图文件")

            def rename_progress(current, total, desc):
                """重命名进度回调"""
                percent = int((current / total) * 100) if total > 0 else 0
                self.progressUpdate.emit(4, total_steps, percent, "重命名航图", f"{desc} ({current}/{total})")

            processor = ChartProcessor(final_path, self.dir_name, max_workers=self.max_workers,
                                      progress_callback=rename_progress)
            processor.process(["rename"])
            self.progressUpdate.emit(4, total_steps, 50, "重命名航图", "分类整理航图...")
            processor.process(["organize"])
            self.progressUpdate.emit(4, total_steps, 100, "重命名航图", "航图重命名和分类完成")
            logger.info("航图重命名和分类完成")

            # 5. 生成索引
            logger.debug("生成索引...")
            self.progressUpdate.emit(5, total_steps, 0, "生成索引", f"使用 {self.max_workers} 个线程并行生成")

            def index_progress(current, total, desc):
                """索引生成进度回调"""
                percent = int((current / total) * 100) if total > 0 else 0
                self.progressUpdate.emit(5, total_steps, percent, "生成索引", f"{desc} ({current}/{total})")

            processor.progress_callback = index_progress
            processor.process(["index"])
            self.progressUpdate.emit(5, total_steps, 100, "生成索引", "所有索引生成完成")
            logger.info("索引生成完成")

            # 6. 清理不需要的文件，只保留 Terminal 和 ENROUTE
            logger.debug("清理不需要的文件...")
            self.progressUpdate.emit(6, total_steps, 0, "整理数据", "清理临时文件...")
            self._cleanup_import_files(final_path)

            # 7. 加载机场数据和航路图（从清理后的新位置）
            logger.debug("加载机场数据和航路图...")
            self.progressUpdate.emit(6, total_steps, 50, "整理数据", "开始加载机场列表")
            airports_data = self._parseAirportsData(final_path)
            self.progressUpdate.emit(6, total_steps, 80, "整理数据", "加载航路图信息")
            enroute_count = self._getEnrouteChartCount(final_path)

            self.progressUpdate.emit(6, total_steps, 100, "整理数据", f"加载完成: {len(airports_data)} 个机场 + {enroute_count} 个航路图")

            logger.info(f"数据导入成功: {len(airports_data)} 个机场 + {enroute_count} 个航路图")
            success_msg = f"✅ 成功导入 {len(airports_data)} 个机场 + {enroute_count} 个航路图\n\nAIRAC 周期: {self.airac_period}"
            self.importFinished.emit(True, success_msg, airports_data, enroute_count)

        except Exception as e:
            logger.error(f"导入失败: {e}", exc_info=True)
            self._cleanup_temp(temp_extract_path)
            error_msg = f"❌ 导入失败: {str(e)}\n\n已自动清理临时文件"
            self.importFinished.emit(False, error_msg, [], 0)

    def _cleanup_import_files(self, base_path: Path):
        """
        清理导入后不需要的文件，只保留 Terminal 和 ENROUTE 文件夹

        Args:
            base_path: AIRAC 周期目录
        """
        try:
            import shutil

            logger.info(f"开始清理不需要的文件: {base_path}")

            # 定位 Terminal 和 ENROUTE 文件夹
            terminal_src = base_path / "Data" / self.dir_name / "Terminal"
            enroute_src = base_path / "Data" / self.dir_name / "ENROUTE"

            terminal_dest = base_path / "Terminal"
            enroute_dest = base_path / "ENROUTE"

            # 移动 Terminal 文件夹
            if terminal_src.exists():
                if terminal_dest.exists():
                    shutil.rmtree(terminal_dest)
                shutil.move(str(terminal_src), str(terminal_dest))
                logger.info(f"移动 Terminal 文件夹: {terminal_dest}")
            else:
                logger.warning(f"Terminal 文件夹不存在: {terminal_src}")

            # 移动 ENROUTE 文件夹
            if enroute_src.exists():
                if enroute_dest.exists():
                    shutil.rmtree(enroute_dest)
                shutil.move(str(enroute_src), str(enroute_dest))
                logger.info(f"移动 ENROUTE 文件夹: {enroute_dest}")
            else:
                logger.warning(f"ENROUTE 文件夹不存在: {enroute_src}")

            # 删除 Data 文件夹及其所有内容
            data_folder = base_path / "Data"
            if data_folder.exists():
                shutil.rmtree(data_folder)
                logger.info(f"删除 Data 文件夹: {data_folder}")

            # 删除其他所有文件和文件夹（除了 Terminal 和 ENROUTE）
            for item in base_path.iterdir():
                if item.name not in ["Terminal", "ENROUTE"]:
                    if item.is_dir():
                        shutil.rmtree(item)
                        logger.debug(f"删除文件夹: {item}")
                    else:
                        item.unlink()
                        logger.debug(f"删除文件: {item}")

            logger.info("清理完成，只保留 Terminal 和 ENROUTE 文件夹")

        except Exception as e:
            logger.error(f"清理文件失败: {e}", exc_info=True)

    def _extract_airac_period(self, folder_name: str) -> Optional[str]:
        """从文件夹名提取 AIRAC 周期"""
        import re
        match = re.search(r'(\d{4})-(\d{1,2})', folder_name)
        if match:
            year = match.group(1)
            month = match.group(2).zfill(2)
            period = year[2:] + month
            logger.debug(f"从 {folder_name} 提取周期: {period}")
            return period

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

    def _parseAirportsData(self, data_path: Path) -> List[Dict[str, Any]]:
        """解析机场数据"""
        logger.debug(f"开始解析机场数据: {data_path}")
        airports = []

        terminal_path = data_path / "Terminal"  # 更新后的路径
        logger.debug(f"Terminal 路径: {terminal_path}")

        if not terminal_path.exists():
            logger.warning(f"Terminal 目录不存在: {terminal_path}")
            return airports

        logger.debug(f"Terminal 目录存在: {terminal_path}")

        all_items = list(terminal_path.iterdir())
        logger.debug(f"Terminal 目录下的项目数: {len(all_items)}")

        for airport_dir in all_items:
            if not airport_dir.is_dir():
                logger.debug(f"跳过非目录项: {airport_dir.name}")
                continue

            icao = airport_dir.name
            index_file = airport_dir / "index.json"
            logger.debug(f"处理机场: {icao}, 索引文件: {index_file}")

            categories = []
            chart_count = 0

            if index_file.exists():
                try:
                    with open(index_file, "r", encoding="utf-8") as f:
                        charts = json.load(f)
                        chart_count = len(charts)
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

        enroute_count = 0
        enroute_path = data_path / "ENROUTE"  # 更新后的路径
        if enroute_path.exists():
            enroute_index = enroute_path / "index.json"
            if enroute_index.exists():
                try:
                    with open(enroute_index, "r", encoding="utf-8") as f:
                        enroute_charts = json.load(f)
                        enroute_count = len(enroute_charts)
                    logger.debug(f"航路图数量: {enroute_count}")
                except Exception as e:
                    logger.error(f"读取航路图索引失败: {e}")

        logger.info(f"解析机场数据完成，共 {len(airports)} 个机场 + {enroute_count} 个航路图")
        return airports

    def _getEnrouteChartCount(self, data_path: Path) -> int:
        """获取航路图数量"""
        try:
            enroute_path = data_path / "ENROUTE"  # 更新后的路径
            logger.debug(f"获取航路图数量: {enroute_path}")

            if not enroute_path.exists():
                logger.warning(f"ENROUTE 目录不存在: {enroute_path}")
                return 0

            index_file = enroute_path / "index.json"
            if not index_file.exists():
                logger.warning(f"ENROUTE 索引文件不存在: {index_file}")
                return 0

            with open(index_file, "r", encoding="utf-8") as f:
                charts = json.load(f)
                count = len(charts)
                logger.debug(f"航路图数量: {count}")
                return count

        except Exception as e:
            logger.error(f"获取航路图数量失败: {e}", exc_info=True)
            return 0


class DataManager(QObject):
    """数据管理器"""

    # 信号定义
    dataImportStarted = Signal()
    dataImportProgress = Signal(int, int, int, str, str)  # 当前步骤, 总步骤数, 进度%, 步骤名称, 任务详情
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
        self._import_worker: Optional[ImportWorker] = None  # 导入工作线程

        # 导入配置
        from utils.config import Config
        self._config = Config()

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
        从压缩包导入 EAIP 数据（使用后台线程）

        Args:
            zip_path: 压缩包文件路径
        """
        logger.info(f"开始导入数据: {zip_path}")

        # 如果有正在运行的导入任务，先停止
        if self._import_worker and self._import_worker.isRunning():
            logger.warning("已有导入任务正在运行")
            return

        # 发送导入开始信号
        self.dataImportStarted.emit()

        # 获取配置的线程数
        max_workers = self._config.getImportWorkers()
        logger.info(f"使用 {max_workers} 个工作线程进行导入")

        # 创建工作线程
        self._import_worker = ImportWorker(
            zip_path,
            self._data_path,
            self._extractor,
            self._airac_period,
            self._dir_name,
            max_workers,
            self
        )

        # 连接信号
        self._import_worker.progressUpdate.connect(self._onProgressUpdate)
        self._import_worker.importFinished.connect(self._onImportFinished)

        # 启动线程
        self._import_worker.start()

    @Slot(int, int, int, str, str)
    def _onProgressUpdate(self, current_step: int, total_steps: int, progress: int,
                         step_name: str, task_detail: str):
        """进度更新"""
        self.dataImportProgress.emit(current_step, total_steps, progress, step_name, task_detail)

    @Slot(bool, str, list, int)
    def _onImportFinished(self, success: bool, message: str, airports_data: list, enroute_count: int):
        """导入完成"""
        if success:
            # 更新 AIRAC 周期和目录名
            if self._import_worker:
                self._airac_period = self._import_worker.airac_period
                self._dir_name = self._import_worker.dir_name

                # 重新初始化 EAIP 处理器
                self._initialize_eaip_handler()

            # 发送机场数据加载信号
            self.airportsLoaded.emit(airports_data)

        # 发送导入完成信号
        self.dataImportCompleted.emit(success, message)

        # 清理工作线程
        if self._import_worker:
            self._import_worker.deleteLater()
            self._import_worker = None

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

    def _getEnrouteChartCount(self, data_path: Path) -> int:
        """
        获取航路图数量

        Args:
            data_path: AIRAC周期数据路径

        Returns:
            航路图数量
        """
        try:
            enroute_path = data_path / "ENROUTE"  # 使用新路径结构
            logger.debug(f"获取航路图数量: {enroute_path}")

            if not enroute_path.exists():
                logger.warning(f"ENROUTE 目录不存在: {enroute_path}")
                return 0

            index_file = enroute_path / "index.json"
            if not index_file.exists():
                logger.warning(f"ENROUTE 索引文件不存在: {index_file}")
                return 0

            with open(index_file, "r", encoding="utf-8") as f:
                charts = json.load(f)
                count = len(charts)
                logger.debug(f"航路图数量: {count}")
                return count

        except Exception as e:
            logger.error(f"获取航路图数量失败: {e}", exc_info=True)
            return 0

    def _parseAirportsData(self, data_path: Path) -> List[Dict[str, Any]]:
        """
        解析机场数据

        Args:
            data_path: AIRAC周期数据路径

        Returns:
            机场数据列表
        """
        logger.debug(f"开始解析机场数据: {data_path}")
        airports = []

        terminal_path = data_path / "Terminal"
        logger.debug(f"Terminal 路径: {terminal_path}")

        if not terminal_path.exists():
            logger.warning(f"Terminal 目录不存在: {terminal_path}")
            return airports

        logger.debug(f"Terminal 目录存在: {terminal_path}")

        all_items = list(terminal_path.iterdir())
        logger.debug(f"Terminal 目录下的项目数: {len(all_items)}")

        for airport_dir in all_items:
            if not airport_dir.is_dir():
                logger.debug(f"跳过非目录项: {airport_dir.name}")
                continue

            icao = airport_dir.name
            index_file = airport_dir / "index.json"
            logger.debug(f"处理机场: {icao}, 索引文件: {index_file}")

            categories = []
            chart_count = 0

            if index_file.exists():
                try:
                    with open(index_file, "r", encoding="utf-8") as f:
                        charts = json.load(f)
                        chart_count = len(charts)
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

        # 扫描 data 目录，查找所有 AIRAC 周期文件夹
        if not self._data_path.exists():
            logger.warning(f"数据目录不存在: {self._data_path}")
            return []

        # 查找所有包含 Terminal 的 AIRAC 周期目录
        airac_periods = []
        for item in self._data_path.iterdir():
            if item.is_dir() and item.name != "cache" and item.name != ".git":
                terminal_path = item / "Terminal"
                if terminal_path.exists() and terminal_path.is_dir():
                    airac_periods.append(item.name)
                    logger.debug(f"发现 AIRAC 周期数据: {item.name}")

        if not airac_periods:
            logger.info("未发现任何 AIRAC 周期数据")
            return []

        # 使用最新的 AIRAC 周期（按名称排序，最大的是最新的）
        latest_period = sorted(airac_periods)[-1]
        logger.info(f"使用最新的 AIRAC 周期: {latest_period}")
        self._airac_period = latest_period

        # 重新初始化 EAIP 处理器
        self._initialize_eaip_handler()

        # 从 Terminal 目录加载数据
        terminal_path = self._data_path / latest_period / "Terminal"
        logger.info(f"从 Terminal 目录加载机场数据: {terminal_path}")

        airports = self._parseAirportsData(self._data_path / latest_period)
        if airports:
            enroute_count = self._getEnrouteChartCount(self._data_path / latest_period)
            logger.info(f"加载成功: {len(airports)} 个机场 + {enroute_count} 个航路图")
            self.airportsLoaded.emit(airports)
            return airports
        else:
            logger.warning("未找到机场数据")
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
