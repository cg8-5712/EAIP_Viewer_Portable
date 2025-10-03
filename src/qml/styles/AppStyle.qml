// AppStyle.qml - 应用样式定义
import QtQuick 2.15

QtObject {
    id: appStyle

    // 字体大小
    readonly property int fontSizeXLarge: 24
    readonly property int fontSizeLarge: 20
    readonly property int fontSizeMedium: 16
    readonly property int fontSizeNormal: 14
    readonly property int fontSizeSmall: 12

    // 间距
    readonly property int spacingXSmall: 4
    readonly property int spacingSmall: 8
    readonly property int spacingMedium: 12
    readonly property int spacingNormal: 16
    readonly property int spacingLarge: 24
    readonly property int spacingXLarge: 32

    // 圆角
    readonly property int radiusSmall: 4
    readonly property int radiusMedium: 8
    readonly property int radiusLarge: 12
    readonly property int radiusXLarge: 16

    // 边框
    readonly property int borderThin: 1
    readonly property int borderMedium: 2
    readonly property int borderThick: 4

    // 动画时长
    readonly property int animationFast: 150
    readonly property int animationNormal: 200
    readonly property int animationMedium: 300
    readonly property int animationSlow: 400

    // 阴影
    readonly property int shadowSmall: 2
    readonly property int shadowMedium: 4
    readonly property int shadowLarge: 8

    // 卡片
    readonly property int cardPadding: spacingNormal
    readonly property int cardRadius: radiusMedium
    readonly property int cardElevation: shadowMedium

    // 按钮
    readonly property int buttonHeight: 40
    readonly property int buttonPadding: spacingNormal
    readonly property int buttonRadius: radiusSmall

    // 输入框
    readonly property int inputHeight: 40
    readonly property int inputPadding: spacingMedium
    readonly property int inputRadius: radiusSmall

    // 列表项
    readonly property int listItemHeight: 72
    readonly property int listItemPadding: spacingNormal

    // 工具栏
    readonly property int toolbarHeight: 56
    readonly property int toolbarPadding: spacingNormal

    // Pin 栏
    readonly property int pinBarHeight: 100
    readonly property int pinItemSize: 80
    readonly property int pinItemSpacing: spacingSmall
}
