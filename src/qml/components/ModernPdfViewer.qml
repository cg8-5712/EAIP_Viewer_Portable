// ModernPdfViewer.qml - 现代化PDF查看器组件
// 完全基于PDF格式，使用Qt PDF原生渲染
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Pdf
import "../styles"

Rectangle {
    id: root

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    color: theme.background

    // 公共属性
    property alias source: pdfDocument.source
    property int currentPage: 0
    property alias pageCount: pdfDocument.pageCount
    property real zoomFactor: 1.0

    // 信号
    signal documentLoaded()
    signal documentError(string error)
    signal pageChanged(int page)

    // PDF文档对象
    PdfDocument {
        id: pdfDocument

        onStatusChanged: {
            if (status === PdfDocument.Ready) {
                console.log("[ModernPdfViewer] PDF加载完成, 页数:", pageCount)
                root.documentLoaded()
                // 自动适应窗口
                zoomToFit()
            } else if (status === PdfDocument.Error) {
                console.error("[ModernPdfViewer] PDF加载失败:", error)
                root.documentError(error)
            }
        }

        onPasswordRequired: {
            console.warn("[ModernPdfViewer] PDF需要密码")
            passwordDialog.open()
        }
    }

    // 公共方法
    function loadPdf(filePath) {
        console.log("[ModernPdfViewer] 加载PDF:", filePath)

        // 规范化路径
        let normalizedPath = filePath.toString()

        // 转换Windows路径
        if (normalizedPath.indexOf('\\') !== -1) {
            normalizedPath = normalizedPath.replace(/\\/g, '/')
        }

        // 添加file:///前缀（如果需要）
        if (!normalizedPath.startsWith('file:///')) {
            // 移除可能存在的file://前缀
            normalizedPath = normalizedPath.replace(/^file:\/\//, '')
            normalizedPath = 'file:///' + normalizedPath
        }

        console.log("[ModernPdfViewer] 最终路径:", normalizedPath)
        pdfDocument.source = normalizedPath
    }

    function clearPdf() {
        pdfDocument.source = ""
    }

    function zoomIn() {
        zoomFactor = Math.min(5.0, zoomFactor * 1.25)
        pdfScrollView.renderScale = zoomFactor
        console.log("[ModernPdfViewer] 放大到:", Math.round(zoomFactor * 100) + "%")
    }

    function zoomOut() {
        zoomFactor = Math.max(0.1, zoomFactor / 1.25)
        pdfScrollView.renderScale = zoomFactor
        console.log("[ModernPdfViewer] 缩小到:", Math.round(zoomFactor * 100) + "%")
    }

    function zoomToFit() {
        if (pageCount === 0) return

        const pageSize = pdfDocument.pagePointSize(currentPage)
        const viewWidth = contentArea.width - 40
        const viewHeight = contentArea.height - 40

        const widthRatio = viewWidth / pageSize.width
        const heightRatio = viewHeight / pageSize.height

        zoomFactor = Math.min(widthRatio, heightRatio)
        pdfScrollView.renderScale = zoomFactor
        console.log("[ModernPdfViewer] 适应页面:", Math.round(zoomFactor * 100) + "%")
    }

    function zoomToWidth() {
        if (pageCount === 0) return

        const pageSize = pdfDocument.pagePointSize(currentPage)
        const viewWidth = contentArea.width - 40

        zoomFactor = viewWidth / pageSize.width
        pdfScrollView.renderScale = zoomFactor
        console.log("[ModernPdfViewer] 适应宽度:", Math.round(zoomFactor * 100) + "%")
    }

    function zoomActualSize() {
        zoomFactor = 1.0
        pdfScrollView.renderScale = 1.0
        console.log("[ModernPdfViewer] 实际大小: 100%")
    }

    function goToPage(pageNumber) {
        if (pageNumber >= 0 && pageNumber < pageCount) {
            currentPage = pageNumber
            root.pageChanged(pageNumber)
        }
    }

    function nextPage() {
        if (currentPage < pageCount - 1) {
            currentPage++
            root.pageChanged(currentPage)
        }
    }

    function previousPage() {
        if (currentPage > 0) {
            currentPage--
            root.pageChanged(currentPage)
        }
    }

    // 主布局
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 顶部工具栏
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: theme.cardBackground
            z: 10

            RowLayout {
                anchors.fill: parent
                anchors.margins: style.spacingSmall
                spacing: style.spacingSmall

                // 页面导航
                ToolButton {
                    text: "◀"
                    enabled: currentPage > 0
                    onClicked: previousPage()
                    ToolTip.visible: hovered
                    ToolTip.text: "上一页"
                }

                TextField {
                    id: pageInput
                    Layout.preferredWidth: 50
                    text: (currentPage + 1).toString()
                    horizontalAlignment: TextInput.AlignHCenter
                    validator: IntValidator { bottom: 1; top: pageCount }

                    onAccepted: {
                        const page = parseInt(text) - 1
                        if (page >= 0 && page < pageCount) {
                            goToPage(page)
                        }
                    }
                }

                Text {
                    text: "/ " + pageCount
                    color: theme.textSecondary
                    font.pixelSize: style.fontSizeNormal
                }

                ToolButton {
                    text: "▶"
                    enabled: currentPage < pageCount - 1
                    onClicked: nextPage()
                    ToolTip.visible: hovered
                    ToolTip.text: "下一页"
                }

                Rectangle {
                    width: 1
                    height: parent.height * 0.6
                    color: theme.divider
                }

                // 缩放控件
                ToolButton {
                    text: "+"
                    onClicked: zoomIn()
                    ToolTip.visible: hovered
                    ToolTip.text: "放大"
                }

                Text {
                    text: Math.round(zoomFactor * 100) + "%"
                    color: theme.textPrimary
                    font.pixelSize: style.fontSizeNormal
                    Layout.preferredWidth: 60
                    horizontalAlignment: Text.AlignHCenter
                }

                ToolButton {
                    text: "-"
                    onClicked: zoomOut()
                    ToolTip.visible: hovered
                    ToolTip.text: "缩小"
                }

                ToolButton {
                    text: "适应页面"
                    onClicked: zoomToFit()
                    ToolTip.visible: hovered
                    ToolTip.text: "适应窗口大小"
                }

                ToolButton {
                    text: "适应宽度"
                    onClicked: zoomToWidth()
                    ToolTip.visible: hovered
                    ToolTip.text: "适应窗口宽度"
                }

                ToolButton {
                    text: "100%"
                    onClicked: zoomActualSize()
                    ToolTip.visible: hovered
                    ToolTip.text: "实际大小"
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

        // PDF显示区域
        Rectangle {
            id: contentArea
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: theme.isDark ? "#1A1A1A" : "#E0E0E0"

            // 使用PdfScrollablePageView原生组件
            PdfScrollablePageView {
                id: pdfScrollView
                anchors.fill: parent
                anchors.margins: 10

                document: pdfDocument

                // 设置当前页
                Component.onCompleted: {
                    console.log("[PdfScrollablePageView] 组件初始化完成")
                }

                // 监听renderScale变化
                onRenderScaleChanged: {
                    console.log("[PdfScrollablePageView] renderScale变化:", renderScale)
                    // 同步zoomFactor
                    if (Math.abs(renderScale - zoomFactor) > 0.01) {
                        zoomFactor = renderScale
                    }
                }
            }

            // 加载指示器
            BusyIndicator {
                anchors.centerIn: parent
                running: pdfDocument.status === PdfDocument.Loading
                visible: running
                z: 10
            }

            // 空状态提示
            Column {
                anchors.centerIn: parent
                spacing: style.spacingNormal
                visible: pdfDocument.status === PdfDocument.Null
                z: 10

                Text {
                    text: "📄"
                    font.pixelSize: 72
                    color: theme.textSecondary
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Text {
                    text: "未加载PDF文档"
                    font.pixelSize: style.fontSizeMedium
                    color: theme.textSecondary
                }
            }

            // 错误提示
            Column {
                anchors.centerIn: parent
                spacing: style.spacingNormal
                visible: pdfDocument.status === PdfDocument.Error
                z: 10

                Text {
                    text: "⚠️"
                    font.pixelSize: 72
                    color: "#F44336"
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Text {
                    text: "无法加载PDF文档"
                    font.pixelSize: style.fontSizeMedium
                    color: "#F44336"
                }

                Text {
                    text: pdfDocument.error
                    font.pixelSize: style.fontSizeSmall
                    color: theme.textSecondary
                    wrapMode: Text.WordWrap
                    width: 400
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    // 密码对话框
    Dialog {
        id: passwordDialog
        title: "需要密码"
        modal: true
        anchors.centerIn: parent

        ColumnLayout {
            spacing: style.spacingNormal

            Text {
                text: "此PDF文档受密码保护，请输入密码："
                color: theme.textPrimary
            }

            TextField {
                id: passwordField
                Layout.preferredWidth: 250
                echoMode: TextInput.Password
                placeholderText: "密码"

                onAccepted: {
                    pdfDocument.password = text
                    passwordDialog.close()
                }
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: style.spacingSmall

                Button {
                    text: "取消"
                    onClicked: passwordDialog.close()
                }

                Button {
                    text: "确定"
                    highlighted: true
                    onClicked: {
                        pdfDocument.password = passwordField.text
                        passwordDialog.close()
                    }
                }
            }
        }
    }

    // 键盘快捷键
    Item {
        focus: true
        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_PageUp || event.key === Qt.Key_Up) {
                previousPage()
                event.accepted = true
            } else if (event.key === Qt.Key_PageDown || event.key === Qt.Key_Down) {
                nextPage()
                event.accepted = true
            } else if (event.key === Qt.Key_Home) {
                goToPage(0)
                event.accepted = true
            } else if (event.key === Qt.Key_End) {
                goToPage(pageCount - 1)
                event.accepted = true
            } else if (event.key === Qt.Key_Plus || event.key === Qt.Key_Equal) {
                if (event.modifiers & Qt.ControlModifier) {
                    zoomIn()
                    event.accepted = true
                }
            } else if (event.key === Qt.Key_Minus) {
                if (event.modifiers & Qt.ControlModifier) {
                    zoomOut()
                    event.accepted = true
                }
            } else if (event.key === Qt.Key_0) {
                if (event.modifiers & Qt.ControlModifier) {
                    zoomActualSize()
                    event.accepted = true
                }
            }
        }
    }

    // 鼠标滚轮缩放
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        propagateComposedEvents: true
        z: 5

        onWheel: function(wheel) {
            if (wheel.modifiers & Qt.ControlModifier) {
                if (wheel.angleDelta.y > 0) {
                    zoomIn()
                } else {
                    zoomOut()
                }
                wheel.accepted = true
            } else {
                wheel.accepted = false
            }
        }
    }

    // 监听currentPage变化，更新页面输入框
    onCurrentPageChanged: {
        pageInput.text = (currentPage + 1).toString()
    }
}
