"""
Nuitka 打包脚本 - EAIP Viewer (Linux)
使用 Nuitka 编译为优化的原生可执行文件
"""

import os
import sys
import shutil
from pathlib import Path

# 设置 UTF-8 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 项目配置
APP_NAME = "EAIP_Viewer"
MAIN_SCRIPT = "src/main.py"
VERSION = "1.0.0"
DISTRO = "debian"  # 或 "rhel"

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
        sys.executable,
        "-m",
        "nuitka",
        # 输出配置
        f"--output-dir={BUILD_DIR}",
        "--standalone",  # 独立模式
        # 应用配置
        f"--output-filename={APP_NAME}",
        # 编译器选择
        "--clang",  # 使用 Clang 编译器
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
        # 数据文件（QML 文件）
        "--include-data-dir=src/qml=qml",
        # Linux 特定选项
        "--linux-icon=resources/icon.png",  # 如果有图标
        # 调试和详细信息
        "--show-scons",  # 显示 SCons 构建详情
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
        # 主脚本
        MAIN_SCRIPT,
    ]

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

    # 3. 创建启动脚本
    launcher_script = dist_root / "eaip-viewer.sh"
    launcher_content = f"""#!/bin/bash
# EAIP Viewer 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
cd "$SCRIPT_DIR"

# 设置 Qt 平台插件路径
export QT_QPA_PLATFORM_PLUGIN_PATH="$SCRIPT_DIR/_internal/PySide6/Qt/plugins/platforms"
export LD_LIBRARY_PATH="$SCRIPT_DIR/_internal:$LD_LIBRARY_PATH"

# 运行程序
./{APP_NAME} "$@"
"""
    launcher_script.write_text(launcher_content)
    launcher_script.chmod(0o755)
    print(f"  - 已创建启动脚本: {launcher_script.name}")

    # 4. 创建其他必要目录
    for dirname in ["data", "cache", "logs"]:
        dir_path = dist_root / dirname
        dir_path.mkdir(exist_ok=True)
        (dir_path / ".gitkeep").touch()

    print("  ✓ 目录结构组织完成\n")


def create_readme():
    """创建使用说明"""
    print("[4/5] 创建使用说明...")

    dist_root = DIST_DIR / APP_NAME
    readme_content = f"""# EAIP Viewer {VERSION} (Linux {DISTRO.upper()})

## 快速开始

1. 运行启动脚本：`./eaip-viewer.sh`
2. 或直接运行：`./{APP_NAME}`
3. 首次使用请导入 EAIP 数据（ZIP 格式）

## 目录说明

- `{APP_NAME}` - 主程序可执行文件
- `eaip-viewer.sh` - 启动脚本（推荐使用）
- `_internal/` - 程序依赖文件（请勿删除）
- `config/` - 配置文件夹
- `data/` - 航图数据（导入后生成）
- `cache/` - 缓存文件（自动生成）
- `logs/` - 日志文件（自动生成）

## 系统要求

- **Debian/Ubuntu 系**:
  - Ubuntu 20.04 或更高版本
  - Debian 11 或更高版本

- **RHEL 系**:
  - Rocky Linux 9 或更高版本
  - RHEL 9 或更高版本
  - CentOS Stream 9 或更高版本

- **依赖库**: 通常已预装，如缺失请安装：
  ```bash
  # Debian/Ubuntu
  sudo apt-get install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \\
      libxcb-keysyms1 libxcb-render-util0 libxkbcommon-x11-0 libegl1

  # RHEL/Rocky
  sudo dnf install xcb-util-cursor xcb-util-image xcb-util-keysyms \\
      xcb-util-renderutil libxkbcommon-x11 mesa-libEGL
  ```

## 便携使用

整个文件夹可以复制到任何位置使用，无需安装。

## 卸载

直接删除整个文件夹即可。

## 系统集成（可选）

创建桌面快捷方式：

```bash
cat > ~/.local/share/applications/eaip-viewer.desktop << EOF
[Desktop Entry]
Name=EAIP Viewer
Comment=Electronic AIP Viewer
Exec=$(pwd)/eaip-viewer.sh
Icon=$(pwd)/resources/icon.png
Terminal=false
Type=Application
Categories=Utility;
EOF
```

## 问题排查

**程序无法启动**:
1. 确认已安装所需依赖库
2. 检查文件权限：`chmod +x {APP_NAME} eaip-viewer.sh`
3. 查看日志：`cat logs/app.log`

**图形界面问题**:
- 确认已安装 X11 或 Wayland
- 尝试设置环境变量：`export QT_QPA_PLATFORM=xcb`

---
构建版本: {VERSION}
构建工具: Nuitka
目标系统: Linux {DISTRO.upper()}
"""

    readme_path = dist_root / "README.txt"
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"  - 已创建: README.txt")
    print("  ✓ 使用说明创建完成\n")


def create_archive():
    """创建压缩包"""
    print("[5/5] 创建发布压缩包...")

    dist_root = DIST_DIR / APP_NAME
    archive_name = f"{APP_NAME}_v{VERSION}_Linux_x64_{DISTRO}"

    # 创建 tar.gz 压缩包
    import tarfile

    archive_path = DIST_DIR / f"{archive_name}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(dist_root, arcname=APP_NAME)

    size_mb = archive_path.stat().st_size / (1024 * 1024)

    print(f"  - 压缩包: {archive_path}")
    print(f"  - 大小: {size_mb:.1f} MB")
    print("  ✓ 压缩包创建完成\n")


def main():
    """主构建流程"""
    print("=" * 60)
    print(f"  EAIP Viewer {VERSION} - Nuitka 构建脚本 (Linux {DISTRO.upper()})")
    print("=" * 60)
    print()

    # 检查 Nuitka 是否安装
    result = os.system(f"{sys.executable} -m nuitka --version > /dev/null 2>&1")
    if result != 0:
        print("✗ 错误: 未安装 Nuitka")
        print(f"\n请先安装: {sys.executable} -m pip install nuitka")
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
        print(f"\n发布文件: dist/{APP_NAME}_v{VERSION}_Linux_x64_{DISTRO}.tar.gz")
        print(f"测试运行: cd dist/{APP_NAME} && ./eaip-viewer.sh\n")

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
