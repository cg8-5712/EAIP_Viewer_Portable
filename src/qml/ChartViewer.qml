// ChartViewer.qml - 航图查看器页面
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "styles"
import "components"

Page {
    id: chartViewerPage

    // 属性
    property string airportCode: "ZBAA"
    property string airportName: "北京首都国际机场"

    // 信号
    signal backRequested()

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    background: Rectangle {
        color: theme.background
    }

    // 顶部工具栏
    header: ToolBar {
        height: style.toolbarHeight
        background: Rectangle {
            color: theme.cardBackground
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: style.spacingNormal
            spacing: style.spacingNormal

            // 返回按钮
            Button {
                text: "← 返回"
                flat: true
                onClicked: backRequested()
            }

            // 机场信息
            Text {
                text: airportCode + " - " + airportName
                font.pixelSize: style.fontSizeMedium
                font.bold: true
                color: theme.textPrimary
            }

            Item { Layout.fillWidth: true }

            // 搜索按钮
            Button {
                text: "🔍 搜索"
                flat: true
            }

            // 设置按钮
            Button {
                text: "⚙ 设置"
                flat: true
            }
        }
    }

    // 主内容 - 三栏布局
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // 左侧：分类列表
        CategoryList {
            id: categoryList
            Layout.preferredWidth: 150
            Layout.fillHeight: true

            onCategorySelected: {
                chartList.currentCategory = category
            }
        }

        // 中间：航图列表
        ChartList {
            id: chartList
            Layout.preferredWidth: 250
            Layout.fillHeight: true

            onChartSelected: {
                pdfViewer.loadChart(chartPath)
            }
        }

        // 右侧：PDF 查看器
        PdfViewer {
            id: pdfViewer
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    // 底部：Pin 栏
    footer: PinBar {
        id: pinBar
        height: style.pinBarHeight
    }
}
