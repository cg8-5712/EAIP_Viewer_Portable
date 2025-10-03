// PinBar.qml - Pin 栏组件
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects
import "../styles"

Rectangle {
    id: pinBar

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    // 毛玻璃背景效果
    color: Qt.rgba(theme.cardBackground.r, theme.cardBackground.g, theme.cardBackground.b, 0.95)

    // 顶部分隔线
    Rectangle {
        anchors.top: parent.top
        width: parent.width
        height: 1
        color: theme.divider
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: style.spacingSmall
        spacing: style.spacingSmall

        // 标题
        Text {
            text: "📌 固定航图"
            font.pixelSize: style.fontSizeNormal
            font.bold: true
            color: theme.textPrimary
            Layout.preferredWidth: 100
        }

        // 固定航图列表
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: ListView.Horizontal
            spacing: style.pinItemSpacing
            clip: true

            model: ListModel {
                ListElement { name: "AD 1.1" }
                ListElement { name: "SID 01" }
                ListElement { name: "STAR 19" }
            }

            delegate: Rectangle {
                width: style.pinItemSize
                height: style.pinItemSize
                radius: style.radiusSmall
                color: theme.cardBackground
                border.width: 2
                border.color: highlighted ? theme.accent : theme.divider

                property bool highlighted: false
                property bool hovered: false

                // 阴影
                layer.enabled: true
                layer.effect: DropShadow {
                    radius: style.shadowSmall
                    samples: 12
                    color: Qt.rgba(0, 0, 0, 0.2)
                    verticalOffset: 2
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor

                    onEntered: parent.hovered = true
                    onExited: parent.hovered = false

                    onClicked: {
                        parent.highlighted = !parent.highlighted
                        console.log("点击固定航图:", model.name)
                    }
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 4

                    // 缩略图占位符
                    Rectangle {
                        width: 50
                        height: 50
                        color: theme.background
                        radius: style.radiusSmall
                        anchors.horizontalCenter: parent.horizontalCenter

                        Text {
                            anchors.centerIn: parent
                            text: "📄"
                            font.pixelSize: 24
                        }
                    }

                    // 航图名称
                    Text {
                        text: model.name
                        font.pixelSize: style.fontSizeSmall
                        color: theme.textPrimary
                        elide: Text.ElideRight
                        width: style.pinItemSize - 8
                        horizontalAlignment: Text.AlignHCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                // 删除按钮
                Button {
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.margins: 4
                    width: 20
                    height: 20
                    text: "×"
                    visible: parent.hovered
                    background: Rectangle {
                        radius: 10
                        color: theme.error
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        console.log("删除固定航图:", model.name)
                    }
                }

                // 悬浮动画
                Behavior on scale {
                    NumberAnimation {
                        duration: style.animationFast
                        easing.type: Easing.OutQuad
                    }
                }

                scale: hovered ? 1.05 : 1.0
            }
        }

        // 添加按钮
        Button {
            Layout.preferredWidth: style.pinItemSize
            Layout.preferredHeight: style.pinItemSize
            flat: true

            background: Rectangle {
                radius: style.radiusSmall
                color: hovered ? theme.hover : "transparent"
                border.width: 2
                border.color: theme.divider
            }

            contentItem: Column {
                spacing: 4

                Text {
                    text: "+"
                    font.pixelSize: 36
                    color: theme.textSecondary
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Text {
                    text: "添加"
                    font.pixelSize: style.fontSizeSmall
                    color: theme.textSecondary
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }

            onClicked: {
                console.log("添加固定航图")
            }
        }

        // 最多10个提示
        Text {
            text: "(最多10个)"
            font.pixelSize: style.fontSizeSmall
            color: theme.textSecondary
            Layout.preferredWidth: 80
        }
    }
}
