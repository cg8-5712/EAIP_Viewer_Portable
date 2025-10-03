// ChartViewer.qml - 航图查看器页面
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "styles"
import "components"

Page {
    id: chartViewerPage

    // 属性
    property string airportCode: ""
    property string airportName: ""

    // 信号
    signal backRequested()

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    // 航图数据和分类
    property var allCharts: []
    property var categories: []

    // 页面加载时获取数据
    Component.onCompleted: {
        if (airportCode) {
            loadAirportCharts()
        }
    }

    // 加载机场航图数据
    function loadAirportCharts() {
        console.log("加载机场航图数据:", airportCode)
        allCharts = appController.dataManager.loadChartsForAirport(airportCode, "")
        console.log("获取到航图数量:", allCharts.length)

        // 提取唯一的分类
        var categorySet = new Set()
        for (var i = 0; i < allCharts.length; i++) {
            var chart = allCharts[i]
            if (chart.sort) {
                categorySet.add(chart.sort)
            }
        }

        // 转换为数组并排序
        categories = Array.from(categorySet).sort()
        console.log("分类列表:", categories)

        // 更新分类列表
        categoryList.updateCategories(categories)
    }

    // 根据分类过滤航图
    function filterChartsByCategory(category) {
        var filtered = []
        for (var i = 0; i < allCharts.length; i++) {
            if (allCharts[i].sort === category) {
                filtered.push(allCharts[i])
            }
        }
        chartList.updateCharts(filtered)
    }

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

            onCategorySelected: function(category) {
                console.log("选择分类:", category)
                filterChartsByCategory(category)
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
