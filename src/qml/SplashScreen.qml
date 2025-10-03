// SplashScreen.qml - 启动画面
import QtQuick 2.15
import QtQuick.Controls 2.15
import "styles"

Rectangle {
    id: splashScreen

    // 信号
    signal loadingComplete()

    // 属性
    property int progress: 0
    property string statusText: "初始化..."
    property int minDisplayTime: 1500  // 最小显示时间（毫秒）

    // 渐变背景
    gradient: Gradient {
        GradientStop { position: 0.0; color: theme.isDark ? "#1A237E" : "#1976D2" }
        GradientStop { position: 1.0; color: theme.isDark ? "#0D47A1" : "#42A5F5" }
    }

    // 主题
    ThemeManager {
        id: theme
    }

    // 样式
    AppStyle {
        id: style
    }

    // 主容器
    Column {
        anchors.centerIn: parent
        spacing: style.spacingXLarge

        // Logo 容器
        Rectangle {
            width: 180
            height: 180
            radius: style.radiusLarge
            color: Qt.rgba(255, 255, 255, 0.1)
            border.width: 2
            border.color: Qt.rgba(255, 255, 255, 0.3)
            anchors.horizontalCenter: parent.horizontalCenter

            // Logo 文字
            Column {
                anchors.centerIn: parent
                spacing: style.spacingSmall

                Text {
                    text: "✈"
                    font.pixelSize: 72
                    color: "#FFFFFF"
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Text {
                    text: "航图"
                    font.pixelSize: style.fontSizeLarge
                    font.bold: true
                    color: "#FFFFFF"
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }

        // 应用名称
        Column {
            spacing: style.spacingSmall
            anchors.horizontalCenter: parent.horizontalCenter

            Text {
                text: "EAIP Viewer"
                font.pixelSize: style.fontSizeXLarge
                font.bold: true
                color: "#FFFFFF"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "Electronic Aeronautical\nInformation Publication Viewer"
                font.pixelSize: style.fontSizeSmall
                color: Qt.rgba(255, 255, 255, 0.8)
                horizontalAlignment: Text.AlignHCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "v1.0.0"
                font.pixelSize: style.fontSizeSmall
                color: Qt.rgba(255, 255, 255, 0.6)
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        // 进度条
        Column {
            spacing: style.spacingSmall
            width: 300
            anchors.horizontalCenter: parent.horizontalCenter

            // 进度条背景
            Rectangle {
                width: parent.width
                height: 6
                radius: 3
                color: Qt.rgba(255, 255, 255, 0.2)

                // 进度条前景
                Rectangle {
                    width: parent.width * (progress / 100)
                    height: parent.height
                    radius: parent.radius
                    color: "#FFFFFF"

                    Behavior on width {
                        NumberAnimation {
                            duration: style.animationNormal
                            easing.type: Easing.InOutQuad
                        }
                    }
                }
            }

            // 状态文字
            Text {
                text: statusText + " " + progress + "%"
                font.pixelSize: style.fontSizeSmall
                color: Qt.rgba(255, 255, 255, 0.9)
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        // 底部信息
        Text {
            text: "Powered by Python & Qt6"
            font.pixelSize: style.fontSizeSmall
            color: Qt.rgba(255, 255, 255, 0.5)
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    // 淡入动画
    opacity: 0
    Component.onCompleted: {
        fadeIn.start()
        startLoading()
    }

    NumberAnimation {
        id: fadeIn
        target: splashScreen
        property: "opacity"
        from: 0
        to: 1
        duration: 500
        easing.type: Easing.InOutQuad
    }

    // 淡出动画
    NumberAnimation {
        id: fadeOut
        target: splashScreen
        property: "opacity"
        from: 1
        to: 0
        duration: 300
        easing.type: Easing.InOutQuad
        onStopped: {
            loadingComplete()
        }
    }

    // 计时器：确保最小显示时间
    property int elapsedTime: 0
    Timer {
        id: minDisplayTimer
        interval: 100
        repeat: true
        running: false
        onTriggered: {
            elapsedTime += interval
        }
    }

    // 模拟加载过程
    function startLoading() {
        minDisplayTimer.start()
        loadingSequence.start()
    }

    SequentialAnimation {
        id: loadingSequence

        // 初始化配置 (20%)
        ScriptAction {
            script: {
                statusText = "初始化配置..."
                progress = 20
            }
        }
        PauseAnimation { duration: 300 }

        // 加载主题/语言 (40%)
        ScriptAction {
            script: {
                statusText = "加载主题和语言..."
                progress = 40
            }
        }
        PauseAnimation { duration: 300 }

        // 初始化数据库 (60%)
        ScriptAction {
            script: {
                statusText = "初始化数据..."
                progress = 60
            }
        }
        PauseAnimation { duration: 300 }

        // 加载已保存数据 (80%)
        ScriptAction {
            script: {
                statusText = "加载数据..."
                progress = 80
            }
        }
        PauseAnimation { duration: 300 }

        // 预加载组件 (100%)
        ScriptAction {
            script: {
                statusText = "准备就绪"
                progress = 100
            }
        }
        PauseAnimation { duration: 200 }

        // 完成加载
        ScriptAction {
            script: {
                finishLoading()
            }
        }
    }

    function finishLoading() {
        // 确保至少显示了最小时间
        if (elapsedTime < minDisplayTime) {
            Qt.callLater(finishLoading)
        } else {
            minDisplayTimer.stop()
            fadeOut.start()
        }
    }
}
