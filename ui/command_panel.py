from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QTextEdit, QFormLayout, QGroupBox)
from PyQt5.QtCore import pyqtSignal
import traceback
import sys


class CommandPanel(QWidget):
    """命令管理面板"""
    
    command_updated = pyqtSignal()  # 命令更新信号
    
    def __init__(self, command_manager):
        super().__init__()
        try:
            self.command_manager = command_manager
            self.current_command_id = None
            self.init_ui()
            self.setup_connections()
        except Exception as e:
            print(f"Error in CommandPanel.__init__: {e}")
            traceback.print_exc()
            raise
        
    def init_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建表单组
        form_group = QGroupBox("命令信息")
        form_layout = QFormLayout(form_group)
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("请输入命令")
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("请输入命令描述")
        
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("请输入工作目录")
        
        form_layout.addRow("命令:", self.command_input)
        form_layout.addRow("描述:", self.description_input)
        form_layout.addRow("目录:", self.directory_input)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        self.delete_button = QPushButton("删除")
        self.delete_button.setObjectName("delete-button")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
    def setup_connections(self):
        """设置信号槽连接"""
        try:
            self.save_button.clicked.connect(self.save_command)
            self.cancel_button.clicked.connect(self.hide_form)
            self.delete_button.clicked.connect(self.delete_command)
        except Exception as e:
            print(f"Error in CommandPanel.setup_connections: {e}")
            traceback.print_exc()
            raise
        
    def show_add_form(self):
        """显示添加命令表单"""
        self.current_command_id = None
        self.command_input.clear()
        self.description_input.clear()
        self.directory_input.clear()
        self.setVisible(True)
        
    def show_edit_form(self, command_id, command_text, description, working_dir):
        """显示编辑命令表单"""
        self.current_command_id = command_id
        self.command_input.setText(command_text)
        self.description_input.setText(description or "")
        self.directory_input.setText(working_dir or "")
        self.setVisible(True)
        
    def save_command(self):
        """保存命令"""
        command_text = self.command_input.text().strip()
        if not command_text:
            return
            
        description = self.description_input.text().strip()
        working_dir = self.directory_input.text().strip()
        
        if self.current_command_id is None:
            # 添加新命令
            self.command_manager.add_command(command_text, description, working_dir)
        else:
            # 更新现有命令
            self.command_manager.update_command(
                self.current_command_id,
                command_text=command_text,
                description=description,
                working_directory=working_dir
            )
            
        self.hide_form()
        self.command_updated.emit()
        
    def delete_command(self):
        """删除命令"""
        if self.current_command_id is not None:
            self.command_manager.del_command(self.current_command_id)
            self.hide_form()
            self.command_updated.emit()
            
    def hide_form(self):
        """隐藏表单"""
        self.setVisible(False)