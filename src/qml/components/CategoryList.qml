// CategoryList.qml - 航图分类列表组件
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../styles"

Rectangle {
    id: categoryList

    signal categorySelected(string category)

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    color: theme.cardBackground

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

        // 标题
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: "transparent"

            Text {
                text: "分类"
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

        // 分类列表
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            model: ListModel {
                ListElement { code: "AD"; name: "机场" }
                ListElement { code: "SID"; name: "离场" }
                ListElement { code: "STAR"; name: "进场" }
                ListElement { code: "APP"; name: "进近" }
            }

            delegate: ItemDelegate {
                width: ListView.view.width
                height: 60

                background: Rectangle {
                    color: highlighted ? theme.selected : (hovered ? theme.hover : "transparent")

                    // 选中指示器
                    Rectangle {
                        visible: highlighted
                        anchors.left: parent.left
                        width: 4
                        height: parent.height
                        color: theme.accent
                    }
                }

                contentItem: ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 4

                    Text {
                        text: model.code
                        font.pixelSize: style.fontSizeMedium
                        font.bold: true
                        color: highlighted ? theme.accent : theme.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: model.name
                        font.pixelSize: style.fontSizeSmall
                        color: theme.textSecondary
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }

                onClicked: {
                    ListView.view.currentIndex = index
                    categorySelected(model.code)
                }
            }

            highlight: Rectangle {
                color: theme.selected
            }
        }
    }
}
