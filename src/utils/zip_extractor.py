"""
Zip Extractor - 压缩包解压工具
"""

import zipfile
import shutil
from pathlib import Path
from typing import Optional, Callable
from utils.logger import Logger

logger = Logger.get_logger("ZipExtractor")


class ZipExtractor:
    """ZIP 文件解压器"""

    def __init__(self):
        pass

    def extract(
        self,
        zip_path: str,
        extract_to: str,
        password: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        解压 ZIP 文件

        Args:
            zip_path: ZIP 文件路径
            extract_to: 解压目标目录
            password: 密码（可选）
            progress_callback: 进度回调函数 (当前文件索引, 总文件数)

        Returns:
            是否成功

        Raises:
            FileNotFoundError: ZIP 文件不存在
            zipfile.BadZipFile: 不是有效的 ZIP 文件
            OSError: 磁盘空间不足或其他 IO 错误
        """
        logger.debug(f"开始解压: {zip_path} -> {extract_to}")

        zip_file_path = Path(zip_path)
        if not zip_file_path.exists():
            logger.error(f"ZIP 文件不存在: {zip_path}")
            raise FileNotFoundError(f"ZIP 文件不存在: {zip_path}")

        extract_path = Path(extract_to)

        try:
            # 创建解压目录
            extract_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"创建解压目录: {extract_path}")

            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                if password:
                    zip_ref.setpassword(password.encode("utf-8"))

                # 获取文件列表
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                logger.info(f"ZIP 文件包含 {total_files} 个文件")

                # 逐个解压文件并报告进度
                for index, file_name in enumerate(file_list):
                    zip_ref.extract(file_name, extract_path)

                    # 调用进度回调
                    if progress_callback and index % max(1, total_files // 100) == 0:
                        progress_callback(index + 1, total_files)

                # 确保最后报告100%
                if progress_callback:
                    progress_callback(total_files, total_files)

            logger.info(f"解压成功: {extract_path}")
            return True

        except zipfile.BadZipFile as e:
            logger.error(f"无效的 ZIP 文件: {e}")
            raise zipfile.BadZipFile(f"无效的 ZIP 文件: {str(e)}")

        except OSError as e:
            # 捕获磁盘空间不足等错误
            error_msg = str(e)
            logger.error(f"解压失败 (OSError): {error_msg}", exc_info=True)

            # 清理已解压的文件
            if extract_path.exists():
                logger.warning(f"清理不完整的解压目录: {extract_path}")
                try:
                    shutil.rmtree(extract_path)
                    logger.info("清理完成")
                except Exception as cleanup_error:
                    logger.error(f"清理失败: {cleanup_error}")

            # 检查是否是磁盘空间不足
            if "No space left on device" in error_msg or e.errno == 28:
                raise OSError("磁盘空间不足，无法完成解压") from e
            else:
                raise OSError(f"解压失败: {error_msg}") from e

        except Exception as e:
            logger.error(f"解压失败: {e}", exc_info=True)

            # 清理已解压的文件
            if extract_path.exists():
                logger.warning(f"清理不完整的解压目录: {extract_path}")
                try:
                    shutil.rmtree(extract_path)
                    logger.info("清理完成")
                except Exception as cleanup_error:
                    logger.error(f"清理失败: {cleanup_error}")

            raise Exception(f"解压失败: {str(e)}") from e

    def list_contents(self, zip_path: str) -> list:
        """
        列出 ZIP 文件内容

        Args:
            zip_path: ZIP 文件路径

        Returns:
            文件列表
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                return zip_ref.namelist()
        except Exception as e:
            print(f"读取 ZIP 文件失败: {e}")
            return []

    def is_valid_zip(self, zip_path: str) -> bool:
        """
        检查是否是有效的 ZIP 文件

        Args:
            zip_path: ZIP 文件路径

        Returns:
            是否有效
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # 尝试读取文件列表
                zip_ref.namelist()
                return True
        except:
            return False
