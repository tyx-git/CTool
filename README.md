# 命令速查工具 | Command Quick Reference Tool

<div align="center">
  <img src="public/ca.jpg" alt="应用截图" width="600"/>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/PyQt5-GUI-red.svg" alt="GUI Framework">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

一个基于PyQt5的图形化命令管理工具，可以帮助开发者和技术人员快速保存、搜索和执行常用命令。集成了AI助手功能，能够智能推荐相关命令，提高工作效率。

## 🌟 特性亮点

### 🔧 强大的命令管理
- **可视化界面操作**：直观的图形界面，操作简单便捷
- **命令增删改查**：完整的命令生命周期管理
- **智能搜索功能**：支持模糊匹配和关键词高亮，快速定位所需命令
- **使用统计分析**：记录命令使用频率，了解个人常用命令习惯
- **工作目录绑定**：为每个命令设置特定的工作目录，一键切换执行环境

### 🤖 AI智能助手
- **智能命令推荐**：基于自然语言描述，推荐相关命令
- **实时交互对话**：与AI助手进行命令相关的技术问答
- **流式响应显示**：流畅的打字机效果，提升用户体验
- **深度学习支持**：集成DeepSeek等大语言模型API

### 💻 终端集成
- **内置终端面板**：直接在应用内执行命令，无需切换窗口
- **PowerShell支持**：专为Windows环境优化，默认使用PowerShell 7
- **ANSI色彩支持**：完美显示彩色终端输出
- **目录自动跟踪**：智能识别和同步终端当前工作目录

### ⚙️ 个性化配置
- **窗口状态记忆**：自动保存上次关闭时的窗口大小和位置
- **界面自适应布局**：支持拖拽调整各面板大小
- **字体大小调节**：根据个人喜好调整界面字体大小
- **主题风格保持**：保留用户的界面定制偏好

## 🏗️ 技术架构

- **编程语言**: Python 3.x
- **GUI框架**: PyQt5
- **数据库**: SQLite (轻量级本地存储)
- **AI支持**: DeepSeek API / OpenAI兼容接口
- **依赖管理**: pip
- **日志系统**: 内置多级日志记录和监控

## 🚀 快速开始

### 环境要求
- Python 3.7+
- Windows 10/11 (推荐PowerShell 7)
- DeepSeek API Key (可选，用于AI功能)

### 安装步骤

1. 克隆项目代码：
   ```bash
   git clone https://github.com/yourusername/command-quick-reference.git
   cd command-quick-reference
   ```

2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置API密钥（可选）：
   编辑 `config/api.json` 文件，填入您的DeepSeek API密钥：
   ```json
   {
       "api": {
           "api_key": "your_actual_api_key_here",
           "api_url": "https://api.deepseek.com",
           "model": "deepseek-chat"
       }
   }
   ```

4. 运行程序：
   ```bash
   python main.py
   ```

## 📖 使用指南

### 基础操作
1. **添加命令**：点击"添加命令"按钮，在弹出对话框中填写命令详情
2. **搜索命令**：在顶部搜索框中输入关键词，实时筛选匹配命令
3. **执行命令**：双击命令项，将在终端面板中自动填充命令，按回车执行
4. **复制命令**：点击命令项右侧的"复制"按钮，快速复制到剪贴板

### 高级功能
1. **AI助手**：在左侧AI助手面板中输入问题，获得智能命令建议
2. **目录切换**：为命令设置工作目录，执行时自动切换到指定路径
3. **使用统计**：通过"使用次数"排序，发现最常用的命令
4. **右键菜单**：在命令项上右键，快速编辑或删除命令

## 📁 项目结构

```
command-quick-reference/
├── ai/                    # AI相关模块
│   └── deepseek-api.py   # DeepSeek API示例
├── config/               # 配置文件目录
│   ├── api.json          # AI API配置
│   ├── app.json          # 应用配置
│   ├── config_manager.py # 配置管理器
│   └── windows.json      # 窗口状态配置
├── core/                 # 核心功能模块
│   ├── ai_assistant.py   # AI助手核心
│   ├── command_manager.py# 命令管理器
│   ├── logger.py         # 日志管理器
│   └── terminal_manager.py# 终端管理器
├── data/                 # 数据存储目录
│   └── commands.db       # SQLite命令数据库
├── public/               # 公共资源文件
│   └── ca.jpg            # 应用图标
├── ui/                   # 用户界面模块
│   ├── add_command_dialog.py # 添加命令对话框
│   ├── command_panel.py     # 命令管理面板
│   ├── main_window.py       # 主窗口界面
│   ├── terminal_panel.py    # 终端面板
│   └── ...                  # 其他UI组件
├── main.py               # 程序入口点
└── requirements.txt      # 依赖包列表
```

## 🗄️ 数据库设计

使用SQLite数据库存储命令信息，主要字段包括：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 命令唯一标识 |
| command_text | TEXT | 命令文本 |
| description | TEXT | 命令描述 |
| working_directory | TEXT | 工作目录 |
| create_time | DATETIME | 创建时间 |
| update_time | DATETIME | 更新时间 |
| usage_count | INTEGER | 使用次数 |

## 🔧 开发指南

### 核心模块说明

1. **CommandManager (`core/command_manager.py`)**：
   - 负责命令的增删改查操作
   - 提供智能搜索算法，支持命令文本和描述的模糊匹配
   - 维护命令使用统计信息

2. **TerminalManager (`core/terminal_manager.py`)**：
   - 管理PowerShell进程的启动、停止和通信
   - 处理命令执行和输出捕获
   - 支持工作目录切换和ANSI色彩代码解析

3. **AIManager (`core/ai_assistant.py`)**：
   - 集成OpenAI兼容API接口
   - 管理对话历史和上下文
   - 提供流式响应处理能力

4. **ConfigManager (`config/config_manager.py`)**：
   - 统一管理系统各项配置
   - 自动保存和恢复窗口状态
   - 支持多层级配置结构

### UI组件说明

1. **MainWindow (`ui/main_window.py`)**：
   - 主程序窗口，协调各组件工作
   - 管理整体布局和窗口状态
   - 处理用户交互事件

2. **TerminalPanel (`ui/terminal_panel.py`)**：
   - 终端显示和输入组件
   - 支持ANSI色彩渲染和自动滚动

3. **CommandPanel (`ui/command_panel.py`)**：
   - 命令管理和编辑面板
   - 提供命令表单的显示和操作

## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进这个项目！

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

## 📃 许可证

本项目采用MIT许可证，详情请见[LICENSE](LICENSE)文件。
