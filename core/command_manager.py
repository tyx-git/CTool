import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 使用新的日志管理器
from core.logger import get_log_manager

class CommandManager:
    '''命令管理器'''
    def __init__(self, db_path: Optional[str] = None):
        '''初始化命令管理器'''
        root_dir = self.find_root_dir()
        # 使用新的日志管理器
        self.logger = get_log_manager().get_logger('command_manager')

        if db_path is None:
            self.db_path = root_dir / 'data/commands.db'
        else:
            self.db_path = Path(db_path)
        self.logger.info(f'数据库路径确定: {self.db_path}')
        self._init_database()

    def find_root_dir(self) -> Path:
        '''
        搜寻根目录
        
        Returns:
            Path对象(pathlib)
        '''

        current_dir = Path(__file__).parent
        max_depth = 5

        # 找到包含data的根目录
        for _ in range(max_depth):
            if (current_dir / 'data').exists() or current_dir.parent == current_dir:
                return current_dir
            current_dir = current_dir.parent

        self.logger.warning(f"未找到data目录! 当前目录为：{current_dir}")
        return current_dir

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """初始化数据库表结构"""

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_text TEXT NOT NULL,
                    description TEXT,
                    working_directory TEXT,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )'''
            )
            # 创建索引以提高搜索性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_text ON commands(command_text)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_description ON commands(description)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_count ON commands(usage_count)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_create_time ON commands(create_time)')
            
            conn.commit()
            conn.close()
            self.logger.info("数据库表结构初始化完成")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        if row is None:
            return {}
        return dict(row)

    def add_command(self, command_text:str, description:str='',
                    working_dir:str='') -> int:
        '''
        增加命令
        
        Args:
            command_text:命令文本
            description:命令描述
            working_dir:工作目录

        Returns:
            id:int
        '''
        try:
            if not command_text:
                self.logger.error(f"命令文本为空!")
                return -1
            
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO commands 
                (command_text, description, working_directory)
                VALUES (?, ?, ?)
            ''', (command_text, description, working_dir))
            cmd_id = cursor.lastrowid or -1
            conn.commit()
            conn.close()
            self.logger.info(f"命令添加成功，ID: {cmd_id}")
            return cmd_id
        except Exception as e:
            self.logger.error(f"添加命令失败: {e}")
            return -1
    
    def get_command(self, command_id:int) -> Optional[Dict[str, Any]]:
        '''
        获取命令
        
        Args:
            command_id:命令id

        Returns:
            命令字典, 不存在则返回None
        '''
        try:
            if command_id is None:
                self.logger.error("id为空!")
                return None
            
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM commands WHERE id = ?
            ''',(command_id,))
            command = cursor.fetchone()
            conn.close()
            result = self._row_to_dict(command) if command else None
            if result:
                self.logger.info(f"获取命令成功，ID: {command_id}")
            else:
                self.logger.warning(f"命令不存在，ID: {command_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"获取命令失败:{e}")
            return None

    def del_command(self, command_id:int) -> bool:
        '''
        删除命令
        
        Args:
            command_id:命令id

        Returns:
            是否删除成功
        '''
        try:
            if command_id is None:
                self.logger.error("id为空!")
                return False
            
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM commands WHERE id = ?
            ''',(command_id,))
            
            is_success = cursor.rowcount > 0
            conn.commit()
            conn.close()

            if is_success:
                self.logger.info(f"删除命令：{command_id}成功!")
            else:
                self.logger.warning(f"删除命令：{command_id}失败!")
            
            return is_success

        except Exception as e:
            self.logger.error(f"删除命令失败:{e}")
            return False
            
    def update_command(self, command_id:int, **kwargs) -> bool:
        '''
        更新命令表
        
        Args:
            command_id:命令id
            **kwargs:需要更新的参数
        
        Returns:
            是否成功更新
        '''
        valid_fields = [
            'command_text',
            'description',
            'working_directory'
        ]

        if not kwargs:
            self.logger.warning(f"没有需要更新的字段!")
            return False
        
        to_updates = {}
        for key, value in kwargs.items():
            if key in valid_fields:
                to_updates[key] = value
                
        if not to_updates:
            self.logger.warning(f"没有有效的更新字段!")
            return False
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            set_clause = ','.join([f"{key} = ?" for key in to_updates.keys()])
            set_clause += ', update_time = ?' 

            values = list(to_updates.values())
            values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            values.append(command_id)

            cursor.execute(f'''
                UPDATE commands SET {set_clause} WHERE id = ?
            ''', values)
            
            is_success = cursor.rowcount > 0
            conn.commit()
            conn.close()

            if is_success:
                self.logger.info(f"更新命令：{command_id}成功!")
            else:
                self.logger.warning(f"命令：{command_id}不存在!")
            
            return is_success

        except Exception as e:
            self.logger.error(f"更新命令：{command_id}失败: {e}")
            return False

    def search_command(self, keyword:str, limit:int = 50) -> List[Dict[str, Any]]:
        '''
        搜索命令
        
        Args:
            keyword:关键词
            limit:限制返回多少条

        Returns:
            匹配到的命令列表
        '''
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT *, 
                       CASE 
                           WHEN command_text = ? THEN 1000         -- 命令文本完全匹配
                           WHEN command_text LIKE ? || '%' THEN 100 -- 命令文本开头匹配
                           WHEN command_text LIKE ? THEN 50        -- 命令文本包含匹配
                           WHEN description LIKE ? || '%' THEN 10  -- 描述开头匹配
                           WHEN description LIKE ? THEN 5          -- 描述包含匹配
                           ELSE 0
                       END as match_score
                FROM commands 
                WHERE command_text LIKE ? OR description LIKE ?
                ORDER BY match_score DESC, usage_count DESC, create_time DESC
                LIMIT ?
            ''', (keyword, keyword, '%' + keyword + '%', keyword, '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', limit))

            commands = [self._row_to_dict(command) for command in cursor.fetchall()]
            conn.close()
            self.logger.info(f"搜索'{keyword}', 找到'{len(commands)}条记录!'")
            return commands
        except Exception as e:
            self.logger.error(f"搜索命令失败, keyword={keyword}, limit={limit}: {e}")
            return []

    def increment_command_usecounts(self, command_id:int) -> bool:
        '''
        增加某命令使用次数

        Args:
            command_id:命令id

        Returns:
            是否更新成功
        '''
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE commands 
                SET usage_count = usage_count + 1 
                WHERE id = ?
            ''', (command_id,))
            
            is_success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            if is_success:
                self.logger.info(f"增加命令使用次数成功，ID: {command_id}")
            else:
                self.logger.warning(f"增加命令使用次数失败，ID: {command_id}")
            return is_success
                
        except Exception as e:
            self.logger.error(f"增加命令使用次数失败 ID={command_id}: {e}")
            return False

    def get_all_commands(self, limit:int = 100) -> List[Dict[str, Any]]:
        '''
        获取所有命令
        
        Args:
            limit:限制返回多少条
        
        Returns:
            命令列表
        '''
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM commands 
                ORDER BY create_time DESC 
                LIMIT ?
            ''',(limit,))
            
            commands = [self._row_to_dict(row) for row in cursor.fetchall()]
            conn.close()
            self.logger.info(f"获取到{len(commands)}条命令")
            return commands
        except Exception as e:
            self.logger.error(f"获取命令失败: {e}")
            return []

    def get_recent_commands(self, limit:int = 100) -> List[Dict[str, Any]]:
        '''
        获取最近添加的命令
        
        Args:
            limit:限制返回数目
            
        Returns:
            命令列表
        '''
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM commands 
                ORDER BY create_time DESC 
                LIMIT ?
            ''', (limit,))

            commands = [self._row_to_dict(row) for row in cursor.fetchall()]
            conn.close()
            self.logger.info(f"获取到{len(commands)}条最近命令")
            return commands
        except Exception as e:
            self.logger.error(f"获取最近命令失败: {e}")
            return []

    def get_popular_commands(self, limit:int = 100) -> List[Dict[str, Any]]:
        """
        获取最常用的命令
        
        Args:
            limit: 返回结果数量限制
        
        Returns:
            常用命令列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM commands 
                ORDER BY usage_count DESC, create_time DESC 
                LIMIT ?
            ''', (limit,))
            
            commands = [self._row_to_dict(row) for row in cursor.fetchall()]
            conn.close()
            self.logger.info(f"获取到{len(commands)}条常用命令")
            return commands
                
        except Exception as e:
            self.logger.error(f"获取常用命令失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            stats = {}
            
            cursor.execute('SELECT COUNT(*) as total FROM commands')
            result = cursor.fetchone()
            stats['total_commands'] = result['total'] if result else 0
            
            cursor.execute('''
                SELECT command_text, usage_count 
                FROM commands 
                ORDER BY usage_count DESC 
                LIMIT 5
            ''')
            stats['top_commands'] = [self._row_to_dict(row) for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM commands 
                WHERE date(create_time) = date('now')
            ''')
            result = cursor.fetchone()
            stats['today_added'] = result['count'] if result else 0
            
            cursor.execute('SELECT SUM(usage_count) as total_usage FROM commands')
            result = cursor.fetchone()
            stats['total_usage'] = result['total_usage'] or 0
            
            conn.close()
            self.logger.info("获取统计信息完成")
            return stats
                
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}

def get_command_manager(db_path: Optional[str] = None) -> CommandManager:
    '''获取命令管理器实例'''
    return CommandManager(db_path)