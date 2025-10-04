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
    property string renderedImagePath: ""
    property bool autoFitOnLoad: true  // 首次加载时自动适应

    // 计算适应窗口的缩放比例
    function calculateFitZoom() {
        if (!pdfPageImage.sourceSize.width || !pdfPageImage.sourceSize.height) {
            console.log("[PdfViewer] 无法计算适应缩放：PDF尺寸无效")
            return 1.0
        }

        // 获取显示区域尺寸（减去一些边距）
        var viewWidth = pdfScrollView.width - 40
        var viewHeight = pdfScrollView.height - 40

        // PDF原始尺寸（考虑当前zoom）
        var pdfWidth = pdfPageImage.sourceSize.width / zoomLevel
        var pdfHeight = pdfPageImage.sourceSize.height / zoomLevel

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
        console.log("[PdfViewer] 接收路径:", path)
        console.log("[PdfViewer] 路径类型:", typeof path)
        console.log("[PdfViewer] 路径长度:", path ? path.length : 0)

        currentPdfPath = path
        console.log("[PdfViewer] currentPdfPath 已设置:", currentPdfPath)

        zoomLevel = 1.0
        autoFitOnLoad = true  // 重置自动适应标志
        console.log("[PdfViewer] zoomLevel 已重置为:", zoomLevel)

        // 使用 Python 后端渲染 PDF
        if (path && appController && appController.pdfHandler) {
            console.log("[PdfViewer] appController 存在:", !!appController)
            console.log("[PdfViewer] pdfHandler 存在:", !!appController.pdfHandler)
            console.log("[PdfViewer] 调用 renderPdfToImage，路径:", path, "缩放:", zoomLevel)

            renderedImagePath = appController.pdfHandler.renderPdfToImage(path, zoomLevel)

            console.log("[PdfViewer] 渲染完成，图片路径:", renderedImagePath)
            console.log("[PdfViewer] 图片路径类型:", typeof renderedImagePath)
            console.log("[PdfViewer] 图片路径长度:", renderedImagePath ? renderedImagePath.length : 0)
        } else {
            console.error("[PdfViewer] 无法渲染 PDF:")
            console.error("  - path:", path)
            console.error("  - appController:", !!appController)
            console.error("  - pdfHandler:", appController ? !!appController.pdfHandler : "N/A")
        }
        console.log("==========================================================")
    }

    // 监听缩放变化
    onZoomLevelChanged: {
        console.log("[PdfViewer] 缩放级别变化:", zoomLevel)
        if (currentPdfPath && appController && appController.pdfHandler) {
            console.log("[PdfViewer] 重新渲染 PDF，缩放:", zoomLevel)
            renderedImagePath = appController.pdfHandler.renderPdfToImage(currentPdfPath, zoomLevel)
            console.log("[PdfViewer] 重新渲染完成，图片路径:", renderedImagePath)
        }
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
                        var fitZoom = calculateFitZoom()
                        if (fitZoom > 0) {
                            zoomLevel = fitZoom
                            console.log("[PdfViewer] 设置适应缩放:", fitZoom)
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
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: theme.isDark ? "#1A1A1A" : "#E0E0E0"

            ScrollView {
                id: pdfScrollView
                anchors.fill: parent
                clip: true
                contentWidth: pdfPageImage.width
                contentHeight: pdfPageImage.height

                // PDF 页面显示
                Item {
                    width: Math.max(pdfPageImage.width, parent.width)
                    height: Math.max(pdfPageImage.height, parent.height)

                    Image {
                        id: pdfPageImage
                        source: renderedImagePath ? "file:///" + renderedImagePath : ""
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        cache: false
                        anchors.centerIn: renderedImagePath ? parent : undefined

                        // 图片加载完成后自动适应
                        onStatusChanged: {
                            if (status === Image.Ready && autoFitOnLoad && zoomLevel === 1.0) {
                                console.log("[PdfViewer] 图片加载完成，自动适应窗口")
                                autoFitOnLoad = false  // 防止重复触发
                                Qt.callLater(function() {
                                    var fitZoom = calculateFitZoom()
                                    if (fitZoom > 0 && fitZoom !== 1.0) {
                                        console.log("[PdfViewer] 自动设置适应缩放:", fitZoom)
                                        zoomLevel = fitZoom
                                    }
                                })
                            }
                        }

                        // 占位内容（PDF 未加载时）
                        Column {
                            visible: !renderedImagePath
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
        }
    }
}
