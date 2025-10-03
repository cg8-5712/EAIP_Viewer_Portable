// AirportList.qml - 机场列表页面
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import Qt5Compat.GraphicalEffects
import "styles"
import "components"

Page {
    id: airportListPage

    signal airportSelected(string airportCode, string airportName)

    // 主题和样式
    ThemeManager { id: theme }
    AppStyle { id: style }

    // 导入进度对话框
    ImportProgressDialog {
        id: importProgressDialog
        parent: Overlay.overlay
    }

    // 文件选择对话框
    FileDialog {
        id: fileDialog
        title: "选择 EAIP 数据压缩包"
        nameFilters: ["ZIP files (*.zip)"]
        fileMode: FileDialog.OpenFile
        onAccepted: {
            var filePath = fileDialog.selectedFile.toString()
            // 移除 file:/// 前缀
            if (filePath.startsWith("file:///")) {
                filePath = filePath.substring(8)
            }
            console.log("选择的文件: " + filePath)
            appController.importData(filePath)
        }
    }

    // 机场数据模型
    ListModel {
        id: airportModel
    }

    // 连接数据管理器信号
    Connections {
        target: appController.dataManager

        function onDataImportStarted() {
            console.log("导入开始")
            importProgressDialog.resetProgress()
            importProgressDialog.open()
        }

        function onDataImportProgress(currentStep, totalSteps, progress, stepName, taskDetail) {
            console.log("导入进度:", currentStep, "/", totalSteps, "-", progress + "%", "-", stepName)
            importProgressDialog.updateProgress(currentStep, totalSteps, progress, stepName, taskDetail)
        }

        function onDataImportCompleted(success, message) {
            console.log("导入完成:", success, message)
            if (success) {
                importProgressDialog.showCompleted(message)
            } else {
                importProgressDialog.showFailed(message)
            }
        }

        function onAirportsLoaded(airports) {
            console.log("机场数据加载完成，机场数量:", airports.length)
            airportModel.clear()
            for (var i = 0; i < airports.length; i++) {
                airportModel.append({
                    code: airports[i].code,
                    nameZh: airports[i].name_zh,
                    nameEn: airports[i].name_en,
                    chartCount: airports[i].chart_count || 0
                })
            }
        }
    }

    // 页面加载时尝试加载已保存的数据
    Component.onCompleted: {
        var savedAirports = appController.dataManager.loadSavedAirports()
        if (savedAirports && savedAirports.length > 0) {
            console.log("加载保存的机场数据，数量:", savedAirports.length)
            for (var i = 0; i < savedAirports.length; i++) {
                airportModel.append({
                    code: savedAirports[i].code,
                    nameZh: savedAirports[i].name_zh,
                    nameEn: savedAirports[i].name_en,
                    chartCount: savedAirports[i].chart_count || 0
                })
            }
        }
    }

    background: Rectangle {
        color: theme.background
    }

    // 顶部工具栏
    header: ToolBar {
        height: style.toolbarHeight
        background: Rectangle {
            color: theme.cardBackground
            layer.enabled: true
            layer.effect: DropShadow {
                radius: style.shadowSmall
                samples: 16
                color: Qt.rgba(0, 0, 0, 0.15)
                verticalOffset: 2
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: style.spacingNormal
            anchors.rightMargin: style.spacingNormal
            spacing: style.spacingNormal

            // 应用标题
            Row {
                spacing: style.spacingSmall

                Text {
                    text: "✈"
                    font.pixelSize: style.fontSizeLarge
                    color: theme.accent
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: "EAIP Viewer"
                    font.pixelSize: style.fontSizeLarge
                    font.bold: true
                    color: theme.textPrimary
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Item { Layout.fillWidth: true }

            // 搜索按钮
            Button {
                text: "🔍 搜索"
                flat: true
                onClicked: searchField.visible = !searchField.visible
            }

            // 导入按钮
            Button {
                text: "📦 导入数据"
                flat: true
                highlighted: true
                onClicked: {
                    fileDialog.open()
                }
            }

            // 设置按钮
            Button {
                text: "⚙ 设置"
                flat: true
                onClicked: {
                    console.log("打开设置")
                }
            }
        }
    }

    // 主内容
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: style.spacingNormal
        spacing: style.spacingNormal

        // 标题和搜索框
        RowLayout {
            Layout.fillWidth: true
            spacing: style.spacingNormal

            Text {
                text: "机场列表"
                font.pixelSize: style.fontSizeLarge
                font.bold: true
                color: theme.textPrimary
            }

            Item { Layout.fillWidth: true }

            // 搜索框
            TextField {
                id: searchField
                Layout.preferredWidth: 300
                placeholderText: "搜索机场..."
                visible: false
            }
        }

        // 机场列表
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: airportListView
                spacing: style.spacingMedium
                model: airportModel

                // 空状态提示
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width * 0.6
                    height: 200
                    visible: airportModel.count === 0
                    color: "transparent"

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: style.spacingNormal

                        Text {
                            text: "📦"
                            font.pixelSize: 48
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Text {
                            text: "暂无机场数据"
                            font.pixelSize: style.fontSizeLarge || 20
                            font.bold: true
                            color: theme.textPrimary
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Text {
                            text: "请点击上方 \"导入数据\" 按钮导入 EAIP 数据包"
                            font.pixelSize: style.fontSizeMedium || 16
                            color: theme.textSecondary
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                delegate: Rectangle {
                    width: airportListView.width
                    height: style.listItemHeight
                    radius: style.cardRadius
                    color: theme.cardBackground

                    // 阴影
                    layer.enabled: true
                    layer.effect: DropShadow {
                        radius: style.shadowMedium
                        samples: 16
                        color: Qt.rgba(0, 0, 0, theme.isDark ? 0.5 : 0.1)
                        verticalOffset: style.shadowSmall
                    }

                    // 悬浮效果
                    property bool hovered: false

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor

                        onEntered: parent.hovered = true
                        onExited: parent.hovered = false

                        onClicked: {
                            airportSelected(model.code, model.nameZh)
                        }
                    }

                    // 内容
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: style.cardPadding
                        spacing: style.spacingNormal

                        // 图标
                        Text {
                            text: "🛫"
                            font.pixelSize: style.fontSizeXLarge || 24
                        }

                        // 文字信息
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: style.spacingXSmall

                            Row {
                                spacing: style.spacingSmall

                                Text {
                                    text: model.code
                                    font.pixelSize: style.fontSizeMedium || 16
                                    font.bold: true
                                    color: theme.accent
                                }

                                Text {
                                    text: "-"
                                    font.pixelSize: style.fontSizeMedium || 16
                                    color: theme.textSecondary
                                }

                                Text {
                                    text: model.nameZh
                                    font.pixelSize: style.fontSizeMedium || 16
                                    color: theme.textPrimary
                                }
                            }

                            Text {
                                text: model.nameEn
                                font.pixelSize: style.fontSizeSmall || 12
                                color: theme.textSecondary
                            }
                        }

                        // 箭头
                        Text {
                            text: "→"
                            font.pixelSize: style.fontSizeLarge || 20
                            color: theme.accent
                        }
                    }

                    // 悬浮动画
                    Behavior on scale {
                        NumberAnimation {
                            duration: style.animationFast
                            easing.type: Easing.OutQuad
                        }
                    }

                    scale: hovered ? 1.02 : 1.0
                }
            }
        }
    }
}
