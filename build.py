"""
Nuitka 打包脚本 - EAIP Viewer
使用 Nuitka 编译为优化的原生可执行文件
"""

import os
import sys
import shutil
from pathlib import Path

# 项目配置
APP_NAME = "EAIP_Viewer"
MAIN_SCRIPT = "src/main.py"
ICON_FILE = "resources/icon.ico"  # 如果有图标的话
VERSION = "1.0.0"

# 输出目录
DIST_DIR = Path("dist")
BUILD_DIR = Path("build")

def clean_build_dirs():
    """清理构建目录"""
    print("[1/5] 清理旧的构建文件...")

    for dir_path in [DIST_DIR, BUILD_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  - 已删除: {dir_path}")

    print("  ✓ 清理完成\n")

def build_with_nuitka():
    """使用 Nuitka 构建"""
    print("[2/5] 使用 Nuitka 编译...")

    # 基本参数
    nuitka_args = [
        "python", "-m", "nuitka",

        # 输出配置
        f"--output-dir={BUILD_DIR}",
        "--standalone",  # 独立模式（多文件）
        "--onefile-tempdir-spec=%TEMP%/eaip_viewer",  # 如果需要临时文件

        # 应用配置
        f"--output-filename={APP_NAME}.exe",
        "--windows-console-mode=disable",  # 禁用控制台（GUI应用）

        # 性能优化
        "--lto=yes",  # 链接时优化
        "--follow-imports",  # 跟踪所有导入

        # PySide6 支持
        "--enable-plugin=pyside6",
        "--include-qt-plugins=all",  # 包含所有 Qt 插件

        # 包含的包
        "--include-package=PySide6",
        "--include-package=utils",
        "--include-package=controllers",
        "--include-package=models",
        "--include-package=qml",

        # 数据文件（QML 文件）
        "--include-data-dir=src/qml=qml",

        # 其他选项
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
    ]

    # 添加图标（如果存在）
    icon_path = Path(ICON_FILE)
    if icon_path.exists():
        nuitka_args.append(f"--windows-icon-from-ico={ICON_FILE}")
        print(f"  - 使用图标: {ICON_FILE}")

    # 添加主脚本
    nuitka_args.append(MAIN_SCRIPT)

    # 执行构建
    print(f"  - 执行命令: {' '.join(nuitka_args)}\n")
    result = os.system(" ".join(nuitka_args))

    if result != 0:
        print("  ✗ 编译失败!")
        sys.exit(1)

    print("  ✓ 编译完成\n")

def organize_distribution():
    """组织发布目录结构"""
    print("[3/5] 组织发布目录...")

    # 创建发布目录结构
    dist_root = DIST_DIR / APP_NAME
    dist_root.mkdir(parents=True, exist_ok=True)

    # 1. 复制编译后的可执行文件和依赖
    build_output = BUILD_DIR / f"{APP_NAME}.dist"
    if build_output.exists():
        # 复制所有文件
        for item in build_output.iterdir():
            dest = dist_root / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        print(f"  - 已复制编译文件到: {dist_root}")

    # 2. 创建配置目录
    config_dir = dist_root / "config"
    config_dir.mkdir(exist_ok=True)

    # 复制配置示例
    config_example = Path("config/settings.json.example")
    if config_example.exists():
        shutil.copy2(config_example, config_dir)
        print(f"  - 已复制配置示例到: config/")

    # 复制配置说明
    config_readme = Path("config/README.md")
    if config_readme.exists():
        shutil.copy2(config_readme, config_dir)
        print(f"  - 已复制配置说明到: config/")

    # 3. 创建其他必要目录（空目录，但有 .gitkeep）
    for dirname in ["data", "cache", "logs"]:
        dir_path = dist_root / dirname
        dir_path.mkdir(exist_ok=True)
        (dir_path / ".gitkeep").touch()

    print("  ✓ 目录结构组织完成\n")

def create_readme():
    """创建使用说明"""
    print("[4/5] 创建使用说明...")

    dist_root = DIST_DIR / APP_NAME
    readme_content = f"""# EAIP Viewer {VERSION}

## 快速开始

1. 双击 `{APP_NAME}.exe` 启动程序
2. 首次使用请导入 EAIP 数据（ZIP 格式）

## 目录说明

- `{APP_NAME}.exe` - 主程序
- `_internal/` - 程序依赖文件（请勿删除）
- `config/` - 配置文件夹
  - `settings.json.example` - 配置示例
  - `settings.json` - 实际配置（自动生成）
  - `README.md` - 配置说明
- `data/` - 航图数据（导入后生成）
- `cache/` - 缓存文件（自动生成）
- `logs/` - 日志文件（自动生成）

## 便携使用

整个文件夹可以复制到任何位置或 U 盘使用，无需安装。

## 配置

首次使用会自动创建默认配置，如需自定义：
1. 复制 `config/settings.json.example` 为 `config/settings.json`
2. 编辑 `settings.json` 修改配置
3. 重启程序生效

详细配置说明请查看 `config/README.md`

## 系统要求

- Windows 10/11 x64
- 500MB 可用磁盘空间（不含航图数据）

## 技术支持

- GitHub: https://github.com/your-repo/eaip-viewer
- 问题反馈: Issues
- 文档: Wiki

---
构建版本: {VERSION}
构建工具: Nuitka
"""

    readme_path = dist_root / "使用说明.txt"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"  - 已创建: 使用说明.txt")
    print("  ✓ 使用说明创建完成\n")

def create_archive():
    """创建压缩包"""
    print("[5/5] 创建发布压缩包...")

    dist_root = DIST_DIR / APP_NAME
    archive_name = f"{APP_NAME}_v{VERSION}_Windows_x64"

    # 创建 ZIP 压缩包
    shutil.make_archive(
        DIST_DIR / archive_name,
        'zip',
        DIST_DIR,
        APP_NAME
    )

    archive_path = DIST_DIR / f"{archive_name}.zip"
    size_mb = archive_path.stat().st_size / (1024 * 1024)

    print(f"  - 压缩包: {archive_path}")
    print(f"  - 大小: {size_mb:.1f} MB")
    print("  ✓ 压缩包创建完成\n")

def main():
    """主构建流程"""
    print("=" * 60)
    print(f"  EAIP Viewer {VERSION} - Nuitka 构建脚本")
    print("=" * 60)
    print()

    # 检查 Nuitka 是否安装
    result = os.system("python -m nuitka --version >nul 2>&1")
    if result != 0:
        print("✗ 错误: 未安装 Nuitka")
        print("\n请先安装: pip install nuitka")
        sys.exit(1)

    try:
        # 执行构建步骤
        clean_build_dirs()
        build_with_nuitka()
        organize_distribution()
        create_readme()
        create_archive()

        print("=" * 60)
        print("  ✓ 构建完成!")
        print("=" * 60)
        print(f"\n发布文件: dist/{APP_NAME}_v{VERSION}_Windows_x64.zip")
        print(f"测试运行: dist/{APP_NAME}/{APP_NAME}.exe\n")

    except KeyboardInterrupt:
        print("\n\n✗ 构建已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
