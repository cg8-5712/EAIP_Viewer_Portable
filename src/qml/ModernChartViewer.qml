// ModernChartViewer.qml - 现代化航图查看器页面
// 使用全新的PDF查看器组件
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
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

    // 当前选中的航图
    property string currentChartPath: ""
    property string currentChartName: ""

    // 页面加载时获取数据
    Component.onCompleted: {
        if (airportCode) {
            loadAirportCharts()
        }
    }

    // 加载机场航图数据
    function loadAirportCharts() {
        console.log("[ModernChartViewer] 加载机场航图:", airportCode)

        allCharts = appController.dataManager.loadChartsForAirport(airportCode, "")
        console.log("[ModernChartViewer] 航图数量:", allCharts.length)

        // 提取分类
        let categorySet = new Set()
        for (let i = 0; i < allCharts.length; i++) {
            if (allCharts[i].sort) {
                categorySet.add(allCharts[i].sort)
            }
        }

        categories = Array.from(categorySet).sort()
        categoryList.updateCategories(categories)

        console.log("[ModernChartViewer] 分类:", categories)
    }

    // 根据分类过滤航图
    function filterChartsByCategory(category) {
        console.log("[ModernChartViewer] 过滤分类:", category)

        let filtered = []
        for (let i = 0; i < allCharts.length; i++) {
            if (allCharts[i].sort === category) {
                filtered.push(allCharts[i])
            }
        }

        chartList.updateCharts(filtered)
        console.log("[ModernChartViewer] 过滤结果:", filtered.length)
    }

    // 打开航图
    function openChart(chartPath, chartName) {
        console.log("[ModernChartViewer] 打开航图:", chartPath)
        currentChartPath = chartPath
        currentChartName = chartName || ""

        // 使用新的PDF查看器加载
        pdfViewer.loadPdf(chartPath)
    }

    background: Rectangle {
        color: theme.background
    }

    // 顶部工具栏
    header: ToolBar {
        height: style.toolbarHeight

        background: Rectangle {
            color: theme.cardBackground

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: theme.divider
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: style.spacingNormal
            spacing: style.spacingNormal

            // 返回按钮
            ToolButton {
                text: "← 返回"
                onClicked: backRequested()
            }

            Rectangle {
                width: 1
                height: parent.height * 0.6
                color: theme.divider
            }

            // 机场信息
            Column {
                spacing: 2

                Text {
                    text: airportCode + " - " + airportName
                    font.pixelSize: style.fontSizeMedium
                    font.bold: true
                    color: theme.textPrimary
                }

                Text {
                    text: currentChartName
                    font.pixelSize: style.fontSizeSmall
                    color: theme.textSecondary
                    visible: currentChartName !== ""
                }
            }

            Item { Layout.fillWidth: true }

            // 刷新按钮
            ToolButton {
                text: "🔄 刷新"
                onClicked: loadAirportCharts()
                ToolTip.visible: hovered
                ToolTip.text: "刷新航图列表"
            }
        }
    }

    // 主内容 - 三栏布局
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // 左侧：分类列表
        Rectangle {
            Layout.preferredWidth: 150
            Layout.fillHeight: true
            color: theme.cardBackground
            z: 10  // 显示在PDF上方

            CategoryList {
                id: categoryList
                anchors.fill: parent

                onCategorySelected: function(category) {
                    console.log("[ModernChartViewer] 选择分类:", category)
                    filterChartsByCategory(category)
                }
            }

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: theme.divider
            }
        }

        // 中间：航图列表
        Rectangle {
            Layout.preferredWidth: 250
            Layout.fillHeight: true
            color: theme.cardBackground
            z: 10  // 显示在PDF上方

            ChartList {
                id: chartList
                anchors.fill: parent

                onChartSelected: function(chartPath) {
                    // 查找航图名称
                    let chartName = ""
                    for (let i = 0; i < allCharts.length; i++) {
                        if (allCharts[i].path === chartPath) {
                            chartName = allCharts[i].name || allCharts[i].chart_name || ""
                            break
                        }
                    }

                    openChart(chartPath, chartName)
                }
            }

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: theme.divider
            }
        }

        // 右侧：PDF 查看器（设置在底层）
        ModernPdfViewer {
            id: pdfViewer
            Layout.fillWidth: true
            Layout.fillHeight: true
            z: 0  // PDF显示在最底层

            onDocumentLoaded: {
                console.log("[ModernChartViewer] PDF加载完成")
            }

            onDocumentError: function(error) {
                console.error("[ModernChartViewer] PDF加载错误:", error)
                errorDialog.errorMessage = error
                errorDialog.open()
            }

            onPageChanged: function(page) {
                console.log("[ModernChartViewer] 页面切换:", page + 1)
            }
        }
    }

    // 底部：Pin 栏
    footer: PinBar {
        id: pinBar
        height: style.pinBarHeight

        onChartClicked: function(filePath) {
            console.log("[ModernChartViewer] PinBar点击航图:", filePath)

            // 查找航图信息
            let chartInfo = appController.pinModel.getChartInfo(filePath)
            let chartName = chartInfo ? (chartInfo.name || chartInfo.chart_name || "") : ""

            openChart(filePath, chartName)
        }
    }

    // 错误对话框
    Dialog {
        id: errorDialog

        property string errorMessage: ""

        title: "加载错误"
        modal: true
        anchors.centerIn: parent

        contentItem: Column {
            spacing: style.spacingNormal
            padding: style.spacingNormal

            Text {
                text: "无法加载PDF文档"
                font.pixelSize: style.fontSizeMedium
                font.bold: true
                color: theme.textPrimary
            }

            Text {
                text: errorDialog.errorMessage
                font.pixelSize: style.fontSizeNormal
                color: theme.textSecondary
                wrapMode: Text.WordWrap
                width: 300
            }
        }

        standardButtons: Dialog.Ok
    }
}
