// ThemeManager.qml - 主题管理器
import QtQuick 2.15

QtObject {
    id: themeManager

    // 主题模式
    property string mode: "light"  // "light", "dark", "auto"

    // 强调色
    property string accentColorName: "aviation_blue"

    // 颜色定义
    readonly property var colors: {
        "aviation_blue": { light: "#1976D2", dark: "#42A5F5" },
        "sky_blue": { light: "#0288D1", dark: "#29B6F6" },
        "green": { light: "#388E3C", dark: "#66BB6A" },
        "purple": { light: "#5E35B1", dark: "#7E57C2" },
        "amber": { light: "#F57C00", dark: "#FFA726" },
        "pink": { light: "#C2185B", dark: "#F06292" },
        "gray": { light: "#455A64", dark: "#78909C" }
    }

    // 当前是否为深色模式
    readonly property bool isDark: mode === "dark"

    // 背景色
    readonly property color background: isDark ? "#121212" : "#FAFAFA"

    // 卡片背景色
    readonly property color cardBackground: isDark ? "#1E1E1E" : "#FFFFFF"

    // 文字颜色
    readonly property color textPrimary: isDark ? "#FFFFFF" : "#212121"
    readonly property color textSecondary: isDark ? "#B0B0B0" : "#757575"

    // 强调色
    readonly property color accent: {
        if (accentColorName in colors) {
            return isDark ? colors[accentColorName].dark : colors[accentColorName].light
        }
        // 默认航空蓝
        return isDark ? "#42A5F5" : "#1976D2"
    }

    // 阴影颜色
    readonly property color shadowColor: isDark ? "#000000" : "#000000"

    // 分隔线颜色
    readonly property color divider: isDark ? "#424242" : "#E0E0E0"

    // 悬浮颜色
    readonly property color hover: isDark ? "#2C2C2C" : "#F5F5F5"

    // 选中颜色
    readonly property color selected: Qt.rgba(accent.r, accent.g, accent.b, 0.12)

    // 错误颜色
    readonly property color error: "#F44336"

    // 成功颜色
    readonly property color success: "#4CAF50"

    // 警告颜色
    readonly property color warning: "#FF9800"

    // 函数：切换主题模式
    function toggleMode() {
        mode = isDark ? "light" : "dark"
    }

    // 函数：设置强调色
    function setAccentColor(colorName) {
        if (colorName in colors) {
            accentColorName = colorName
        }
    }
}
