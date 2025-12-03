import logging
from datetime import datetime
import logging.handlers
from queue import Empty, Queue
import threading
import sys
import os
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List

# 全局配置管理器引用，用于避免循环导入
_config_manager = None

def set_config_manager(config_manager):
    """设置全局配置管理器引用"""
    global _config_manager
    _config_manager = config_manager

class LogManager:
    '''日志管理器'''

    _lock = threading.Lock()
    _instance = None

    log_level = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING
    }

    def __new__(cls):
        '''重写new方法'''
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        '''初始化日志管理器'''
        # 使用双检查锁定模式确保单例
        if not hasattr(self, 'initialized'):
            with self._lock:
                if not hasattr(self, 'initialized'):
                    self.initialized = True
                    # 初始化属性
                    self.loggers = {}
                    self.log_queue = Queue()
                    self.log_listeners = []
                    self.is_running = False
                    self.running_thread = None
                    self.log_config = {}
                    self.root_dir = None
                    # 延迟初始化配置，避免循环导入
                    self._initialized_config = False

    def _initialize_config(self):
        """延迟初始化配置"""
        global _config_manager
        if not self._initialized_config and _config_manager is not None:
            self.config_manager = _config_manager
            self.root_dir = self.config_manager.root_dir
            self.log_config = self._load_log_config()
            
            try:
                log_dir = self.root_dir / 'log'
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                print(f"创建日志目录失败: {e}")

            self._setup_logger()
            self._initialized_config = True

    def _load_log_config(self):
        '''加载所有日志配置'''
        default_config = {
            'level': 'INFO',
            'console_output': True,
            'file_output': True,
            'max_file_size': 10, 
            'backup_count': 5,
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'log_dir': 'log',
            'enable_monitoring': False,
            'monitor_buffer_size': 1000
        }
        
        # 从配置管理器获取日志配置
        try:
            if hasattr(self, 'config_manager') and self.config_manager is not None:
                app_config = self.config_manager.get_config('app', {})
                if isinstance(app_config, dict) and 'log' in app_config:
                    log_config = app_config['log']
                    # 合并默认配置和实际配置
                    merged_config = default_config.copy()
                    if isinstance(log_config, dict):
                        merged_config.update(log_config)
                    return merged_config
            return default_config
        except Exception as e:
            print(f"加载日志配置时出错: {e}")
            return default_config

    def _setup_logger(self):
        '''配置自定义日志管理器'''
        try:
            required_keys = ['level', 'log_format', 'date_format', 'log_dir']
            for key in required_keys:
                if key not in self.log_config:
                    raise ValueError(f"缺少必要的日志配置项: {key}")

            # 设置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(self.log_level.get(self.log_config['level'], logging.INFO))
            
            # 清除现有的处理器
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
                
            formatter = logging.Formatter(
                self.log_config['log_format'],
                datefmt=self.log_config['date_format']
            )

            if self.log_config.get('console_output', True):
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(self.log_level.get(self.log_config['level'], logging.INFO))
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)

            if self.log_config.get('file_output', True):
                log_dir = self.root_dir / self.log_config['log_dir']
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / 'app.log'
                
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=str(log_file),
                    maxBytes=self.log_config.get('max_file_size', 10) * 1024 * 1024,
                    backupCount=self.log_config.get('backup_count', 5),
                    encoding='utf-8'
                )
                file_handler.setLevel(self.log_level.get(self.log_config['level'], logging.INFO))
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)

            root_logger.propagate = False
            
        except (OSError, KeyError, ValueError) as e:
            print(f"配置日志记录器失败: {e}")
            logging.basicConfig(level=logging.INFO)

    def get_logger(self, name: str) -> Logger:
        '''获取指定名称的日志管理器'''
        # 确保配置已初始化
        self._initialize_config()
        
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]
        
    def set_logger_level(self, level: str):
        '''设置日志管理器级别'''
        # 确保配置已初始化
        self._initialize_config()
        
        if level not in self.log_level:
            raise ValueError(f"无效的日志级别: {level}。可选值: {list(self.log_level.keys())}")
        
        self.log_config['level'] = level
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level[level])

        for handler in root_logger.handlers:
            handler.setLevel(self.log_level[level])

    def start_monitoring(self):
        '''启动日志监控'''
        # 确保配置已初始化
        self._initialize_config()
        
        if self.is_running:
            return
        self.is_running = True
        self.running_thread = threading.Thread(
            target=self._running_logs,
            daemon=True
        )
        self.running_thread.start()
    
    def stop_monitoring(self):
        '''停止日志监控'''
        if not self.is_running:
            return
        self.is_running = False
        if self.running_thread:
            self.running_thread.join(timeout=5)
            self.running_thread = None

    def _running_logs(self):
        """监控日志（后台线程）"""
        # 确保配置已初始化
        self._initialize_config()
        
        buffer_size = self.log_config.get('monitor_buffer_size', 1000)
        log_buffer = []
        
        class LogHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                log_entry = self.format(record)
                self.log_queue.put(log_entry)

        handler = LogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter(self.log_config['log_format']))
        logging.getLogger().addHandler(handler)
        
        try:
            while self.is_running:
                try:
                    log_entry = self.log_queue.get(timeout=1.0)
                    log_buffer.append(log_entry)

                    if len(log_buffer) > buffer_size:
                        log_buffer = log_buffer[-buffer_size:]
                    for listener in self.log_listeners:
                        try:
                            listener(log_entry, log_buffer.copy())
                        except Exception as e:
                            print(f"日志监听器错误: {e}")
                            
                except Empty:
                    continue
                    
        except Exception as e:
            print(f"日志监控错误: {e}")
        finally:
            logging.getLogger().removeHandler(handler)
    
    def add_log_listener(self, listener_callback):
        """
        添加日志监听器
        """
        # 确保配置已初始化
        self._initialize_config()
        
        if listener_callback not in self.log_listeners:
            self.log_listeners.append(listener_callback)
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """
        获取所有日志文件信息
        
        Returns:
            日志文件信息列表
        """
        # 确保配置已初始化
        self._initialize_config()
        
        log_dir = self.root_dir / self.log_config['log_dir']
        log_files = []
        
        try:
            for file_path in log_dir.glob("*.log*"):
                stat = file_path.stat()
                log_files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
            
            log_files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            print(f"获取日志文件列表失败: {e}")
        
        return log_files
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Returns:
            统计信息字典
        """
        # 确保配置已初始化
        self._initialize_config()
        
        log_files = self.get_log_files()
        total_size = sum(f['size'] for f in log_files)
        
        return {
            'total_files': len(log_files),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'log_directory': self.log_config['log_dir'],
            'current_level': self.log_config['level']
        }
    
    def reload_config(self):
        """重新加载日志配置"""
        # 确保配置已初始化
        self._initialize_config()
        
        self.log_config = self._load_log_config()
        self._setup_logger()

def get_log_manager() -> LogManager:
    """获取日志管理器实例"""
    return LogManager()