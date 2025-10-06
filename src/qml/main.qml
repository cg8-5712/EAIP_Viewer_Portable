// main.qml - 主窗口
import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import "styles"

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 600
    title: "EAIP Viewer"

    // 主题管理
    ThemeManager {
        id: theme
    }

    // 样式
    AppStyle {
        id: style
    }

    // 背景色
    color: theme.background

    // 当前页面
    property string currentView: "splash"  // "splash", "airportList", "chartViewer"

    // StackView 用于页面切换
    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: splashScreenComponent

        // 页面切换动画
        pushEnter: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 0
                to: 1
                duration: style.animationMedium
            }
            PropertyAnimation {
                property: "x"
                from: mainWindow.width * 0.3
                to: 0
                duration: style.animationMedium
                easing.type: Easing.OutCubic
            }
        }

        pushExit: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 1
                to: 0
                duration: style.animationMedium
            }
        }

        popEnter: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 0
                to: 1
                duration: style.animationMedium
            }
        }

        popExit: Transition {
            PropertyAnimation {
                property: "opacity"
                from: 1
                to: 0
                duration: style.animationMedium
            }
            PropertyAnimation {
                property: "x"
                from: 0
                to: mainWindow.width * 0.3
                duration: style.animationMedium
                easing.type: Easing.InCubic
            }
        }
    }

    // 启动画面组件
    Component {
        id: splashScreenComponent
        SplashScreen {
            onLoadingComplete: {
                // 加载完成，切换到机场列表
                currentView = "airportList"
                stackView.replace(airportListComponent)
            }
        }
    }

    // 机场列表组件
    Component {
        id: airportListComponent
        AirportList {
            onAirportSelected: {
                // 选中机场，切换到航图查看器
                currentView = "chartViewer"
                stackView.push(chartViewerComponent, {
                    "airportCode": airportCode,
                    "airportName": airportName
                })
            }
        }
    }

    // 航图查看器组件
    Component {
        id: chartViewerComponent
        ModernChartViewer {
            onBackRequested: {
                // 返回机场列表
                currentView = "airportList"
                stackView.pop()
            }
        }
    }

    // 全局快捷键
    Shortcut {
        sequence: "Ctrl+Q"
        onActivated: Qt.quit()
    }

    Shortcut {
        sequence: "F11"
        onActivated: {
            if (mainWindow.visibility === Window.FullScreen) {
                mainWindow.showNormal()
            } else {
                mainWindow.showFullScreen()
            }
        }
    }

    // 组件加载完成
    Component.onCompleted: {
        // 如果禁用启动画面，直接进入主界面
        // if (!appController.config.splashScreenEnabled) {
        //     currentView = "airportList"
        //     stackView.replace(airportListComponent)
        // }
    }
}
