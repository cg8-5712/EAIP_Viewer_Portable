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
        console.log("==================== 加载机场航图数据 ====================")
        console.log("[ChartViewer] 机场代码:", airportCode)
        console.log("[ChartViewer] 机场名称:", airportName)

        allCharts = appController.dataManager.loadChartsForAirport(airportCode, "")

        console.log("[ChartViewer] 获取到航图数量:", allCharts.length)

        if (allCharts.length > 0) {
            console.log("[ChartViewer] 第一个航图示例:", JSON.stringify(allCharts[0], null, 2))
        }

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
        console.log("[ChartViewer] 分类列表:", JSON.stringify(categories))

        // 更新分类列表
        categoryList.updateCategories(categories)
        console.log("[ChartViewer] 分类列表已更新")
        console.log("==========================================================")
    }

    // 根据分类过滤航图
    function filterChartsByCategory(category) {
        console.log("[ChartViewer] 过滤分类:", category)
        var filtered = []
        for (var i = 0; i < allCharts.length; i++) {
            if (allCharts[i].sort === category) {
                filtered.push(allCharts[i])
            }
        }
        console.log("[ChartViewer] 过滤后航图数量:", filtered.length)
        if (filtered.length > 0) {
            console.log("[ChartViewer] 第一个过滤航图:", JSON.stringify(filtered[0], null, 2))
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

            onChartSelected: function(chartPath) {
                console.log("==================== 选择航图 ====================")
                console.log("[ChartViewer] 航图路径:", chartPath)
                console.log("[ChartViewer] 路径类型:", typeof chartPath)
                console.log("[ChartViewer] 路径长度:", chartPath ? chartPath.length : 0)
                console.log("[ChartViewer] 调用 pdfViewer.loadChart()")
                pdfViewer.loadChart(chartPath)
                console.log("================================================")
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
