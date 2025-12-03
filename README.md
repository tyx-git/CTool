# 命令速查工具

一个基于PyQt5的图形化命令管理工具，可以帮助用户快速保存、搜索和执行常用命令。

## 功能特点

- 图形化界面操作，简单易用
- 支持命令的增删改查
- 智能搜索功能，快速定位所需命令
- 命令使用统计，了解常用命令
- 内置AI助手，可智能推荐命令
- 终端集成，直接执行命令

## 技术架构

- **编程语言**: Python 3.x
- **GUI框架**: PyQt5
- **数据库**: SQLite
- **AI支持**: DeepSeek API
- **依赖管理**: pip

## 安装依赖

```bash
pip install -r requirements.txt
```

## 主要组件

### 核心模块
- `main.py`: 程序入口点
- `core/command_manager.py`: 命令管理器，负责命令的增删改查
- `core/terminal_manager.py`: 终端管理器，负责执行系统命令
- `core/ai_assistant.py`: AI助手，提供智能命令推荐
- `core/logger.py`: 日志管理器

### 配置模块
- `config/config_manager.py`: 配置管理器
- `config/app.json`: 应用配置
- `config/api.json`: AI API配置
- `config/windows.json`: 窗口配置

### UI模块
- `ui/main_window.py`: 主窗口界面
- `ui/command_panel.py`: 命令面板
- `ui/terminal_panel.py`: 终端面板
- `ui/add_command_dialog.py`: 添加命令对话框

### AI模块
- `ai/deepseek-api.py`: DeepSeek API接口示例

## 数据库结构

使用SQLite数据库存储命令信息，主要字段包括：
- id: 命令唯一标识
- command_text: 命令文本
- description: 命令描述
- working_directory: 工作目录
- create_time: 创建时间
- update_time: 更新时间
- usage_count: 使用次数

## 使用说明

1. 运行程序：
   ```bash
   python main.py
   ```

2. 在搜索框中输入关键字搜索命令

3. 点击命令项可复制命令到剪贴板

4. 右键点击命令项可编辑或删除命令

5. 使用AI助手可以获得智能命令推荐

## 配置说明

在`config/api.json`中配置您的DeepSeek API密钥：
```json
{
    "api": {
        "api_key": "your_api_key_here",
        "api_url": "https://api.deepseek.com",
        "model": "deepseek-chat"
    }
}
```

## 许可证

MIT License