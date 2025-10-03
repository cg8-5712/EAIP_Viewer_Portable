// ImportProgressDialog.qml - 数据导入进度对话框
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects
import "../styles"

Dialog {
    id: progressDialog
    modal: true
    closePolicy: Popup.NoAutoClose

    width: 600
    height: 400

    x: (parent.width - width) / 2
    y: (parent.height - height) / 2

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    // 属性
    property int currentStep: 0
    property int totalSteps: 6
    property int progress: 0
    property string stepName: ""
    property string taskDetail: ""
    property bool isCompleted: false
    property bool isFailed: false
    property string resultMessage: ""

    // 背景
    background: Rectangle {
        color: theme.cardBackground
        radius: style.cardRadius

        layer.enabled: true
        layer.effect: DropShadow {
            radius: 24
            samples: 48
            color: Qt.rgba(0, 0, 0, 0.3)
        }
    }

    // 标题
    title: "导入 EAIP 数据"

    header: Rectangle {
        height: 60
        color: theme.accent
        radius: style.cardRadius

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: style.cardRadius
            color: theme.accent
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: style.spacingNormal
            spacing: style.spacingNormal

            Text {
                text: "📦"
                font.pixelSize: 28
                color: "white"
            }

            Text {
                text: progressDialog.title
                font.pixelSize: style.fontSizeLarge || 20
                font.bold: true
                color: "white"
            }

            Item { Layout.fillWidth: true }
        }
    }

    // 内容
    contentItem: Item {
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: style.spacingLarge
            spacing: style.spacingLarge

            // 步骤指示器
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 80
                color: theme.isDark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.03)
                radius: style.cardRadius

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: style.spacingNormal
                    spacing: style.spacingSmall

                    // 步骤编号
                    Text {
                        text: progressDialog.isCompleted || progressDialog.isFailed
                              ? (progressDialog.isFailed ? "❌ 导入失败" : "✅ 导入完成")
                              : "步骤 " + progressDialog.currentStep + "/" + progressDialog.totalSteps
                        font.pixelSize: style.fontSizeSmall || 12
                        color: theme.textSecondary
                        font.bold: true
                    }

                    // 步骤名称
                    Text {
                        Layout.fillWidth: true
                        text: progressDialog.stepName
                        font.pixelSize: style.fontSizeLarge || 20
                        font.bold: true
                        color: theme.textPrimary
                        elide: Text.ElideRight
                    }
                }
            }

            // 进度条
            ColumnLayout {
                Layout.fillWidth: true
                spacing: style.spacingSmall
                visible: !progressDialog.isCompleted && !progressDialog.isFailed

                ProgressBar {
                    id: progressBar
                    Layout.fillWidth: true
                    value: progressDialog.progress / 100

                    background: Rectangle {
                        implicitHeight: 8
                        color: theme.isDark ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(0, 0, 0, 0.1)
                        radius: 4
                    }

                    contentItem: Item {
                        implicitHeight: 8

                        Rectangle {
                            width: progressBar.visualPosition * parent.width
                            height: parent.height
                            radius: 4
                            color: theme.accent

                            // 进度条动画
                            Behavior on width {
                                NumberAnimation {
                                    duration: 300
                                    easing.type: Easing.OutQuad
                                }
                            }
                        }
                    }
                }

                // 进度百分比
                Text {
                    Layout.alignment: Qt.AlignRight
                    text: progressDialog.progress + "%"
                    font.pixelSize: style.fontSizeMedium || 16
                    color: theme.accent
                    font.bold: true
                }
            }

            // 任务详情区域
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: theme.isDark ? Qt.rgba(0, 0, 0, 0.2) : Qt.rgba(0, 0, 0, 0.05)
                radius: style.cardRadius

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: style.spacingNormal
                    clip: true

                    ColumnLayout {
                        width: parent.width
                        spacing: style.spacingSmall

                        // 当前任务详情
                        Text {
                            Layout.fillWidth: true
                            text: progressDialog.taskDetail || "准备中..."
                            font.pixelSize: style.fontSizeSmall || 12
                            color: theme.textSecondary
                            wrapMode: Text.WordWrap
                            lineHeight: 1.5
                        }

                        Item { Layout.fillHeight: true }
                    }
                }
            }

            // 结果消息 (完成或失败时显示)
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: resultText.implicitHeight + style.spacingNormal * 2
                visible: progressDialog.isCompleted || progressDialog.isFailed
                color: progressDialog.isFailed
                       ? Qt.rgba(1, 0, 0, 0.1)
                       : Qt.rgba(0, 1, 0, 0.1)
                radius: style.cardRadius
                border.width: 2
                border.color: progressDialog.isFailed
                             ? Qt.rgba(1, 0, 0, 0.3)
                             : Qt.rgba(0, 1, 0, 0.3)

                Text {
                    id: resultText
                    anchors.fill: parent
                    anchors.margins: style.spacingNormal
                    text: progressDialog.resultMessage
                    font.pixelSize: style.fontSizeMedium || 16
                    color: theme.textPrimary
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    // 底部按钮
    footer: Rectangle {
        height: 60
        color: "transparent"

        RowLayout {
            anchors.fill: parent
            anchors.margins: style.spacingNormal
            spacing: style.spacingNormal

            Item { Layout.fillWidth: true }

            // 关闭按钮 (仅在完成或失败时显示)
            Button {
                visible: progressDialog.isCompleted || progressDialog.isFailed
                text: "关闭"
                font.pixelSize: style.fontSizeMedium || 16

                background: Rectangle {
                    implicitWidth: 100
                    implicitHeight: 40
                    color: parent.down ? Qt.darker(theme.accent, 1.2) : theme.accent
                    radius: style.cardRadius
                }

                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    progressDialog.close()
                    progressDialog.resetProgress()
                }
            }
        }
    }

    // 重置进度
    function resetProgress() {
        currentStep = 0
        progress = 0
        stepName = ""
        taskDetail = ""
        isCompleted = false
        isFailed = false
        resultMessage = ""
    }

    // 更新进度
    function updateProgress(step, total, percent, name, detail) {
        currentStep = step
        totalSteps = total
        progress = percent
        stepName = name
        taskDetail = detail
    }

    // 显示完成
    function showCompleted(message) {
        isCompleted = true
        isFailed = false
        resultMessage = message
    }

    // 显示失败
    function showFailed(message) {
        isCompleted = false
        isFailed = true
        resultMessage = message
    }
}
