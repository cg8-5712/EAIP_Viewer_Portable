"""
Nuitka 打包脚本 - EAIP Viewer (macOS)
使用 Nuitka 编译为优化的原生 macOS 应用
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 设置 UTF-8 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 项目配置
APP_NAME = "EAIP_Viewer"
APP_DISPLAY_NAME = "EAIP Viewer"
MAIN_SCRIPT = "src/main.py"
VERSION = "1.0.0"
ARCH = "x86_64"  # 或 "arm64" (Apple Silicon)
BUNDLE_ID = "com.eaip.viewer"

# 输出目录
DIST_DIR = Path("dist")
BUILD_DIR = Path("build")


def clean_build_dirs():
    """清理构建目录"""
    print("[1/6] 清理旧的构建文件...")

    for dir_path in [DIST_DIR, BUILD_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  - 已删除: {dir_path}")

    print("  ✓ 清理完成\n")


def build_with_nuitka():
    """使用 Nuitka 构建"""
    print("[2/6] 使用 Nuitka 编译...")

    # 基本参数
    nuitka_args = [
        sys.executable,
        "-m",
        "nuitka",
        # 输出配置
        f"--output-dir={BUILD_DIR}",
        "--standalone",  # 独立模式
        "--macos-create-app-bundle",  # 创建 .app 包
        # 应用配置
        f"--macos-app-name={APP_DISPLAY_NAME}",
        f"--output-filename={APP_NAME}",
        # macOS 特定
        f"--macos-target-arch={ARCH}",
        "--macos-app-mode=gui",  # GUI 应用
        # 编译器选择
        "--clang",  # 使用 Clang 编译器（macOS 默认）
        # 性能优化
        "--lto=yes",  # 链接时优化
        "--follow-imports",  # 跟踪所有导入
        # PySide6 支持
        "--enable-plugin=pyside6",
        "--include-qt-plugins=all",  # 包含所有 Qt 插件
        # 包含的包
        "--include-package=PySide6",
        "--include-package=PySide6.QtPdf",  # 包含 QtPdf 模块
        "--include-package=utils",
        "--include-package=controllers",
        "--include-package=models",
        # 数据文件（QML 文件）
        "--include-data-dir=src/qml=qml",
        # 图标
        "--macos-app-icon=resources/icon.icns",  # 如果有图标
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


def organize_app_bundle():
    """组织 .app 包结构"""
    print("[3/6] 组织 App Bundle...")

    # 找到生成的 .app 包
    app_bundle = BUILD_DIR / f"{APP_DISPLAY_NAME}.app"

    if not app_bundle.exists():
        print(f"  ✗ 未找到 App Bundle: {app_bundle}")
        sys.exit(1)

    # 复制到 dist 目录
    dist_app = DIST_DIR / f"{APP_DISPLAY_NAME}.app"
    if dist_app.exists():
        shutil.rmtree(dist_app)

    shutil.copytree(app_bundle, dist_app)
    print(f"  - 已复制 App Bundle 到: {dist_app}")

    # 创建额外的数据目录（在用户目录）
    # macOS 应用通常将数据存储在 ~/Library/Application Support/
    print("  - macOS 应用将使用标准路径存储数据")
    print("    数据目录: ~/Library/Application Support/EAIP_Viewer/")
    print("    缓存目录: ~/Library/Caches/EAIP_Viewer/")
    print("    日志目录: ~/Library/Logs/EAIP_Viewer/")

    print("  ✓ App Bundle 组织完成\n")


def create_dmg():
    """创建 DMG 磁盘映像"""
    print("[4/6] 创建 DMG 磁盘映像...")

    dist_app = DIST_DIR / f"{APP_DISPLAY_NAME}.app"
    dmg_name = f"{APP_NAME}_v{VERSION}_macOS_{ARCH}"
    dmg_path = DIST_DIR / f"{dmg_name}.dmg"

    # 删除已存在的 DMG
    if dmg_path.exists():
        dmg_path.unlink()

    # 创建临时 DMG 目录
    dmg_dir = BUILD_DIR / "dmg"
    if dmg_dir.exists():
        shutil.rmtree(dmg_dir)
    dmg_dir.mkdir(parents=True)

    # 复制 .app 到临时目录
    shutil.copytree(dist_app, dmg_dir / f"{APP_DISPLAY_NAME}.app")

    # 创建 Applications 软链接
    os.symlink("/Applications", dmg_dir / "Applications")

    # 创建使用说明
    readme_content = f"""EAIP Viewer {VERSION}

安装方法：
1. 将 "{APP_DISPLAY_NAME}.app" 拖到 "Applications" 文件夹
2. 首次运行时，右键点击应用，选择"打开"
3. 如果提示安全警告，在"系统偏好设置 > 安全性与隐私"中允许运行

系统要求：
- macOS 11 Big Sur 或更高版本
- 架构: {ARCH}

问题反馈：
https://github.com/your-repo/eaip-viewer/issues
"""
    (dmg_dir / "README.txt").write_text(readme_content)

    # 使用 hdiutil 创建 DMG
    print("  - 创建 DMG...")
    result = subprocess.run(
        [
            "hdiutil",
            "create",
            "-volname",
            f"{APP_DISPLAY_NAME} {VERSION}",
            "-srcfolder",
            str(dmg_dir),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  ✗ DMG 创建失败: {result.stderr}")
        sys.exit(1)

    size_mb = dmg_path.stat().st_size / (1024 * 1024)
    print(f"  - DMG 文件: {dmg_path}")
    print(f"  - 大小: {size_mb:.1f} MB")
    print("  ✓ DMG 创建完成\n")


def sign_app(skip_signing=True):
    """代码签名（可选）"""
    print("[5/6] 代码签名...")

    if skip_signing:
        print("  - 跳过代码签名（需要 Apple Developer 账号）")
        print("  - 用户首次运行时需要右键打开")
        print("  ✓ 跳过签名\n")
        return

    # 如果有开发者证书，可以进行签名
    # codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "EAIP Viewer.app"
    dist_app = DIST_DIR / f"{APP_DISPLAY_NAME}.app"

    result = subprocess.run(
        [
            "codesign",
            "--deep",
            "--force",
            "--verify",
            "--verbose",
            "--sign",
            "-",  # Ad-hoc 签名
            str(dist_app),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("  ✓ Ad-hoc 签名完成\n")
    else:
        print(f"  ! 签名失败（非致命）: {result.stderr}\n")


def create_checksums():
    """创建校验和文件"""
    print("[6/6] 创建校验和...")

    dmg_name = f"{APP_NAME}_v{VERSION}_macOS_{ARCH}"
    dmg_path = DIST_DIR / f"{dmg_name}.dmg"

    if not dmg_path.exists():
        print("  ✗ DMG 文件不存在")
        return

    # SHA256
    result = subprocess.run(
        ["shasum", "-a", "256", str(dmg_path)], capture_output=True, text=True
    )

    if result.returncode == 0:
        checksum = result.stdout.split()[0]
        checksum_file = DIST_DIR / f"{dmg_name}.sha256"
        checksum_file.write_text(f"{checksum}  {dmg_path.name}\n")
        print(f"  - SHA256: {checksum}")
        print(f"  - 校验和文件: {checksum_file.name}")

    print("  ✓ 校验和创建完成\n")


def main():
    """主构建流程"""
    print("=" * 60)
    print(f"  EAIP Viewer {VERSION} - Nuitka 构建脚本 (macOS {ARCH})")
    print("=" * 60)
    print()

    # 检查平台
    if sys.platform != "darwin":
        print("✗ 错误: 此脚本只能在 macOS 上运行")
        sys.exit(1)

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
        organize_app_bundle()
        create_dmg()
        sign_app(skip_signing=True)  # 默认跳过签名
        create_checksums()

        print("=" * 60)
        print("  ✓ 构建完成!")
        print("=" * 60)
        print(f"\n发布文件: dist/{APP_NAME}_v{VERSION}_macOS_{ARCH}.dmg")
        print(f"测试运行: open dist/{APP_DISPLAY_NAME}.app\n")

        print("提示：")
        print("  - 首次运行需要右键点击应用，选择'打开'")
        print("  - 或在系统偏好设置中允许运行")
        print("  - 如需分发，建议进行代码签名和公证\n")

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
