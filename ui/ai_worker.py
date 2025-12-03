from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import threading


class AIWorker(QThread):
    """AI 流式输出工作线程（从 main_window.py 提取成独立组件）。"""

    result_ready = pyqtSignal(dict)  # 结果信号
    stream_chunk = pyqtSignal(str)   # 流式片段信号

    def __init__(self, ai_manager, user_message, system_prompt, model_name):
        super().__init__()
        self.ai_manager = ai_manager
        self.user_message = user_message
        self.system_prompt = system_prompt
        self.model_name = model_name
        self._abort_event = threading.Event()

    def _get_current_timestamp(self):
        return datetime.now().isoformat()

    def run(self):
        """执行 AI 请求，通过 AIManager 流式生成器输出。"""
        try:
            full_response = ""
            for chunk in self.ai_manager.stream_chat(
                self.user_message,
                self.system_prompt,
                model_name=self.model_name,
                stop_check=lambda: self._abort_event.is_set(),
                retries=2,
            ):
                if chunk:
                    full_response += chunk
                    self.stream_chunk.emit(chunk)
            # 完成后通知结果
            self.result_ready.emit({
                'success': True,
                'raw_response': full_response,
                'timestamp': self._get_current_timestamp()
            })
        except Exception as e:
            self.result_ready.emit({'success': False, 'error': str(e)})

    def request_abort(self):
        """请求中止流式输出。"""
        self._abort_event.set()
