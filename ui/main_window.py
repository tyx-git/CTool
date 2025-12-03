import sys
import os
import traceback
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QSplitter, 
                             QListView, QLabel, QTextEdit, QListWidgetItem, 
                             QMessageBox, QDialog, QSizePolicy, QMenu, QAction)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QFontMetrics, QTextCursor, QCursor

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from PyQt5.QtCore import Qt as QtEnum
else:
    QtEnum = int

# 添加类型注释以解决类型检查问题
from PyQt5.QtCore import Qt as QtConstants

# 添加日志管理器导入
from core.logger import get_log_manager

from ui.command_panel import CommandPanel
from ui.terminal_panel import TerminalPanel
from ui.add_command_dialog import AddCommandDialog
from core.command_manager import CommandManager
from core.terminal_manager import TerminalManager
from config.config_manager import get_config_manager

# 获取日志记录器
logger = get_log_manager().get_logger('main_window')

class CommandListItem(QWidget):
    """自定义命令列表项"""
    
    def __init__(self, command_id, command_text, description, working_dir, parent=None):
        super().__init__(parent)
        self.command_id = command_id
        self.command_text = command_text
        self.description = description
        self.working_dir = working_dir
        
        # 从配置中获取字体大小
        self.config_manager = get_config_manager()
        ui_state = self.config_manager.get_ui_state()
        self.font_size = ui_state.get('font_size', 14)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)  # 增加上下边距使对齐更美观
        layout.setSpacing(15)  # 组件间距
        
        # 命令文本
        command_label = QLabel(self.command_text)
        command_label.setStyleSheet("font-weight: 600; color: #2c3e50;")
        command_label.setToolTip(self.command_text)  # 显示完整文本的提示
        command_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        command_label.setWordWrap(False)
        
        # 描述
        desc_label = QLabel(self.description if self.description else "")
        desc_label.setStyleSheet("color: #555555; font-size: 13px;")
        desc_label.setToolTip(self.description if self.description else "")
        desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        desc_label.setWordWrap(False)
        
        # 设置省略号显示在末尾，并为不同字段分配不同宽度
        # 命令文本需要更多空间显示
        command_label.setWordWrap(False)
        # 简化实现，避免类型检查错误
        if len(self.command_text) > 50:
            command_label.setText(self.command_text[:47] + "...")
        
        # 描述文本中等宽度
        desc_label.setWordWrap(False)
        if len(self.description if self.description else "") > 35:
            desc_label.setText((self.description[:32] if self.description else "") + "...")
        
        # 复制按钮
        copy_button = QPushButton("复制")
        copy_button.setFixedWidth(60)
        # 为复制按钮添加样式以提升美观度
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border: 1px solid #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                border: 1px solid #868e96;
            }
        """)
        
        # 添加到布局
        layout.addWidget(command_label)
        layout.addWidget(desc_label)
        layout.addStretch()  # 添加弹性空间
        layout.addWidget(copy_button)
        
        # 连接按钮信号
        copy_button.clicked.connect(self.copy_to_clipboard)
        
        # 启用右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore
        self.customContextMenuRequested.connect(self.show_context_menu)  # type: ignore
        
    def copy_to_clipboard(self):
        """复制命令到剪贴板"""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.command_text)
            
    def show_context_menu(self, position):
        """显示右键菜单"""
        context_menu = QMenu(self)
        
        # 创建菜单项
        copy_action = QAction("复制命令", self)
        edit_action = QAction("编辑命令", self)
        delete_action = QAction("删除命令", self)
        
        # 连接信号
        copy_action.triggered.connect(self.copy_to_clipboard)
        edit_action.triggered.connect(self.edit_command)
        delete_action.triggered.connect(self.delete_command)
        
        # 添加到菜单
        context_menu.addAction(copy_action)
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        
        # 显示菜单
        context_menu.exec_(self.mapToGlobal(position))
        
    def edit_command(self):
        """编辑命令"""
        # 获取主窗口并调用编辑命令方法
        main_window = self.window()
        if main_window and hasattr(main_window, 'edit_command'):
            main_window.edit_command(self.command_id, self.command_text, self.description, self.working_dir)
            
    def delete_command(self):
        """删除命令"""
        # 获取主窗口并调用删除命令方法
        main_window = self.window()
        if main_window and hasattr(main_window, 'delete_command'):
            main_window.delete_command(self.command_id)

class AIWorker(QThread):
    """AI工作线程"""
    result_ready = pyqtSignal(dict)  # 结果信号
    stream_data_ready = pyqtSignal(str)  # 流式数据信号
    
    def __init__(self, ai_manager, user_message, system_prompt):
        super().__init__()
        self.ai_manager = ai_manager
        self.user_message = user_message
        self.system_prompt = system_prompt
        self.is_streaming = True
        
    def run(self):
        """执行AI调用"""
        try:
            # 使用流式API调用
            result = self.ai_manager.chat_stream(
                self.user_message, 
                self.system_prompt, 
                self._stream_callback
            )
            self.result_ready.emit(result)
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e)
            }
            self.result_ready.emit(error_result)
    
    def _stream_callback(self, data: str):
        """流式数据回调"""
        if self.is_streaming:
            self.stream_data_ready.emit(data)
            
    def stop_streaming(self):
        """停止流式传输"""
        self.is_streaming = False

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        try:
            logger.info("初始化主窗口")
            self.command_manager = CommandManager()
            self.terminal_manager = TerminalManager()
            self.config_manager = get_config_manager()
            
            # 初始化AI助手
            from core.ai_assistant import get_ai_assistant
            self.ai_manager = get_ai_assistant(self.config_manager)
            
            self.init_ui()
            self.setup_connections()
            self.load_window_state()
            QTimer.singleShot(100, self.load_commands)
            logger.info("主窗口初始化完成")
        except Exception as e:
            logger.error(f"主窗口初始化失败: {e}")
            traceback.print_exc()
        
    def init_ui(self):
        """初始化UI界面"""
        logger.info("初始化UI界面")
        self.setWindowTitle("命令速查工具")
        
        # 设置窗口属性，确保可以拖拽
        self.setWindowFlags(Qt.WindowFlags())  # 使用默认窗口标志
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'public', 'ca.jpg')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 从配置中获取字体大小
        ui_state = self.config_manager.get_ui_state()
        self.font_size = ui_state.get('font_size', 14)
        self.ai_title_font_size = self.font_size + 6  # AI标题字体大小
        self.ai_component_font_size = self.font_size + 2  # AI组件字体大小
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)  # type: ignore
        main_layout.addWidget(splitter)
        self.main_splitter = splitter  # 保存对主分割器的引用
        
        # 创建左侧AI助手区域（占25%）
        self.ai_widget = QWidget()
        self.ai_widget.setMinimumWidth(250)  # 增加宽度
        self.ai_widget.setStyleSheet("""
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6;
            border-radius: 8px;
        """)
        ai_layout = QVBoxLayout(self.ai_widget)
        ai_layout.setSpacing(10)  # 增加间距
        ai_layout.setContentsMargins(15, 15, 15, 15)  # 增加边距
        
        # 添加AI助手标题和功能区域
        ai_title = QLabel("AI助手")
        ai_title.setStyleSheet(f"""
            font-size: {self.ai_title_font_size}px; 
            font-weight: bold; 
            padding: 10px;
            color: #2c3e50;
            border-bottom: 1px solid #dee2e6;
        """)
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setPlaceholderText("AI助手输出区域...")
        self.ai_output.setStyleSheet(f"""
            background-color: white;
            border: 1px solid #ced4da;
            border-radius: 6px;
            padding: 5px;
            font-size: {self.ai_component_font_size}px;
            color: #333;
            line-height: 1.0;
        """)
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("向AI助手提问...")
        self.ai_input.setStyleSheet(f"""
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: {self.ai_component_font_size}px;
        """)
        self.ai_send_button = QPushButton("发送")  # 保存为实例变量
        self.ai_send_button.setStyleSheet(f"""
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: {self.ai_component_font_size}px;
            font-weight: bold;
        """)
        self.ai_input.returnPressed.connect(self.send_ai_message)
        
        ai_layout.addWidget(ai_title)
        ai_layout.addWidget(self.ai_output)
        ai_layout.addWidget(self.ai_input)
        ai_layout.addWidget(self.ai_send_button)
        
        splitter.addWidget(self.ai_widget)
        
        # 创建右侧主区域（占75%）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(right_widget)
        self.right_widget = right_widget  # 保存对右侧部件的引用
        
        # 创建命令搜索区域
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索命令...")
        # 连接回车键事件进行搜索
        self.search_input.returnPressed.connect(lambda: self.load_commands(self.search_input.text()))
        
        # 添加清除按钮
        self.clear_button = QPushButton("清除")
        
        # 移除管理命令按钮，只保留添加命令按钮
        self.add_button = QPushButton("添加命令")
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_button)
        search_layout.addWidget(self.add_button)
        
        right_layout.addWidget(search_widget)
        
        # 创建命令列表和管理面板区域
        content_splitter = QSplitter()
        content_splitter.setOrientation(Qt.Vertical)  # type: ignore
        right_layout.addWidget(content_splitter)
        self.content_splitter = content_splitter  # 保存对内容分割器的引用
        
        # 创建命令列表区域
        self.command_list_view = QListView()
        self.command_model = QStandardItemModel()
        self.command_list_view.setModel(self.command_model)
        
        # 为命令列表添加样式
        self.command_list_view.setStyleSheet("""
            QListView {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 5px;
                outline: 0;
            }
            QListView::item {
                border-bottom: 1px solid #f0f0f0;
                padding: 0;
            }
            QListView::item:selected {
                background-color: #e3f2fd;
                border-radius: 4px;
            }
        """)
        
        content_splitter.addWidget(self.command_list_view)
        
        # 创建终端区域（占40%）
        self.terminal_panel = TerminalPanel(self.terminal_manager)
        content_splitter.addWidget(self.terminal_panel)
        
        # 创建命令管理面板（默认隐藏）
        self.command_panel = CommandPanel(self.command_manager)
        self.command_panel.setVisible(False)
        right_layout.addWidget(self.command_panel)
        logger.info("UI界面初始化完成")
 
    def setup_connections(self):
        """设置信号槽连接"""
        logger.info("设置信号槽连接")
        self.search_input.textChanged.connect(self.on_search_changed)
        # 连接清除按钮
        self.clear_button.clicked.connect(self.clear_search)
        # 使用右键菜单
        # self.manage_button.clicked.connect(self.toggle_command_panel)
        self.add_button.clicked.connect(self.show_add_command_dialog)
        self.command_panel.command_updated.connect(self.load_commands)
        
        # 连接命令列表的双击事件
        self.command_list_view.doubleClicked.connect(self.on_command_double_clicked)
        
        # 连接AI助手的发送按钮和回车键事件
        self.ai_send_button.clicked.connect(self.send_ai_message)
        self.ai_input.returnPressed.connect(self.send_ai_message)
        logger.info("信号槽连接设置完成")

    def load_commands(self, keyword=""):
        """加载命令列表"""
        try:
            logger.info(f"加载命令列表，搜索关键词: {keyword}")
            self.command_model.clear()
            
            if keyword:
                commands = self.command_manager.search_command(keyword)
            else:
                commands = self.command_manager.get_all_commands()
                
            logger.info(f"找到 {len(commands)} 条命令")
            for cmd in commands:
                item = QStandardItem()
                widget = CommandListItem(
                    cmd['id'],
                    cmd['command_text'],
                    cmd['description'],
                    cmd['working_directory']
                )
                item.setSizeHint(widget.sizeHint())
                self.command_model.appendRow(item)
                self.command_list_view.setIndexWidget(item.index(), widget)
                
            # 优化命令列表的显示效果
            self.command_list_view.setStyleSheet("""
                QListView {
                    background-color: white;
                    border: none;
                    outline: 0;
                }
                QListView::item {
                    border-bottom: 1px solid #f0f0f0;
                    padding: 0;
                }
                QListView::item:selected {
                    background-color: #e3f2fd;
                }
            """)
        except Exception as e:
            logger.error(f"加载命令列表失败: {e}")
            traceback.print_exc()
            
    def on_search_changed(self, text):
        """搜索框内容变化时触发"""
        logger.info(f"搜索框内容变化: {text}")
        if not hasattr(self, '_search_timer'):
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(lambda: self.load_commands(text))
        else:
            self._search_timer.stop()
            
        self._search_timer.start(500)  # 增加延迟到500ms以减少闪烁
        
    def clear_search(self):
        """清除搜索框并显示所有命令"""
        logger.info("清除搜索框")
        self.search_input.clear()  # 清除搜索框内容
        self.load_commands()  # 加载所有命令
        
    def toggle_command_panel(self):
        """切换命令管理面板显示状态"""
        is_visible = self.command_panel.isVisible()
        self.command_panel.setVisible(not is_visible)
        
        # 更新按钮文本
        if self.command_panel.isVisible():
            self.manage_button.setText("隐藏管理")
        else:
            self.manage_button.setText("管理命令")
            
    def show_add_command_dialog(self):
        """显示添加命令对话框"""
        try:
            logger.info("显示添加命令对话框")
            dialog = AddCommandDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                command_data = dialog.get_command_data()
                if command_data['command_text']:
                    cmd_id = self.command_manager.add_command(
                        command_data['command_text'],
                        command_data['description'],
                        command_data['working_directory']
                    )
                    if cmd_id > 0:
                        logger.info(f"命令添加成功，ID: {cmd_id}")
                    else:
                        logger.error("命令添加失败")
                    self.load_commands()
        except Exception as e:
            logger.error(f"显示添加命令对话框失败: {e}")
            traceback.print_exc()
                
    def on_command_double_clicked(self, index):
        """命令列表双击事件"""
        try:
            logger.info("命令列表双击事件")
            # 获取对应的widget
            item = self.command_model.itemFromIndex(index)
            widget = self.command_list_view.indexWidget(index)
            
            if widget and hasattr(widget, 'command_text') and hasattr(widget, 'working_dir'):
                command_text = widget.command_text
                working_dir = widget.working_dir
                command_id = widget.command_id
                
                logger.info(f"双击命令: {command_text}, 工作目录: {working_dir}")
                
                # 增加使用次数
                self.command_manager.increment_command_usecounts(command_id)
                
                # 切换工作目录（如果指定了工作目录）
                if working_dir:
                    # 使用立即执行的方式切换目录
                    try:
                        self.terminal_manager.change_directory(working_dir)
                    except Exception as e:
                        logger.error(f"切换目录时出错: {e}")

                try:
                    # 根据规范，将命令文本填充到终端输入框而不是直接执行
                    self.terminal_panel.command_input.setText(command_text)
                except Exception as e:
                    logger.error(f"设置命令到输入框时出错: {e}")
                
                # 将焦点设置到终端输入框
                try:
                    self.terminal_panel.command_input.setFocus()
                except Exception as e:
                    logger.error(f"设置焦点时出错: {e}")
                
                # 不再重新加载命令列表，避免干扰搜索状态
                # self.load_commands(self.search_input.text())
        except Exception as e:
            logger.error(f"命令列表双击事件处理失败: {e}")
            traceback.print_exc()
            
    def send_ai_message(self):
        """发送AI消息"""
        message = self.ai_input.text().strip()
        if not message:
            return
            
        logger.info(f"发送AI消息: {message}")
        # 显示用户消息
        self.ai_output.append(f"<b style='color: #007bff;'>用户:</b> {message}")
        
        # 清空输入框
        self.ai_input.clear()
        
        # 禁用发送按钮，显示正在处理状态
        self.ai_send_button.setEnabled(False)
        self.ai_send_button.setText("思考中...")
        
        # 显示思考动画
        self.thinking_dots = 0
        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking_animation)
        self.thinking_timer.start(500)  # 每500ms更新一次
        
        # 在新线程中处理AI调用
        self.ai_worker = AIWorker(self.ai_manager, message, "你是一个命令行工具助手，帮助用户理解和使用各种命令行工具。")
        self.ai_worker.result_ready.connect(self.handle_ai_result)
        self.ai_worker.stream_data_ready.connect(self.handle_ai_stream_data)
        self.ai_worker.start()
        
        # 初始化AI响应显示
        self.ai_output.append(f"<b style='color: #28a745;'>AI助手:</b> ")
        self.ai_current_response = ""
        
    def handle_ai_stream_data(self, data: str):
        """处理AI流式数据"""
        try:
            # 累积响应数据
            self.ai_current_response += data
            
            # 在UI中显示流式数据
            # 移动光标到AI助手响应的末尾
            cursor = self.ai_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.ai_output.setTextCursor(cursor)
            
            # 插入新的流式数据
            self.ai_output.insertPlainText(data)
            
            # 滚动到底部
            self.ai_output.moveCursor(QTextCursor.End)
            self.ai_output.ensureCursorVisible()
            
        except Exception as e:
            logger.error(f"处理AI流式数据失败: {e}")
            
    def update_thinking_animation(self):
        """更新思考动画"""
        self.thinking_dots = (self.thinking_dots + 1) % 4
        dots = "." * self.thinking_dots
        self.ai_send_button.setText(f"思考中{dots}")
        
    def handle_ai_result(self, result):
        """处理AI结果"""
        logger.info("处理AI结果")
        # 停止思考动画
        if hasattr(self, 'thinking_timer'):
            self.thinking_timer.stop()
            del self.thinking_timer
            
        try:
            if result['success']:
                logger.info("AI助手响应成功")
            else:
                # 显示错误信息
                error_msg = result.get('error', 'AI助手响应失败')
                self.ai_output.append(f"\n<b style='color: #dc3545;'>AI助手错误:</b> {error_msg}")
                logger.error(f"AI助手响应失败: {error_msg}")
                
        except Exception as e:
            error_msg = f"处理AI结果失败: {str(e)}"
            self.ai_output.append(f"\n<b style='color: #dc3545;'>AI助手错误:</b> {error_msg}")
            logger.error(error_msg)
        finally:
            # 恢复发送按钮状态
            self.ai_send_button.setEnabled(True)
            self.ai_send_button.setText("发送")
            
            # 滚动到底部
            self.ai_output.moveCursor(QTextCursor.End)
            
            # 清理工作线程
            if hasattr(self, 'ai_worker'):
                self.ai_worker.deleteLater()
                del self.ai_worker
                
            # 清理当前响应缓存
            if hasattr(self, 'ai_current_response'):
                del self.ai_current_response
                
    def _format_ai_response(self, response):
        """
        格式化AI响应，处理Markdown内容
        
        Args:
            response (str): AI原始响应
            
        Returns:
            str: 格式化后的响应
        """
        try:
            # 使用Markdown解析器处理响应
            from core.markdown_parser import get_markdown_parser
            markdown_parser = get_markdown_parser()
            formatted_response = markdown_parser.parse(response)
            return formatted_response
        except Exception as e:
            # 如果Markdown解析失败，回退到原来的处理方式
            logger.warning(f"Markdown解析失败，使用默认格式化: {e}")
            # 处理代码块 ```language\ncontent\n```
            def replace_code_block(match):
                code_content = match.group(2)
                # 转义HTML特殊字符
                code_content = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                return f'<pre style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px; margin: 5px 0; font-family: Consolas, monospace; white-space: pre-wrap;">{code_content}</pre>'
            
            # 处理代码块
            formatted = re.sub(r'```(\w+)?\n(.*?)\n```', replace_code_block, response, flags=re.DOTALL)
            
            # 处理行内代码 `code`
            formatted = re.sub(r'`([^`]+)`', r'<code style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px; padding: 2px 4px; font-family: Consolas, monospace;">\1</code>', formatted)
            
            # 处理换行符
            formatted = formatted.replace('\n', '<br>')
            
            return formatted
        
    def load_window_state(self):
        """加载窗口状态"""
        try:
            logger.info("加载窗口状态")
            # 加载窗口几何信息
            geometry = self.config_manager.get_window_geometry()
            if geometry:
                x, y, width, height = geometry
                # 确保窗口位置在屏幕范围内
                screen = QApplication.primaryScreen()
                if screen is not None:
                    screen_geometry = screen.geometry()
                    # 限制x坐标在屏幕范围内
                    x = max(0, min(x, screen_geometry.width() - width))
                    # 限制y坐标在屏幕范围内
                    y = max(0, min(y, screen_geometry.height() - height))
                self.setGeometry(x, y, width, height)
            else:
                self.setGeometry(100, 100, 1200, 800)

            main_splitter_sizes = self.config_manager.get_splitter_sizes('main_splitter')
            right_splitter_sizes = self.config_manager.get_splitter_sizes('right_splitter')
            
            if hasattr(self, 'main_splitter') and main_splitter_sizes and len(main_splitter_sizes) >= 2:
                try:
                    self.main_splitter.setSizes(main_splitter_sizes)
                except Exception as e:
                    logger.error(f"设置主分割器尺寸失败: {e}")
                    traceback.print_exc()
            if hasattr(self, 'content_splitter') and right_splitter_sizes and len(right_splitter_sizes) >= 2:
                try:
                    self.content_splitter.setSizes(right_splitter_sizes)
                except Exception as e:
                    logger.error(f"设置内容分割器尺寸失败: {e}")
                    traceback.print_exc()
            logger.info("窗口状态加载完成")
        except Exception as e:
            logger.error(f"加载窗口状态失败: {e}")
            traceback.print_exc()
        
    def save_window_state(self):
        """保存窗口状态"""
        try:
            logger.info("保存窗口状态")
            # 保存窗口几何信息
            geometry = f"{self.x()},{self.y()},{self.width()},{self.height()}"
            self.config_manager.save_window_state(geometry, "normal")
            main_splitter_sizes = self.main_splitter.sizes()
            right_splitter_sizes = self.content_splitter.sizes()
            self.config_manager.save_splitter_sizes(main_splitter_sizes, right_splitter_sizes)
            logger.info("窗口状态保存完成")
        except Exception as e:
            logger.error(f"保存窗口状态失败: {e}")
            traceback.print_exc()
        
    def closeEvent(self, a0):
        """窗口关闭事件"""
        logger.info("窗口关闭事件")
        try:
            # 保存窗口状态
            self.save_window_state()
            if hasattr(self, 'terminal_manager'):
                self.terminal_manager.stop_terminal()

            if hasattr(self, 'ai_worker') and self.ai_worker.isRunning():
                logger.info("等待AI工作线程完成")
                self.ai_worker.quit()
                self.ai_worker.wait(3000) 

            if hasattr(self, 'thinking_timer'):
                self.thinking_timer.stop()
                
        except Exception as e:
            logger.error(f"窗口关闭事件处理失败: {e}")
            traceback.print_exc()
        finally:
            # 调用父类的closeEvent方法
            super().closeEvent(a0)
            logger.info("窗口已关闭")

    def edit_command(self, command_id, command_text, description, working_dir):
        """编辑命令"""
        # 显示编辑命令对话框
        try:
            logger.info(f"编辑命令，ID: {command_id}")
            dialog = AddCommandDialog(self)
            dialog.setWindowTitle("编辑命令")  # 设置窗口标题为"编辑命令"
            dialog.set_command_data(command_text, description, working_dir)
            if dialog.exec_() == QDialog.Accepted:
                command_data = dialog.get_command_data()
                if command_data['command_text']:
                    success = self.command_manager.update_command(
                        command_id,
                        command_text=command_data['command_text'],
                        description=command_data['description'],
                        working_directory=command_data['working_directory']
                    )
                    if success:
                        logger.info(f"命令更新成功，ID: {command_id}")
                    else:
                        logger.error(f"命令更新失败，ID: {command_id}")
                    self.load_commands(self.search_input.text())  # 重新加载命令列表，保持搜索状态
        except Exception as e:
            logger.error(f"编辑命令失败: {e}")
            traceback.print_exc()
            
    def delete_command(self, command_id):
        """删除命令"""
        try:
            logger.info(f"删除命令，ID: {command_id}")
            reply = QMessageBox.question(
                self, 
                '确认删除', 
                '确定要删除这个命令吗？', 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.command_manager.del_command(command_id)
                if success:
                    logger.info(f"命令删除成功，ID: {command_id}")
                else:
                    logger.error(f"命令删除失败，ID: {command_id}")
                self.load_commands(self.search_input.text())  # 重新加载命令列表，保持搜索状态
        except Exception as e:
            logger.error(f"删除命令失败: {e}")
            traceback.print_exc()