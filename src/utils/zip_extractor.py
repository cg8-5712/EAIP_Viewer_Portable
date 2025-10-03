"""
Zip Extractor - 压缩包解压工具
"""

import zipfile
from pathlib import Path
from typing import Optional


class ZipExtractor:
    """ZIP 文件解压器"""

    def __init__(self):
        pass

    def extract(self, zip_path: str, extract_to: str, password: Optional[str] = None) -> bool:
        """
        解压 ZIP 文件

        Args:
            zip_path: ZIP 文件路径
            extract_to: 解压目标目录
            password: 密码（可选）

        Returns:
            是否成功

        Raises:
            FileNotFoundError: ZIP 文件不存在
            zipfile.BadZipFile: 不是有效的 ZIP 文件
        """
        zip_file_path = Path(zip_path)
        if not zip_file_path.exists():
            raise FileNotFoundError(f"ZIP 文件不存在: {zip_path}")

        extract_path = Path(extract_to)
        extract_path.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                if password:
                    zip_ref.setpassword(password.encode('utf-8'))

                # 解压所有文件
                zip_ref.extractall(extract_path)

            return True

        except zipfile.BadZipFile as e:
            raise zipfile.BadZipFile(f"无效的 ZIP 文件: {str(e)}")

        except Exception as e:
            print(f"解压失败: {e}")
            return False

    def list_contents(self, zip_path: str) -> list:
        """
        列出 ZIP 文件内容

        Args:
            zip_path: ZIP 文件路径

        Returns:
            文件列表
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
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
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 尝试读取文件列表
                zip_ref.namelist()
                return True
        except:
            return False
