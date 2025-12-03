from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QTextEdit, QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt


class AddCommandDialog(QDialog):
    """添加命令对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加命令")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()
        self.setup_connections()
        
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
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
    def setup_connections(self):
        """设置信号槽连接"""
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def get_command_data(self):
        """获取命令数据"""
        return {
            'command_text': self.command_input.text().strip(),
            'description': self.description_input.text().strip(),
            'working_directory': self.directory_input.text().strip()
        }
        
    def set_command_data(self, command_text="", description="", working_directory=""):
        """设置命令数据"""
        self.command_input.setText(command_text)
        self.description_input.setText(description)
        self.directory_input.setText(working_directory)