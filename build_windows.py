"""
Windows 打包脚本 - 使用 Nuitka
运行前请确保已安装: pip install nuitka ordered-set zstandard
"""

import subprocess
import sys
import os

# 设置 UTF-8 编码（兼容 Windows 环境）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_requirements():
    """检查必要的依赖"""
    print("检查依赖...")
    try:
        import nuitka
        print("✓ Nuitka 已安装")
    except ImportError:
        print("✗ Nuitka 未安装")
        print("请运行: pip install nuitka ordered-set zstandard")
        return False

    # 检查 Visual Studio 或 MinGW
    print("\n注意: Nuitka 需要 C 编译器")
    print("  - Visual Studio 2019+ (推荐)")
    print("  - 或 MinGW64")

    return True

def build():
    """执行打包"""
    if not check_requirements():
        sys.exit(1)

    print("\n" + "="*60)
    print("开始打包 EAIP Viewer (Windows)")
    print("="*60 + "\n")

    # Nuitka 编译参数
    args = [
        sys.executable, '-m', 'nuitka',
        '--standalone',                    # 独立模式
        '--onefile',                       # 单文件
        '--windows-console-mode=disable',  # 无控制台窗口
        '--enable-plugin=pyside6',         # PySide6 插件
        '--include-qt-plugins=qml',        # 包含 QML 插件
        '--include-package=PySide6.QtPdf', # 包含 QtPdf 模块

        # 包含数据目录
        '--include-data-dir=src/qml=qml',
        '--include-data-dir=src/resources=resources',
        '--include-data-dir=src/i18n=i18n',
        '--include-data-dir=config=config',

        # Windows 元数据
        '--company-name=EAIP Viewer Team',
        '--product-name=EAIP Viewer',
        '--file-version=1.0.0',
        '--product-version=1.0.0',
        '--file-description=Electronic Aeronautical Information Publication Viewer Portable',

        # 输出设置
        '--output-dir=dist',
        '--output-filename=EAIPViewer.exe',

        # 性能优化
        '--lto=yes',                       # 链接时优化
        '--jobs=32',                       # 并行编译

        # 入口文件
        'src/main.py'
    ]

    # 如果有图标文件，添加图标参数
    icon_path = 'src/resources/images/app_icon.ico'
    if os.path.exists(icon_path):
        args.insert(-1, f'--windows-icon-from-ico={icon_path}')
        print(f"✓ 使用图标: {icon_path}\n")
    else:
        print(f"⚠ 未找到图标文件: {icon_path}\n")

    print("编译命令:")
    print(' '.join(args))
    print("\n" + "="*60)
    print("编译中，请耐心等待 (通常需要 5-15 分钟)...")
    print("="*60 + "\n")

    # 执行编译
    result = subprocess.run(args)

    if result.returncode == 0:
        print("\n" + "="*60)
        print("✓ 打包成功!")
        print("="*60)
        print(f"\n输出目录: dist\\EAIPViewer.dist\\")
        print(f"主程序: dist\\EAIPViewer.dist\\EAIPViewer.exe")
        print("\n提示:")
        print("  - 整个 EAIPViewer.dist 文件夹包含所有依赖")
        print("  - 文件夹大小约 150-250 MB")
        print("  - 可直接分发整个文件夹，无需 Python 环境")
        print("  - 启动速度快，无需解压临时文件")
    else:
        print("\n" + "="*60)
        print("✗ 打包失败")
        print("="*60)
        print("\n常见问题:")
        print("  1. 未安装 C 编译器 (需要 Visual Studio 或 MinGW)")
        print("  2. 依赖包未安装: pip install -r requirements.txt")
        print("  3. Nuitka 未安装: pip install nuitka ordered-set zstandard")

    sys.exit(result.returncode)

if __name__ == '__main__':
    build()
