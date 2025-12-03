import sys
import traceback
import re
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit, 
                             QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QTextCharFormat, QColor, QFont
import threading

# 添加日志管理器导入
from core.logger import get_log_manager

# 获取日志记录器
logger = get_log_manager().get_logger('terminal_panel')

# 统一字体定义
TERMINAL_FONT_FAMILY = "'Consolas', 'Monaco', 'Courier New', monospace"

class TerminalOutputSignal(QObject):
    """用于跨线程传递终端输出信号的类"""
    output_received = pyqtSignal(str)

class TerminalPanel(QWidget):
    """终端面板"""
    
    def __init__(self, terminal_manager):
        super().__init__()
        try:
            logger.info("初始化终端面板")
            self.terminal_manager = terminal_manager
            self.current_directory = ""  # 保存当前目录
            
            # 从配置中获取字体大小
            from config.config_manager import get_config_manager
            self.config_manager = get_config_manager()
            terminal_config = self.config_manager.get_terminal_config()
            self.terminal_font_size = terminal_config.get('font_size', 12)
            
            # 创建信号对象用于跨线程通信
            self.output_signal = TerminalOutputSignal()
            self.output_signal.output_received.connect(self.append_output)
            
            self.init_ui()
            self.setup_connections()
            QTimer.singleShot(100, self.start_terminal)
            logger.info("终端面板初始化完成")
        except Exception as e:
            logger.error(f"终端面板初始化失败: {e}")
            traceback.print_exc()
            raise
        
    def init_ui(self):
        """初始化UI界面"""
        logger.info("初始化终端面板UI")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        # 设置支持ANSI颜色代码的样式，统一字体
        self.output_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: {TERMINAL_FONT_FAMILY};
                font-size: {self.terminal_font_size}px;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        # 移除默认的"正在启动终端..."文本，避免重复
        # 启动终端时会显示更具体的提示信息
        
        # 创建输入区域（简单的输入框，不带目录标签）
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("在此输入命令，按回车执行...")
        self.command_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-family: {TERMINAL_FONT_FAMILY};
                font-size: {self.terminal_font_size}px;
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QLineEdit:focus {{
                border-color: #0078d4;
                outline: none;
            }}
        """)
        
        input_layout.addWidget(self.command_input)
        
        layout.addWidget(self.output_display)
        layout.addLayout(input_layout)
        logger.info("终端面板UI初始化完成")
        
    def setup_connections(self):
        """设置信号槽连接"""
        logger.info("设置终端面板信号槽连接")
        # 只连接回车键事件
        self.command_input.returnPressed.connect(self.execute_command)
        
        # 注册终端输出回调
        self.terminal_manager.register_output_callback(self._on_output_received)
        logger.info("终端面板信号槽连接设置完成")
        
    def _on_output_received(self, output):
        """终端输出回调函数 - 在非UI线程中调用"""
        # 使用信号将输出传递到UI线程
        self.output_signal.output_received.emit(output)
        
    def start_terminal(self):
        """启动终端"""
        try:
            logger.info("启动终端")
            # 不再显示"正在启动终端..."，避免与_handle_terminal_start_result中的信息重复
            # 在单独的线程中启动终端以避免阻塞UI
            thread = threading.Thread(target=self._start_terminal_thread, daemon=True)
            thread.start()
        except Exception as e:
            logger.error(f"启动终端失败: {e}")
            traceback.print_exc()
            
    def _start_terminal_thread(self):
        """在单独线程中启动终端"""
        try:
            success = self.terminal_manager.start_terminal()
            QTimer.singleShot(0, lambda: self._handle_terminal_start_result(success))
        except Exception as e:
            logger.error(f"终端启动线程执行失败: {e}")
            traceback.print_exc()
            
    def _handle_terminal_start_result(self, success):
        """处理终端启动结果"""
        if success:
            self.append_output("PowerShell终端已启动\n")
            logger.info("PowerShell终端已启动")
            # 获取初始目录并显示初始提示符
            QTimer.singleShot(800, self._show_initial_prompt)  # 增加延迟时间确保终端完全启动
        else:
            self.append_output("PowerShell终端启动失败\n")
            logger.error("PowerShell终端启动失败")
        
    def _show_initial_prompt(self):
        """显示初始提示符"""
        try:
            self.update_current_directory()
            # 确保目录不为空，如果为空则使用当前工作目录
            directory = self.current_directory if self.current_directory else os.getcwd()
            # 显示初始提示符
            prompt = f"PS {directory}> "
            self.append_output(prompt)
            logger.info(f"显示初始提示符: {prompt}")
        except Exception as e:
            logger.error(f"显示初始提示符失败: {e}")
            traceback.print_exc()
        
    def execute_command(self):
        """执行命令"""
        try:
            command = self.command_input.text().strip()
            if command:
                logger.info(f"执行命令: {command}")
                # 不再手动添加提示符和命令到输出区域，让PowerShell自己输出
                # 直接发送命令到终端
                try:
                    success = self.terminal_manager.send_input(command, add_newline=True)
                    if not success:
                        logger.warning(f"向终端发送命令失败: {command}")
                        # 如果发送失败，手动显示错误信息
                        self.append_output(f"命令执行失败: {command}\n")
                except Exception as e:
                    logger.error(f"向终端发送命令时出错: {e}")
                    traceback.print_exc()
                    # 显示错误信息
                    self.append_output(f"命令执行错误: {str(e)}\n")
                
                self.command_input.clear()
                
                # 如果是cd命令，更新目录
                if command.lower().startswith('cd '):
                    # 延迟更新目录，给终端一些时间处理命令
                    QTimer.singleShot(1000, self._update_directory_and_show_prompt)
                # 对于其他命令，也定期更新目录以确保准确性
                else:
                    QTimer.singleShot(500, self._update_directory_and_show_prompt)
            else:
                # 即使命令为空，也要刷新提示符
                self._update_directory_and_show_prompt()
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            traceback.print_exc()
            
    def _update_directory_and_show_prompt(self):
        """更新目录并显示新的提示符"""
        try:
            old_directory = self.current_directory
            self.update_current_directory()
            # 如果目录发生了变化，显示新的提示符
            if self.current_directory != old_directory:
                # 确保目录不为空，如果为空则使用当前工作目录
                directory = self.current_directory if self.current_directory else os.getcwd()
                prompt = f"PS {directory}> "
                self.append_output(prompt)
                logger.info(f"显示新提示符: {prompt}")
        except Exception as e:
            logger.error(f"更新目录并显示提示符失败: {e}")
            traceback.print_exc()
            
    def update_current_directory(self):
        """更新当前目录"""
        try:
            directory = self.terminal_manager.get_current_directory()
            if directory and directory != self.current_directory:
                self.current_directory = directory
                logger.info(f"当前目录更新为: {directory}")
        except Exception as e:
            logger.error(f"更新当前目录失败: {e}")
            traceback.print_exc()
            
    def append_output(self, output):
        """追加输出到显示区域"""
        try:
            if output:
                # 过滤掉重复的提示符输出
                filtered_output = self._filter_duplicate_prompts(output)
                if filtered_output:
                    # 确保输出以换行符结尾，实现自动换行
                    if not filtered_output.endswith('\n'):
                        filtered_output += '\n'
                    
                    # 处理ANSI颜色代码
                    self._append_colored_text(filtered_output)
                    
                    # 自动滚动到底部
                    scrollbar = self.output_display.verticalScrollBar()
                    if scrollbar:
                        scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            logger.error(f"追加输出失败: {e}")
            traceback.print_exc()
            
    def _filter_duplicate_prompts(self, output):
        """过滤重复的提示符输出"""
        # 过滤掉PowerShell自动输出的提示符，避免与我们手动添加的提示符重复
        lines = output.split('\n')
        filtered_lines = []
        
        for line in lines:
            # 检查是否为PowerShell提示符行（以"PS "开头并以">"结尾）
            if line.strip().startswith("PS ") and line.strip().endswith(">"):
                # 这可能是PowerShell自动输出的提示符，过滤掉
                continue
            # 检查是否为包含命令的PowerShell提示符行（以"PS "开头并包含命令）
            elif line.strip().startswith("PS ") and "> " in line.strip():
                # 这可能是PowerShell自动输出的提示符和命令，过滤掉
                continue
            # 过滤掉PowerShell的表头信息
            elif line.strip() in ["Path", "----"]:
                continue
            else:
                filtered_lines.append(line)
                
        return '\n'.join(filtered_lines)
    
    def _append_colored_text(self, text):
        """追加带颜色的文本到显示区域"""
        try:
            # 获取当前光标位置
            cursor = self.output_display.textCursor()
            cursor.movePosition(cursor.End)
            
            # 处理ANSI颜色代码
            formatted_text = self._process_ansi_colors(text, cursor)
            
            # 如果没有ANSI代码，直接插入文本
            if formatted_text is None:
                cursor.insertText(text)
                # 应用默认格式
                format = QTextCharFormat()
                format.setForeground(QColor("#d4d4d4"))
                format.setFontFamily(TERMINAL_FONT_FAMILY)
                format.setFontPointSize(self.terminal_font_size)
                cursor.movePosition(cursor.PreviousCharacter, cursor.KeepAnchor, len(text))
                cursor.setCharFormat(format)
            
            # 移动光标到末尾
            cursor.movePosition(cursor.End)
            self.output_display.setTextCursor(cursor)
        except Exception as e:
            # 如果颜色处理失败，直接添加文本并确保换行
            self.output_display.append(text.rstrip())
            
    def _process_ansi_colors(self, text, cursor):
        """处理ANSI颜色代码"""
        try:
            # 确保text是字符串类型
            if not isinstance(text, str):
                return None
                
            # ANSI转义序列模式
            ansi_pattern = re.compile(r'\x1b\[([0-9;]*)m')
            
            # 如果没有ANSI代码，返回None表示使用默认处理
            if not ansi_pattern.search(text):
                return None
                
            last_index = 0
            current_format = QTextCharFormat()
            current_format.setForeground(QColor("#d4d4d4"))
            current_format.setFontFamily(TERMINAL_FONT_FAMILY)
            current_format.setFontPointSize(self.terminal_font_size)
            
            for match in ansi_pattern.finditer(text):
                start, end = match.span()
                ansi_code = match.group(1)
                
                # 插入ANSI代码之前的部分
                if start > last_index:
                    segment = text[last_index:start]
                    cursor.insertText(segment, current_format)
                
                # 解析ANSI代码
                if ansi_code:
                    codes = ansi_code.split(';')
                    for code in codes:
                        if code.isdigit():
                            color_code = int(code)
                            # 重置格式
                            if color_code == 0:
                                current_format = QTextCharFormat()
                                current_format.setForeground(QColor("#d4d4d4"))
                                current_format.setFontFamily(TERMINAL_FONT_FAMILY)
                                current_format.setFontPointSize(self.terminal_font_size)
                            # 设置前景色
                            elif color_code in [30, 31, 32, 33, 34, 35, 36, 37, 90, 91, 92, 93, 94, 95, 96, 97]:
                                # ANSI颜色映射
                                ansi_colors = {
                                    30: QColor("#000000"),  # 黑色
                                    31: QColor("#FF5555"),  # 红色
                                    32: QColor("#50FA7B"),  # 绿色
                                    33: QColor("#F1FA8C"),  # 黄色
                                    34: QColor("#BD93F9"),  # 蓝色
                                    35: QColor("#FF79C6"),  # 洋红色
                                    36: QColor("#8BE9FD"),  # 青色
                                    37: QColor("#F8F8F2"),  # 白色
                                    90: QColor("#6272A4"),  # 亮黑色
                                    91: QColor("#FF6E6E"),  # 亮红色
                                    92: QColor("#69FF94"),  # 亮绿色
                                    93: QColor("#FFFFA5"),  # 亮黄色
                                    94: QColor("#D6ACFF"),  # 亮蓝色
                                    95: QColor("#FF92DF"),  # 亮洋红色
                                    96: QColor("#A4FFFF"),  # 亮青色
                                    97: QColor("#FFFFFF"),  # 亮白色
                                }
                                current_format.setForeground(ansi_colors[color_code])
                
                last_index = end
                
            # 插入剩余部分
            if last_index < len(text):
                segment = text[last_index:]
                cursor.insertText(segment, current_format)
                
            return True
        except Exception as e:
            logger.error(f"处理ANSI颜色代码失败: {e}")
            return None