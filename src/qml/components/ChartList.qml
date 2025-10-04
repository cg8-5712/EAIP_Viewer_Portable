// ChartList.qml - 航图列表组件
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../styles"

Rectangle {
    id: chartList

    property string currentCategory: ""
    property string airportCode: ""

    signal chartSelected(string chartPath)

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    color: theme.background

    // 航图数据模型
    ListModel {
        id: chartModel
    }

    // 更新航图列表
    function updateCharts(charts) {
        console.log("==================== 更新航图列表 ====================")
        console.log("[ChartList] 接收到航图数量:", charts.length)

        chartModel.clear()
        for (var i = 0; i < charts.length; i++) {
            var chart = charts[i]
            console.log("[ChartList] 添加航图", i, ":", {
                id: chart.id,
                code: chart.code,
                name: chart.name,
                path: chart.path,
                sort: chart.sort
            })

            chartModel.append({
                chartId: chart.id || "",
                code: chart.code || "",
                name: chart.name || "",
                path: chart.path || "",
                sort: chart.sort || ""
            })
        }

        console.log("[ChartList] 航图列表模型数量:", chartModel.count)
        console.log("===================================================")
    }

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
            id: chartListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: style.spacingSmall

            model: chartModel

            delegate: Rectangle {
                width: chartListView.width
                height: 80
                color: ListView.isCurrentItem ? theme.selected : (hovered ? theme.hover : "transparent")

                property bool hovered: false

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor

                    onEntered: parent.hovered = true
                    onExited: parent.hovered = false

                    onClicked: {
                        console.log("==================== 点击航图项 ====================")
                        console.log("[ChartList] 索引:", index)
                        console.log("[ChartList] 航图 ID:", model.chartId)
                        console.log("[ChartList] 航图代码:", model.code)
                        console.log("[ChartList] 航图名称:", model.name)
                        console.log("[ChartList] 航图路径:", model.path)
                        console.log("[ChartList] 航图分类:", model.sort)

                        chartListView.currentIndex = index

                        console.log("[ChartList] 发送 chartSelected 信号，路径:", model.path)
                        // 发送完整的航图路径
                        chartSelected(model.path)
                        console.log("===================================================")
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
                            text: model.code || model.name
                            font.pixelSize: style.fontSizeMedium
                            font.bold: true
                            color: theme.textPrimary
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        Text {
                            text: model.name
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
