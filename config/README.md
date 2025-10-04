# EAIP Viewer 配置说明

## 配置文件位置
- **示例文件**: `config/settings.json.example`
- **实际配置**: `config/settings.json`

## 首次使用
1. 复制 `settings.json.example` 为 `settings.json`
2. 根据需要修改配置项
3. 重启应用生效

## 配置项说明

### 基本配置

#### `data_path` (字符串)
- **说明**: 航图数据存储路径
- **默认值**: `"./data"`
- **推荐值**: 相对路径（便于移植）或绝对路径

#### `cache_path` (字符串)
- **说明**: 缓存目录路径，存储临时文件和渲染的 PDF 图片
- **默认值**: `"./cache"`
- **注意**: 可定期清理以释放空间

#### `max_pins` (整数)
- **说明**: 最大固定航图数量
- **默认值**: `10`
- **范围**: 1-20
- **提示**: 过多会影响底部栏显示

#### `pdf_render_dpi` (整数)
- **说明**: PDF 渲染 DPI，影响图片清晰度和文件大小
- **默认值**: `150`
- **范围**: 100-300
- **提示**:
  - 100-150: 快速渲染，较小文件
  - 150-200: 平衡清晰度和性能（推荐）
  - 200-300: 高清晰度，较慢渲染

#### `language` (字符串)
- **说明**: 界面语言
- **默认值**: `"zh_CN"`
- **可选值**:
  - `"zh_CN"`: 简体中文
  - `"en_US"`: English (开发中)

### 主题配置 (`theme` 对象)

#### `theme.mode` (字符串)
- **说明**: 主题模式
- **默认值**: `"light"`
- **可选值**:
  - `"light"`: 浅色主题
  - `"dark"`: 深色主题
  - `"auto"`: 跟随系统（开发中）

#### `theme.accent_color` (字符串)
- **说明**: 主题强调色
- **默认值**: `"aviation_blue"`
- **可选值**:
  - `"aviation_blue"`: 航空蓝（推荐）
  - `"red"`: 红色
  - `"green"`: 绿色
  - `"purple"`: 紫色
  - 更多颜色可在代码中自定义

### 启动画面配置 (`splash_screen` 对象)

#### `splash_screen.enabled` (布尔值)
- **说明**: 是否启用启动画面
- **默认值**: `true`
- **提示**: 关闭可加快启动速度

#### `splash_screen.min_display_time` (整数)
- **说明**: 启动画面最小显示时间（毫秒）
- **默认值**: `1500`
- **范围**: 500-5000
- **提示**: 即使加载很快，也会显示此时间

### 导入配置 (`import` 对象)

#### `import.max_workers` (字符串或整数)
- **说明**: 导入数据时使用的工作线程数
- **默认值**: `"auto"`
- **可选值**:
  - `"auto"`: 自动根据 CPU 核心数和 `auto_workers_ratio` 计算
  - 整数: 手动指定线程数（1 到 CPU线程数*0.7）
- **示例**:
  - 4核8线程 CPU，auto 模式默认使用 4 个线程（8*0.5）
  - 手动设置为 `4` 则始终使用 4 个线程

#### `import.auto_workers_ratio` (浮点数)
- **说明**: 自动模式下使用的 CPU 线程比例
- **默认值**: `0.5`
- **范围**: 0.1-0.7
- **提示**:
  - `0.5`: 使用 50% CPU 线程（推荐，平衡性能和响应）
  - `0.3`: 保守，导入较慢但不影响其他任务
  - `0.7`: 激进，导入最快但可能卡顿

### 固定航图 (`pinned_charts` 数组)

#### `pinned_charts` (数组)
- **说明**: 固定的航图列表
- **默认值**: `[]`
- **注意**: 由程序自动管理，**无需手动编辑**
- **数据结构**:
```json
[
  {
    "chart_id": "ZBAA-01L-SID",
    "name": "ZBAA 01L SID",
    "file_path": "F:/data/2505/Terminal/ZBAA/SID/ZBAA-01L-SID.pdf",
    "airport_code": "ZBAA",
    "category": "SID",
    "thumbnail": "",
    "pinned_at": "2025-10-04T10:30:00.000Z"
  }
]
```

## 配置修改生效

### 立即生效的配置
- `theme.mode` - 主题模式
- `theme.accent_color` - 主题色
- `max_pins` - 固定航图上限

### 需要重启生效的配置
- `data_path` - 数据路径
- `cache_path` - 缓存路径
- `language` - 界面语言
- `splash_screen.*` - 启动画面配置
- `import.*` - 导入配置

## 故障排除

### 配置文件损坏
如果配置文件损坏导致无法启动：
1. 删除 `config/settings.json`
2. 重启应用，会自动创建默认配置

### 恢复默认配置
1. 删除 `config/settings.json`
2. 复制 `settings.json.example` 为 `settings.json`
3. 重启应用

### 配置不生效
1. 检查 JSON 格式是否正确（可用在线工具验证）
2. 检查值是否在允许范围内
3. 查看应用日志 `logs/app.log` 获取错误信息

## 性能优化建议

### 针对低配置电脑
```json
{
  "pdf_render_dpi": 100,
  "import": {
    "max_workers": 2
  }
}
```

### 针对高配置电脑
```json
{
  "pdf_render_dpi": 200,
  "import": {
    "auto_workers_ratio": 0.7
  }
}
```

### 针对 SSD 固态硬盘
```json
{
  "import": {
    "max_workers": "auto",
    "auto_workers_ratio": 0.6
  }
}
```
