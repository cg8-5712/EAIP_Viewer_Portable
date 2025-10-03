// PdfViewer.qml - PDF 查看器组件
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../styles"

Rectangle {
    id: pdfViewer

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    color: theme.background

    // 属性
    property string currentPdfPath: ""
    property real zoomLevel: 1.0

    // 函数
    function loadChart(path) {
        currentPdfPath = path
        console.log("加载 PDF:", path)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 工具栏
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: theme.cardBackground

            RowLayout {
                anchors.fill: parent
                anchors.margins: style.spacingSmall
                spacing: style.spacingSmall

                Item { Layout.fillWidth: true }

                // 缩放控件
                Button {
                    text: "🔍 放大"
                    flat: true
                    onClicked: {
                        zoomLevel = Math.min(5.0, zoomLevel * 1.25)
                    }
                }

                Text {
                    text: Math.round(zoomLevel * 100) + "%"
                    font.pixelSize: style.fontSizeNormal
                    color: theme.textPrimary
                    Layout.preferredWidth: 60
                    horizontalAlignment: Text.AlignHCenter
                }

                Button {
                    text: "缩小"
                    flat: true
                    onClicked: {
                        zoomLevel = Math.max(0.1, zoomLevel / 1.25)
                    }
                }

                Button {
                    text: "适应"
                    flat: true
                    onClicked: {
                        zoomLevel = 1.0
                    }
                }

                Rectangle {
                    width: 1
                    height: parent.height * 0.6
                    color: theme.divider
                }

                // 旋转按钮
                Button {
                    text: "↻ 旋转"
                    flat: true
                    onClicked: {
                        console.log("旋转 PDF")
                    }
                }

                Item { Layout.fillWidth: true }
            }

            // 底部分隔线
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: theme.divider
            }
        }

        // PDF 显示区域
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: theme.isDark ? "#1A1A1A" : "#E0E0E0"

            ScrollView {
                anchors.fill: parent
                clip: true

                // PDF 内容占位符
                Rectangle {
                    width: Math.max(pdfViewer.width - 40, 600 * zoomLevel)
                    height: Math.max(pdfViewer.height - 40, 800 * zoomLevel)
                    color: "white"
                    anchors.centerIn: parent

                    // 占位内容
                    Column {
                        anchors.centerIn: parent
                        spacing: style.spacingNormal

                        Text {
                            text: "📄"
                            font.pixelSize: 72
                            color: theme.textSecondary
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        Text {
                            text: currentPdfPath || "未加载 PDF"
                            font.pixelSize: style.fontSizeMedium
                            color: theme.textSecondary
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Text {
                            text: "缩放: " + Math.round(zoomLevel * 100) + "%"
                            font.pixelSize: style.fontSizeSmall
                            color: theme.textSecondary
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }
                }
            }
        }
    }
}
