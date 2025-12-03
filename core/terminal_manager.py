import os
import time
import threading
import subprocess
from queue import Queue, Empty
from pathlib import Path
from typing import List, Callable, Optional

# 使用新的日志管理器
from core.logger import get_log_manager

class TerminalManager:
    '''终端管理器'''

    def __init__(self, working_directory: Optional[str] = None,
                 output_callback: Optional[Callable] = None):
        """
        初始化终端管理器
        
        Args:
            working_directory: 初始工作目录
            output_callback: 输出回调函数
        """
        # 使用新的日志管理器
        self.logger = get_log_manager().get_logger('terminal_manager')
        self.logger.info("初始化终端管理器")
        self.working_directory = working_directory or os.getcwd()
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.output_callbacks: List[Callable] = []
        self.output_queue = Queue()
        self._stderr_thread: Optional[threading.Thread] = None
        self._stdout_thread: Optional[threading.Thread] = None
        self._callback_lock = threading.Lock()
        self._directory_lock = threading.Lock()

        if output_callback:
            self.output_callbacks.append(output_callback)
        self.logger.info("终端管理器初始化完成")
    
    def register_output_callback(self, callback: Optional[Callable] = None):
        """注册输出回调函数"""
        with self._callback_lock: 
            if callback and callback not in self.output_callbacks:
                self.output_callbacks.append(callback)
                self.logger.info("输出回调函数注册成功")
    
    def unregister_output_callback(self, callback: Optional[Callable] = None):
        """取消注册输出回调函数"""
        with self._callback_lock: 
            if callback and callback in self.output_callbacks:
                self.output_callbacks.remove(callback)
                self.logger.info("输出回调函数取消注册成功")
    
    def is_process_running(self) -> bool:
        """检查终端进程是否在运行"""
        return bool(self.is_running and self.process and self.process.poll() is None)

    def start_terminal(self) -> bool:
        """启动 PowerShell 终端进程"""
        self.logger.info("启动终端进程")
        try:
            # 使用系统默认的PowerShell 7
            powershell_path = r"C:\Program Files\PowerShell\7\pwsh.exe"
            if not os.path.exists(powershell_path):
                # 如果PowerShell 7不存在，使用系统默认的PowerShell
                powershell_path = "powershell.exe"
                
            self.logger.info(f"使用PowerShell路径: {powershell_path}")
            self.process = subprocess.Popen(
                [powershell_path, '-NoExit', '-Command', ''],
                cwd=self.working_directory,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.is_running = True
            self.logger.info("PowerShell进程已启动")

            self._stderr_thread = threading.Thread(
                target=self._read_stderr,
                daemon=True
            )
            self._stdout_thread = threading.Thread(
                target=self._read_stdout,
                daemon=True
            )

            self._stderr_thread.start()
            self._stdout_thread.start()
            self.logger.info("输出线程已启动")

            # 移除阻塞UI的sleep调用
            # time.sleep(0.5)

            self.logger.info("终端启动成功")
            return True
        except Exception as e:
            self.logger.error(f"启动终端失败: {e}")
            return False
    
    def _read_stdout(self):
        """读取标准输出"""
        self.logger.info("启动标准输出读取线程")
        while self.is_running and self.process:
            try:
                if self.process and self.process.stdout:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    if line.strip():
                        self.output_queue.put(('stdout', line))
                        with self._callback_lock: 
                            for callback in self.output_callbacks:
                                try:
                                    callback(line)
                                except Exception as e:
                                    self.logger.error(f"回调函数执行错误: {e}")
            except Exception as e:
                if self.is_running:
                    self.logger.error(f'读取输出出错：{e}')
                else:
                    self.logger.info(f'终端静默或未知错误：{e}')
                break  
        self.logger.info("标准输出读取线程结束")
    
    def _read_stderr(self):
        """读取标准错误"""
        self.logger.info("启动标准错误读取线程")
        while self.is_running and self.process:
            try:
                if self.process and self.process.stderr:
                    line = self.process.stderr.readline()
                    if line:
                        self.output_queue.put(('stderr', line))
                        with self._callback_lock: 
                            for callback in self.output_callbacks:
                                try:
                                    callback(line)
                                except Exception as e:
                                    self.logger.error(f"回调函数执行错误: {e}")
            except Exception as e:
                if self.is_running:
                    self.logger.error(f'读取错误信息出错：{e}')
                else:
                    self.logger.info(f'终端静默或未知错误：{e}')
                break  
        self.logger.info("标准错误读取线程结束")

    def send_input(self, input_text: str, add_newline: bool = False) -> bool:
        """
        向终端发送输入
        
        Args:
            input_text: 输入文本
            add_newline: 是否添加换行符（立即执行）- 关键改进：默认False符合"不自动执行"需求
            
        Returns:
            是否成功发送
        """
        try:
            if self.is_process_running() and self.process:
                text_to_send = input_text + ('\n' if add_newline else '')
                if self.process.stdin:
                    self.process.stdin.write(text_to_send)
                    self.process.stdin.flush()
                    self.logger.info(f"向终端发送输入: {input_text}")
                    return True
            self.logger.warning("终端未运行或进程不存在，无法发送输入")
            return False
        except Exception as e:
            self.logger.error(f"终端输入失败: {e}")
            return False

    def execute_command(self, command: str, working_dir: Optional[str] = None, 
                       execute_immediately: bool = True) -> bool:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            working_dir: 工作目录（可选）
            execute_immediately: 是否立即执行 - 关键改进: 默认True, 默认自动执行
            
        Returns:
            是否成功发送命令
        """
        try:
            if not self.is_process_running():
                self.logger.warning("终端未运行，无法执行命令")
                return False
                
            if working_dir and not os.path.exists(working_dir):
                self.logger.error(f'工作目录不存在: {working_dir}')
                return False
                
            full_command = command
            if working_dir:
                full_command = f'Set-Location "{working_dir}"; {command}'
                
            self.logger.info(f"执行命令: {full_command}")
            return self.send_input(full_command, add_newline=execute_immediately)
        except Exception as e:
            self.logger.error(f"终端命令执行失败: {e}")
            return False
 
    def change_directory(self, new_directory: str) -> bool:
        """改变工作目录"""
        if not os.path.exists(new_directory):
            self.logger.error(f'目录不存在: {new_directory}')
            return False
        
        try:
            if self.is_process_running():
                command = f'Set-Location "{new_directory}"'
                success = self.send_input(command, add_newline=True) 
                if success:
                    with self._directory_lock:
                        self.working_directory = new_directory
                    self.logger.info(f"目录切换成功: {new_directory}")
                return success
            self.logger.warning("终端未运行，无法切换目录")
            return False
        except Exception as e:
            self.logger.error(f'目录切换失败: {e}')
            return False
              
    def get_output(self, timeout: float = 0.1) -> List[str]:
        """获取终端输出"""
        outputs = []

        try:
            while True:
                item = self.output_queue.get(timeout=timeout)
                outputs.append(item[1])
        except Empty:
            pass

        return outputs

    def stop_terminal(self) -> bool:
        """停止终端"""
        try:
            self.logger.info("停止终端")
            self.is_running = False
            
            if self.process:
                try:
                    if self.process.stdin:
                        self.process.stdin.write("exit\n")
                        self.process.stdin.flush()
                except:
                    pass
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        try:
                            self.process.kill() 
                            self.process.wait()
                        except:
                            pass
                
                self.process = None
                self.logger.info("终端进程已停止")
            
            return True
        except Exception as e:
            self.logger.error(f"停止终端失败: {e}")
            return False
    
    def get_current_directory(self) -> str:
        """获取当前工作目录"""
        # 首先返回已知的工作目录
        with self._directory_lock:
            if self.working_directory:
                return self.working_directory

        # 如果终端未运行，返回当前工作目录
        if not self.is_process_running():
            with self._directory_lock:
                return self.working_directory or os.getcwd()
        
        try:
            # 发送Get-Location命令获取当前目录，使用PowerShell格式化输出
            self.send_input("(Get-Location).Path", add_newline=True)
            time.sleep(0.3)  # 给终端更多时间处理命令
            outputs = self.get_output(timeout=1.5)  # 增加超时时间
            if outputs:
                for output in outputs:
                    # 过滤掉提示符行，只获取实际的路径
                    if output.strip() and not (output.strip().startswith("PS ") and output.strip().endswith(">")):
                        # 移除可能的ANSI颜色代码和特殊字符
                        path = output.strip()
                        # 移除可能的PowerShell输出格式
                        if path and not path.startswith('----') and not path.lower().startswith('path') and path != "Path":
                            # 确保路径是有效的
                            if ':' in path and len(path) > 2:
                                # 标准化路径格式
                                normalized_path = os.path.normpath(path)
                                with self._directory_lock:
                                    self.working_directory = normalized_path
                                self.logger.info(f"通过Get-Location命令获取目录: {normalized_path}")
                                return normalized_path
        except Exception as e:
            self.logger.error(f"通过Get-Location命令获取目录时出错: {e}")

        # 如果所有方法都失败，返回已知的工作目录或当前目录
        with self._directory_lock:
            return self.working_directory or os.getcwd()

    def __del__(self):
        """析构函数，确保资源清理"""
        if hasattr(self, 'is_running') and self.is_running:
            self.stop_terminal()

def get_terminal_manager(working_dir: Optional[str] = None) -> TerminalManager:
    """获取终端管理器实例"""
    return TerminalManager(working_dir)