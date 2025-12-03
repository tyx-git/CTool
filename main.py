import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 添加日志管理器导入
from core.logger import get_log_manager

try:
    from PyQt5.QtWidgets import QApplication
except Exception as e:
    traceback.print_exc()
    sys.exit(1)

try:
    from ui.main_window import MainWindow
except Exception as e:
    traceback.print_exc()
    sys.exit(1)

# 获取日志记录器
logger = get_log_manager().get_logger('main')

def main():
    """主函数"""
    try:
        logger.info("应用程序启动")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info("应用程序窗口显示")
        result = app.exec_()
        logger.info("应用程序退出")
        return result
    except Exception as e:
        logger.error(f"主函数执行失败: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)