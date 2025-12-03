import logging
from datetime import datetime
from openai import OpenAI
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from config.config_manager import ConfigManager

# 使用新的日志管理器
from core.logger import get_log_manager

class AIManager:
    '''AI管理器'''
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化 AI 管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        # 使用新的日志管理器
        self.logger = get_log_manager().get_logger('ai_manager')
        self.config_manager = config_manager or ConfigManager()
        self.api_config = self._load_api_config()

        if not self._validate_config():
            raise ValueError("AI 配置验证失败，请检查 api.json")

        self.client = self._init_openai_client()
        self.conversation_history = []
        self.max_history_length = 50

    def _load_api_config(self) -> Dict[str, Any]:
        """加载 API 配置"""
        try:
            api_data = self.config_manager.get_api()
            return {
                'api_key': api_data.get('api_key'),
                'api_url': api_data.get('api_url'),  
                'model': api_data.get('model'),
                'temperature': api_data.get('temperature'),
                'max_tokens': api_data.get('max_tokens'),
                'timeout': api_data.get('timeout')
            }
        except Exception as e:
            self.logger.error(f"加载 API 配置失败: {e}")
            return {}
            
    def _validate_config(self) -> bool:
        """验证配置完整性"""
        if not self.api_config.get('api_key'):
            self.logger.error("DeepSeek API Key 未配置")
            return False
        
        required_fields = ['api_url', 'model']  
        for field in required_fields:
            if not self.api_config.get(field):
                self.logger.error(f"缺少必要配置: {field}")
                return False
        
        self.logger.info("AI 配置验证通过")
        return True

    def _init_openai_client(self) -> OpenAI:
        """初始化 OpenAI 客户端"""
        try:
            # 修复OpenAI客户端初始化参数
            client = OpenAI(
                api_key=self.api_config['api_key'],
                base_url=self.api_config['api_url']  # 使用base_url而不是api_url
            )
            self.logger.info("OpenAI 客户端初始化成功")
            return client
        except Exception as e:
            self.logger.error(f"初始化 OpenAI 客户端失败: {e}")
            raise

    def _call_ai_api_stream(self, message: List[Dict[str, str]], system_prompt: str, callback: Callable[[str], None]) -> Optional[str]:
        '''
        流式调用ai助手
        
        Args:
            message: 消息列表
            system_prompt: 系统提示词
            callback: 流式数据回调函数
            
        Returns:
            AI 回复内容完整文本
        '''
        try:
            full_message = []

            if system_prompt:
                full_message.append({
                    'role': 'system',
                    'content': system_prompt
                })

            full_message.extend(self.conversation_history)
            full_message.extend(message)  

            response = self.client.chat.completions.create(
                model=self.api_config['model'],
                messages=full_message,
                temperature=self.api_config.get('temperature', 0.7),
                max_tokens=self.api_config.get('max_tokens', 2000),
                stream=True  # 启用流式传输
            )
            
            full_response = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # 调用回调函数传递流式数据
                    if callback:
                        callback(content)
            
            return full_response
            
        except Exception as e:
            self.logger.error(f"API 流式调用失败: {e}")
            return None

    def _add_to_conversation_history(self, role: str, content: str):
        """
        添加消息到对话历史
        
        Args:
            role: 角色 ('user' 或 'assistant')
            content: 消息内容
        """
        self.conversation_history.append({
            'role': role,
            'content': content
        })
        
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]

    def chat_stream(self, user_input: str, system_prompt: str, callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        流式对话方法
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            callback: 流式数据回调函数
            
        Returns:
            包含原始回复和解析后内容的字典
        """
        try:
            message = [{
                'role': 'user',
                'content': user_input
            }]

            response = self._call_ai_api_stream(message, system_prompt, callback)

            if response is not None:
                self._add_to_conversation_history('user', user_input)
                self._add_to_conversation_history('assistant', response)  

                self.logger.info(f"AI 流式对话完成，用户输入: {user_input[:20]}...")

                return {
                    'success': True,
                    'raw_response': response,
                    'timestamp': self._get_current_timestamp()
                }
            else:
                self.logger.error("API 返回空响应")
                return {
                    'success': False,
                    'error': "AI 助手暂时无法响应，请稍后再试。"
                }
                
        except Exception as e:
            self.logger.error(f"流式对话处理失败: {e}")
            return {
                'success': False,
                'error': f"对话处理失败: {str(e)}"
            }

    def _get_current_timestamp(self) -> str: 
        '''获取当前时间戳'''
        return datetime.now().isoformat()
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
        self.logger.info("对话已清空!")

    def get_conversation_history(self) -> List[Dict[str, Any]]: 
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def set_max_history_length(self, max_length: int):
        '''
        设置最大历史长度

        Args:
            max_length: 最大长度
        '''
        self.max_history_length = max(10, max_length)
        self.logger.info(f"最大历史记录长度设置为: {self.max_history_length}")

    def get_conversation_statistics(self) -> Dict[str, Any]:
        '''
        获取对话历史统计信息

        Returns:
            统计字典
        '''
        user_messages = len([msg for msg in self.conversation_history if msg['role'] == 'user'])
        assistant_messages = len([msg for msg in self.conversation_history if msg['role'] == 'assistant'])  # 修正拼写

        return {
            'total_messages': len(self.conversation_history),
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,  # 修正键名
            'max_history_length': self.max_history_length,
            'remaining_capacity': self.max_history_length - len(self.conversation_history)
        }

def get_ai_assistant(config_manager: Optional[ConfigManager] = None) -> AIManager:  # 修正函数名拼写
    """获取 AI 助手实例"""
    return AIManager(config_manager)