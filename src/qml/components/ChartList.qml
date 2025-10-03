// ChartList.qml - 航图列表组件
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../styles"

Rectangle {
    id: chartList

    property string currentCategory: ""

    signal chartSelected(string chartPath)

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    color: theme.background

    // 分隔线
    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: theme.divider
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 标题栏
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: theme.cardBackground

            Text {
                text: "航图列表"
                font.pixelSize: style.fontSizeMedium
                font.bold: true
                color: theme.textPrimary
                anchors.centerIn: parent
            }

            // 底部分隔线
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: theme.divider
            }
        }

        // 航图列表
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: style.spacingSmall

            model: ListModel {
                ListElement { name: "AD 1.1"; description: "机场概况" }
                ListElement { name: "AD 1.2"; description: "机场数据" }
                ListElement { name: "AD 2.1"; description: "跑道数据" }
                ListElement { name: "AD 2.2"; description: "滑行道数据" }
            }

            delegate: Rectangle {
                width: ListView.view.width
                height: 80
                color: highlighted ? theme.selected : (hovered ? theme.hover : "transparent")

                property bool hovered: false

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor

                    onEntered: parent.hovered = true
                    onExited: parent.hovered = false

                    onClicked: {
                        ListView.view.currentIndex = index
                        chartSelected("/path/to/" + model.name + ".pdf")
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: style.spacingMedium
                    spacing: style.spacingSmall

                    // 缩略图占位符
                    Rectangle {
                        Layout.preferredWidth: 50
                        Layout.preferredHeight: 60
                        color: theme.divider
                        radius: style.radiusSmall

                        Text {
                            anchors.centerIn: parent
                            text: "📄"
                            font.pixelSize: 24
                        }
                    }

                    // 文字信息
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: model.name
                            font.pixelSize: style.fontSizeMedium
                            font.bold: true
                            color: theme.textPrimary
                        }

                        Text {
                            text: model.description
                            font.pixelSize: style.fontSizeSmall
                            color: theme.textSecondary
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    // Pin 按钮
                    Button {
                        text: "📌"
                        flat: true
                        implicitWidth: 40
                        implicitHeight: 40
                        onClicked: {
                            console.log("Pin:", model.name)
                        }
                    }
                }

                // 底部分隔线
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: theme.divider
                    opacity: 0.3
                }
            }
        }
    }
}
