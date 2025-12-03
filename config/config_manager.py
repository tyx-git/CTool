import json
import logging
from threading import Lock
from pathlib import Path
from typing import Any, Dict, List, Tuple
import traceback
import sys

# 使用新的日志管理器设置方法
from core.logger import get_log_manager, set_config_manager

class ConfigManager:
    '''配置管理器'''
    _lock = Lock() # 进程锁
    _instance = None # 实例化对象
    _config = {} # 配置列表
    _initialized = False # 是否初始化

    def __new__(cls):
        # 不在__new__方法中使用锁，避免死锁
        if cls._instance is None:
            cls._instance = super(ConfigManager,cls).__new__(cls)
        return cls._instance

    def __init__(self):
        '''初始化配置管理器'''
        # 使用新的日志管理器
        self.logger = get_log_manager().get_logger('config_manager')
        # 设置全局配置管理器引用以避免循环导入
        set_config_manager(self)
        
        # 使用锁机制，但避免死锁
        if not self._initialized:
            self.logger.info("配置管理器初始化")
            self.root_dir = self.find_root_dir()
            self.config_dir = self.root_dir / 'config'
            self._load_all_config()
            self._initialized = True
            self.logger.info("配置管理器初始化完成")

    def find_root_dir(self) -> Path:
        '''
        搜寻根目录
        
        Returns:
            Path对象(pathlib)
        '''
        self.logger.info("查找根目录")
        current_dir = Path(__file__).parent
        max_depth = 5

        # 找到包含config的根目录
        for _ in range(max_depth):
            if (current_dir / 'config').exists() or current_dir.parent == current_dir:
                self.logger.info(f"根目录找到: {current_dir}")
                return current_dir
            current_dir = current_dir.parent

        self.logger.warning(f"未找到config目录! 当前目录为：{current_dir}")
        return current_dir
    
    def _load_config(self,file_path:Path) -> Dict[str,Any]:
        '''
        加载单个配置文件
        
        Args:
            file_path: 配置文件路径

        Returns:
            配置列表

        '''
        # 不在_load_config方法中使用锁，避免死锁
        # 因为这个方法已经在_load_all_config的锁中调用了
        try:
            if not file_path.exists():
                self.logger.error(f"配置文件路径出错: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.logger.info(f"配置文件加载成功: {file_path}")
            return config
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件解码失败：{e}")
            return {}
        except Exception as e:
            self.logger.error(f"配置文件加载失败：{e}")
            return {}

    def _load_all_config(self):
        '''加载所有配置文件'''
        self.logger.info("加载所有配置文件")
        # 在_load_all_config方法中使用锁
        with self._lock:
            self.config_dir.mkdir(exist_ok = True)

            config_files = [
                'app.json',
                'api.json',
                'search.json',
                'windows.json'
            ]

            for config_file in config_files:
                file_path = self.config_dir / config_file
                file_config = self._load_config(file_path)
                self._config.update(file_config)

            self.logger.info("所有配置文件加载完成!")

    def get_config(self, key: str, default: Any = None,
                   category: str | None = None, 
                   subcategory: str | None = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值（如果配置不存在）
            category: 配置类别（如 'windows', 'app' 等）
            subcategory: 子类别（如 'main_window', 'layout' 等）
        
        Returns:
            配置值或默认值
        """
        with self._lock:
            try:
                if category and subcategory:
                    # 安全地访问嵌套字典
                    category_dict = self._config.get(category, {})
                    subcategory_dict = category_dict.get(subcategory, {})
                    result = subcategory_dict.get(key, default)
                    return result
                elif category:
                    category_dict = self._config.get(category, {})
                    result = category_dict.get(key, default)
                    return result
                else:
                    if key in self._config:
                        result = self._config[key]
                        return result
                    for category_config in self._config.values():
                        if isinstance(category_config, dict) and key in category_config:
                            result = category_config[key]
                            return result
                    return default
            except Exception as e:
                self.logger.error(f"获取配置失败 key={key}, category={category}, subcategory={subcategory}: {e}")
                return default

    def get_category(self, category:str) -> Dict[str, Any]:
        '''
        获取整个配置细节

        Args:
            category: 类别名

        Returns:
            字典副本(防止其他代码对配置的修改)
        '''
        with self._lock:
            return self._config.get(category, {}).copy()

    def get_api(self) -> Dict[str, Any]:
        '''获取api配置'''
        return self.get_category('api')
    
    def get_app(self) -> Dict[str, Any]:
        '''获取app配置'''
        return self.get_category('app')
    
    def get_search(self) -> Dict[str, Any]:
        '''获取search配置'''
        return self.get_category('search')
    
    def get_windows(self) -> Dict[str, Any]:
        '''获取windows配置'''
        return self.get_category('windows')
    
    # 窗口配置的专用方法
    def get_main_window_config(self) -> Dict[str, Any]:
        '''获取主窗口配置'''
        with self._lock:
            return self._config.get('windows', {}).get('main_window', {}).copy()
    
    def get_layout_config(self) -> Dict[str, Any]:
        '''获取布局配置'''
        with self._lock:
            return self._config.get('windows', {}).get('layout', {}).copy()
    
    def get_splitter_states(self) -> Dict[str, Any]:
        '''获取分割条状态'''
        with self._lock:
            return self._config.get('windows', {}).get('splitter_states', {}).copy()
    
    def get_ui_state(self) -> Dict[str, Any]:
        '''获取UI状态'''
        with self._lock:
            return self._config.get('windows', {}).get('ui_state', {}).copy()
    
    def get_terminal_config(self) -> Dict[str, Any]:
        '''获取终端配置'''
        with self._lock:
            return self._config.get('windows', {}).get('terminal', {}).copy()
    
    def get_ai_assistant_config(self) -> Dict[str, Any]:
        '''获取AI助手配置'''
        with self._lock:
            return self._config.get('windows', {}).get('ai_assistant', {}).copy()
    
    def get_command_panel_config(self) -> Dict[str, Any]:
        '''获取命令面板配置'''
        with self._lock:
            return self._config.get('windows', {}).get('command_panel', {}).copy()
    
    def set_config(self, key: str, value: Any, 
                   category: str | None = None,
                   subcategory: str | None = None):
        '''
        设置配置值

        Args:
            key: 键名
            value: 值
            category: 类别名
            subcategory: 子类别名
        '''
        # 不在set_config方法中使用锁，避免死锁
        # 因为这个方法可能在已经持有锁的情况下被调用
        try:
            if category and subcategory:
                if category not in self._config:
                    self.logger.warning(f"{category}不属于配置项!")
                    # 初始化category
                    self._config[category] = {}
                if subcategory not in self._config[category]:
                    self.logger.warning(f"{subcategory}不属于配置项1")
                    # 初始化subcategory
                    self._config[category][subcategory] = {}
                self._config[category][subcategory][key] = value
            elif category:
                if category not in self._config:
                    self.logger.warning(f"{category}不属于配置项!")
                    # 初始化category
                    self._config[category] = {}
                self._config[category][key] = value
            else:
                self.logger.warning(f"当前并无配置键名{key}")
                
        except Exception as e:
            self.logger.error(f"设置配置失败 key={key}, value={value}, category={category}, subcategory={subcategory}: {e}")

    def save_file(self, category:str|None = None,
                  filename:str|None = None):
        '''
        保存配置项到文件

        Args:
            category: 要保存的配置类别(如果为None则保存所有配置)
            filename: 目标文件名(如果为None则使用类别名)
        '''

        config_files = [
            'app.json',
            'api.json',
            'search.json',
            'windows.json'
        ]

        # 不在save_file方法中使用锁，避免死锁
        # 因为这个方法可能在已经持有锁的情况下被调用
        try:
            if category:
                if filename is None:
                    filename = f"{category}.json"
                # 不使用get_category方法，直接访问_config以避免死锁
                to_save = {
                    category: self._config.get(category, {}).copy()
                }
                file_path = self.config_dir / filename

                with open(file_path, 'w', encoding='utf-8') as f: 
                    json.dump(to_save, f, ensure_ascii=False, indent=2) 

                self.logger.info(f'{category}配置保存成功!')
            else:
                for file in config_files:
                    category_name = file.replace('.json', '')
                    self.save_file(category=category_name, filename=file)

        except Exception as e:
            self.logger.error(f"保存配置失败!{e}")

    # 窗口配置保存方法
    def save_window_state(self, geometry: str, window_state: str, maximized: bool = False):
        '''
        保存窗口状态

        Args:
            geometry: 窗口几何信息
            window_state: 窗口状态
            maximized: 是否最大化
        '''
        with self._lock:
            try:
                self.set_config('geometry', geometry, 'windows', 'main_window')
                self.set_config('window_state', window_state, 'windows', 'main_window')
                self.set_config('maximized', maximized, 'windows', 'main_window')

                # 现在在这里保存文件，确保窗口状态被正确保存
                self.save_file('windows')
                self.logger.info("窗口状态保存成功")
            except Exception as e:
                self.logger.error(f"保存窗口状态出错：{e}")

    def save_splitter_sizes(self, main_splitter_sizes: List[int] | None = None, 
                       right_splitter_sizes: List[int] | None = None):
        '''
        保存分割条尺寸

        Args:
            main_splitter_sizes: 主分割条尺寸 [左侧宽度, 右侧宽度]
            right_splitter_sizes: 右侧分割条尺寸 [上方高度, 下方高度]
        '''
        with self._lock:
            try:
                if main_splitter_sizes is not None:
                    if len(main_splitter_sizes) >= 2:
                        self.set_config('main_splitter_sizes', main_splitter_sizes, 
                                    'windows', 'splitter_states')
                        self.set_config('left_panel_width', main_splitter_sizes[0], 
                                    'windows', 'layout')
                        self.set_config('right_panel_width', main_splitter_sizes[1], 
                                    'windows', 'layout')
                        self.set_config('main_splitter', ','.join(map(str,main_splitter_sizes)), 'windows', 'splitter_states')
                    else:
                        self.logger.warning(f"主分割条尺寸数组长度不足: {main_splitter_sizes}")
                
                if right_splitter_sizes is not None:
                    if len(right_splitter_sizes) >= 2:
                        self.set_config('right_splitter_sizes', right_splitter_sizes, 
                                    'windows', 'splitter_states')
                        self.set_config('search_panel_height', right_splitter_sizes[0], 
                                    'windows', 'layout')
                        self.set_config('terminal_panel_height', right_splitter_sizes[1], 
                                    'windows', 'layout')
                        self.set_config('right_splitter', ','.join(map(str,right_splitter_sizes)), 'windows', 'splitter_states')
                    else:
                        self.logger.warning(f"右侧分割条尺寸数组长度不足: {right_splitter_sizes}")

                # 只在这里保存文件，避免重复保存
                self.save_file('windows')
                self.logger.info("分割条尺寸保存成功")
                
            except Exception as e:
                self.logger.error(f"保存分割条尺寸出错：{e}")

    def save_ui_state(self, current_tab_index: int = 0, search_filter: str = "", 
                     command_sort_order: str = "name_asc", theme: str = "default", 
                     font_size: int = 12):
        '''
        保存UI状态

        Args:
            current_tab_index: 当前标签页索引
            search_filter: 搜索过滤器
            command_sort_order: 命令排序方式
            theme: 主题
            font_size: 字体大小
        '''
        with self._lock:
            try:
                self.set_config('current_tab_index', current_tab_index, 'windows', 'ui_state')
                self.set_config('search_filter', search_filter, 'windows', 'ui_state')
                self.set_config('command_sort_order', command_sort_order, 'windows', 'ui_state')
                self.set_config('theme', theme, 'windows', 'ui_state')
                self.set_config('font_size', font_size, 'windows', 'ui_state')
                
                self.save_file('windows')
                self.logger.info("UI状态保存成功")
            except Exception as e:
                self.logger.error(f"保存UI状态出错：{e}")

    def save_command_management_state(self, expanded: bool, width: int = 400):
        '''
        保存命令管理面板状态

        Args:
            expanded: 是否展开
            width: 面板宽度
        '''
        with self._lock:
            try:
                self.set_config('command_management_expanded', expanded, 'windows', 'layout')
                self.set_config('command_management_width', width, 'windows', 'layout')

                self.save_file('windows')
                self.logger.info("命令管理面板状态保存成功")
            except Exception as e:
                self.logger.error(f"保存命令管理面板状态出错：{e}")

    def get_window_geometry(self) -> Tuple[int, int, int, int]:
        '''
        获取窗口几何信息

        Returns:
            元组 (x, y, width, height)
        '''
        # 不在get_window_geometry方法中使用锁，避免死锁
        # 因为这个方法可能在初始化过程中被调用
        geometry_str = self.get_config('geometry', '', 'windows', 'main_window')
        if geometry_str:
            try:
                parts = geometry_str.split(',')
                if len(parts) == 4:
                    result = (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
                    return result
            except ValueError as e:
                self.logger.error(f"获取窗口几何信息失败!")
        return (100, 50, 1200, 800)

    def get_splitter_sizes(self, splitter_name: str) -> List[int]:
        '''
        获取分割条尺寸

        Args:
            splitter_name: 分割条名称

        Returns:
            尺寸列表
        '''
        # 不在get_splitter_sizes方法中使用锁，避免死锁
        # 因为这个方法可能在初始化过程中被调用
        sizes_str = self.get_config(splitter_name, '', 'windows', 'splitter_states')
        if sizes_str:
            try:
                return list(map(int, sizes_str.split(',')))
            except ValueError:
                self.logger.error(f"获取分割条尺寸失败!")
        
        if splitter_name == 'main_splitter':
            return [300, 900]
        elif splitter_name == 'right_splitter':
            return [480, 320]
        return []

    def is_command_management_expanded(self) -> bool:
        '''检查命令管理面板是否展开'''
        return self.get_config('command_management_expanded', False, 'windows', 'layout')

    def get_command_management_width(self) -> int:
        '''获取命令管理面板宽度'''
        return self.get_config('command_management_width', 400, 'windows', 'layout')

    def validate_config(self) -> bool:
        '''验证配置完整性'''
        with self._lock:
            config_files = [
                'app.json',
                'api.json',
                'search.json',
                'windows.json'
            ]

            for file in config_files:
                if not (self.config_dir / file).exists():
                    self.logger.error(f"配置文件{file}不存在!")
                    return False
                else:
                    category = file.replace('.json','')
                    if not self._config.get(category):
                        self.logger.error(f"配置文件{file}内容为空!")
                        return False
            self.logger.info("配置完整性验证完成!")
            return True
    
def get_config_manager() -> ConfigManager:
    return ConfigManager()