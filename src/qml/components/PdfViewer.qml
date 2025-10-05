// PdfViewer.qml - PDF 查看器组件
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Pdf
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

    // 监听路径变化
    onCurrentPdfPathChanged: {
        console.log("[PdfViewer] currentPdfPath 变化:", currentPdfPath)
        if (currentPdfPath) {
            updatePdfSource()
        }
    }

    // 监听缩放变化
    onZoomLevelChanged: {
        console.log("[PdfViewer] 缩放变化:", zoomLevel)
    }

    // 更新 PDF 源
    function updatePdfSource() {
        if (!currentPdfPath) {
            console.log("[PdfViewer] 路径为空，清空 PDF 源")
            pdfDocument.source = ""
            return
        }

        // 标准化路径
        var path = currentPdfPath.toString()
        console.log("[PdfViewer] 原始路径:", path)

        // 如果已有 file:/// 前缀，直接使用
        if (path.startsWith("file:///")) {
            console.log("[PdfViewer] 已有 file:/// 前缀")
            pdfDocument.source = path
            return
        }

        // 转换反斜杠为正斜杠（Windows 路径）
        path = path.replace(/\\/g, "/")
        console.log("[PdfViewer] 转换后路径:", path)

        // 添加 file:/// 前缀
        var finalPath = "file:///" + path
        console.log("[PdfViewer] 最终路径:", finalPath)
        console.log("[PdfViewer] 设置 pdfDocument.source =", finalPath)
        pdfDocument.source = finalPath
    }

    // PDF 文档对象
    PdfDocument {
        id: pdfDocument

        onStatusChanged: {
            var currentStatus = pdfDocument.status
            console.log("[PdfViewer] PDF 状态变化:", currentStatus)
            console.log("[PdfViewer] 当前 source:", pdfDocument.source)

            if (currentStatus === PdfDocument.Ready) {
                console.log("[PdfViewer] PDF 加载完成，页数:", pdfDocument.pageCount)
                // 计算适应窗口的缩放
                if (pdfDocument.pageCount > 0) {
                    var pageSize = pdfDocument.pagePointSize(0)
                    console.log("[PdfViewer] PDF 页面尺寸:", pageSize.width, "x", pageSize.height)
                    var fitZoom = calculateFitZoom(pageSize.width, pageSize.height)
                    zoomLevel = fitZoom
                }
            } else if (currentStatus === PdfDocument.Error) {
                console.error("[PdfViewer] PDF 加载失败!")
                console.error("[PdfViewer] 错误信息:", pdfDocument.error)
                console.error("[PdfViewer] 文件路径:", pdfDocument.source)
            } else if (currentStatus === PdfDocument.Loading) {
                console.log("[PdfViewer] PDF 正在加载...")
            } else if (currentStatus === PdfDocument.Null) {
                console.log("[PdfViewer] PDF 文档为空")
            }
        }
    }

    // 计算适应窗口的缩放比例
    function calculateFitZoom(pdfWidth, pdfHeight) {
        if (!pdfWidth || !pdfHeight) {
            console.log("[PdfViewer] 无法计算适应缩放：PDF尺寸无效")
            return 1.0
        }

        // 获取显示区域尺寸（减去一些边距）
        var viewWidth = pdfViewContainer.width - 40
        var viewHeight = pdfViewContainer.height - 40

        // 计算宽度和高度的缩放比例
        var widthRatio = viewWidth / pdfWidth
        var heightRatio = viewHeight / pdfHeight

        // 取较小值，确保整个PDF都能显示
        var fitZoom = Math.min(widthRatio, heightRatio)

        console.log("[PdfViewer] 适应缩放计算:")
        console.log("  - 显示区域:", viewWidth, "x", viewHeight)
        console.log("  - PDF原始尺寸:", pdfWidth, "x", pdfHeight)
        console.log("  - 宽度比例:", widthRatio)
        console.log("  - 高度比例:", heightRatio)
        console.log("  - 适应缩放:", fitZoom)

        return fitZoom
    }

    // 函数
    function loadChart(path) {
        console.log("==================== PdfViewer.loadChart ====================")
        console.log("[PdfViewer] 加载 PDF:", path)
        currentPdfPath = path
        console.log("==========================================================")
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
                        console.log("[PdfViewer] 点击放大按钮")
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
                    text: "🔍 缩小"
                    flat: true
                    onClicked: {
                        console.log("[PdfViewer] 点击缩小按钮")
                        zoomLevel = Math.max(0.1, zoomLevel / 1.25)
                    }
                }

                Button {
                    text: "适应"
                    flat: true
                    onClicked: {
                        console.log("[PdfViewer] 点击适应按钮")
                        if (pdfDocument.status === PdfDocument.Ready && pdfDocument.pageCount > 0) {
                            var pageSize = pdfDocument.pagePointSize(0)
                            var fitZoom = calculateFitZoom(pageSize.width, pageSize.height)
                            if (fitZoom > 0) {
                                zoomLevel = fitZoom
                                console.log("[PdfViewer] 设置适应缩放:", fitZoom)
                            }
                        }
                    }
                }

                Button {
                    text: "原始大小"
                    flat: true
                    onClicked: {
                        console.log("[PdfViewer] 点击1:1按钮")
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
                        console.log("[PdfViewer] 点击旋转按钮")
                        // TODO: 实现旋转功能
                        console.log("[PdfViewer] 旋转功能待实现")
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
            id: pdfViewContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: theme.isDark ? "#1A1A1A" : "#E0E0E0"

            PdfScrollablePageView {
                id: pdfScrollView
                anchors.fill: parent
                anchors.margins: 10
                document: pdfDocument

                // 设置渲染缩放
                renderScale: zoomLevel

                Component.onCompleted: {
                    console.log("[PdfViewer] PdfScrollablePageView 初始化完成")
                }

                onRenderScaleChanged: {
                    console.log("[PdfViewer] renderScale 更新:", renderScale)
                }
            }

            // 占位内容（PDF 未加载时）
            Column {
                visible: pdfDocument.status !== PdfDocument.Ready
                anchors.centerIn: parent
                spacing: style.spacingNormal
                z: 10

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
                    wrapMode: Text.WordWrap
                    width: pdfViewer.width * 0.6
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
