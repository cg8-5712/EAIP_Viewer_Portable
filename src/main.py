#!/usr/bin/env python3
"""
EAIP Viewer - Electronic Aeronautical Information Publication Viewer
主程序入口
"""

import os
import sys
from pathlib import Path

from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from controllers import AppController
from utils import Logger


def qt_message_handler(msg_type, context, message):
    """Qt 消息处理器 - 将 Qt 消息转发到日志系统"""
    import logging

    logger = logging.getLogger("Qt")

    if msg_type == QtMsgType.QtDebugMsg:
        logger.debug(message)
    elif msg_type == QtMsgType.QtInfoMsg:
        logger.info(message)
    elif msg_type == QtMsgType.QtWarningMsg:
        logger.warning(message)
    elif msg_type == QtMsgType.QtCriticalMsg:
        logger.critical(message)
    elif msg_type == QtMsgType.QtFatalMsg:
        logger.fatal(message)
        sys.exit(1)


def main():
    """主函数"""
    # 初始化日志系统
    Logger.setup(log_dir="logs", level=10)  # DEBUG=10
    logger = Logger.get_logger("Main")
    logger.info("应用程序启动")

    # 设置消息处理器
    qInstallMessageHandler(qt_message_handler)

    # 创建应用
    app = QGuiApplication(sys.argv)
    app.setApplicationName("EAIP Viewer")
    app.setOrganizationName("EAIP")
    app.setApplicationVersion("1.0.0")

    # 设置应用图标（如果存在）
    icon_path = Path(__file__).parent / "resources" / "images" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # 创建 QML 引擎
    engine = QQmlApplicationEngine()

    # 创建主控制器
    app_controller = AppController()

    # 将控制器暴露给 QML
    engine.rootContext().setContextProperty("appController", app_controller)

    # 加载 QML 文件
    qml_file = Path(__file__).parent / "qml" / "main.qml"
    if not qml_file.exists():
        print(f"错误: QML 文件不存在: {qml_file}")
        sys.exit(1)

    engine.load(QUrl.fromLocalFile(str(qml_file)))

    # 检查是否成功加载
    if not engine.rootObjects():
        print("错误: 无法加载 QML 文件")
        sys.exit(1)

    # 初始化应用
    app_controller.initialize()

    # 运行应用
    exit_code = app.exec()

    # 清理
    del engine
    del app

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
