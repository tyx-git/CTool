import re
from typing import Dict, Any, List, Optional

class MarkdownParser:
    """
    Markdown解析器，用于解析和渲染Markdown格式的文本
    """
    
    def __init__(self):
        """初始化Markdown解析器"""
        pass
    
    def parse(self, markdown_text: str) -> str:
        """
        解析Markdown文本并转换为HTML格式
        
        Args:
            markdown_text (str): Markdown格式的文本
            
        Returns:
            str: 转换后的HTML格式文本
        """
        if not markdown_text:
            return ""
        
        # 处理文本，按顺序进行转换
        html_text = markdown_text
        
        # 处理代码块 ```language\ncontent\n```
        html_text = self._process_code_blocks(html_text)
        
        # 处理行内代码 `code`
        html_text = self._process_inline_code(html_text)
        
        # 处理粗体 **text** 或 __text__
        html_text = self._process_bold(html_text)
        
        # 处理斜体 *text* 或 _text_
        html_text = self._process_italic(html_text)
        
        # 处理标题 # Header
        html_text = self._process_headers(html_text)
        
        # 处理无序列表 - item
        html_text = self._process_unordered_lists(html_text)
        
        # 处理有序列表 1. item
        html_text = self._process_ordered_lists(html_text)
        
        # 处理链接 [text](url)
        html_text = self._process_links(html_text)
        
        # 处理换行符
        html_text = self._process_line_breaks(html_text)
        
        return html_text
    
    def _process_code_blocks(self, text: str) -> str:
        """处理代码块"""
        def replace_code_block(match):
            language = match.group(1) or ""
            code_content = match.group(2)
            # 转义HTML特殊字符
            code_content = self._escape_html(code_content)
            # 最大限度减少代码块的外边距和内边距
            return f'<pre style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px; padding: 3px; margin: 0px 0; font-family: Consolas, monospace; white-space: pre-wrap; line-height: 1.0;">{code_content}</pre>'
        
        # 匹配代码块 ```language\ncontent\n```
        return re.sub(r'```(\w+)?\n(.*?)\n```', replace_code_block, text, flags=re.DOTALL)
    
    def _process_inline_code(self, text: str) -> str:
        """处理行内代码"""
        def replace_inline_code(match):
            code_content = match.group(1)
            # 转义HTML特殊字符
            code_content = self._escape_html(code_content)
            return f'<code style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 2px; padding: 0px 1px; font-family: Consolas, monospace; line-height: 1.0;">{code_content}</code>'
        
        # 匹配行内代码 `code`
        return re.sub(r'`([^`]+)`', replace_inline_code, text)
    
    def _process_bold(self, text: str) -> str:
        """处理粗体文本"""
        # 匹配 **text** 或 __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        return text
    
    def _process_italic(self, text: str) -> str:
        """处理斜体文本"""
        # 匹配 *text* 或 _text_
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
        return text
    
    def _process_headers(self, text: str) -> str:
        """处理标题"""
        # 匹配标题 # Header, ## Header, ### Header 等，最小化边距
        text = re.sub(r'###### (.*?)\n', r'<h6 style="margin: 0px 0;">\1</h6>', text)
        text = re.sub(r'##### (.*?)\n', r'<h5 style="margin: 0px 0;">\1</h5>', text)
        text = re.sub(r'#### (.*?)\n', r'<h4 style="margin: 0px 0;">\1</h4>', text)
        text = re.sub(r'### (.*?)\n', r'<h3 style="margin: 0px 0;">\1</h3>', text)
        text = re.sub(r'## (.*?)\n', r'<h2 style="margin: 0px 0;">\1</h2>', text)
        text = re.sub(r'# (.*?)\n', r'<h1 style="margin: 0px 0;">\1</h1>', text)
        return text
    
    def _process_unordered_lists(self, text: str) -> str:
        """处理无序列表"""
        lines = text.split('\n')
        in_list = False
        result = []
        
        for line in lines:
            # 检查是否为列表项 (- item)
            match = re.match(r'^\s*[-*+]\s+(.*)', line)
            if match:
                item_content = match.group(1)
                if not in_list:
                    result.append('<ul style="margin: 0px 0; padding-left: 12px;">')
                    in_list = True
                result.append(f'<li style="margin: 0px 0;">{item_content}</li>')
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line)
        
        if in_list:
            result.append('</ul>')
            
        return '\n'.join(result)
    
    def _process_ordered_lists(self, text: str) -> str:
        """处理有序列表"""
        lines = text.split('\n')
        in_list = False
        result = []
        
        for line in lines:
            # 检查是否为有序列表项 (1. item)
            match = re.match(r'^\s*\d+\.\s+(.*)', line)
            if match:
                item_content = match.group(1)
                if not in_list:
                    result.append('<ol style="margin: 0px 0; padding-left: 12px;">')
                    in_list = True
                result.append(f'<li style="margin: 0px 0;">{item_content}</li>')
            else:
                if in_list:
                    result.append('</ol>')
                    in_list = False
                result.append(line)
        
        if in_list:
            result.append('</ol>')
            
        return '\n'.join(result)
    
    def _process_links(self, text: str) -> str:
        """处理链接"""
        # 匹配链接 [text](url)
        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color: #007bff; text-decoration: none;">\1</a>', text)
    
    def _process_line_breaks(self, text: str) -> str:
        """处理换行符"""
        # 使用简单的换行符处理方式，避免复杂的段落处理
        # 只将换行符替换为<br>标签
        return text.replace('\n', '<br>')
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))

def get_markdown_parser() -> MarkdownParser:
    """获取Markdown解析器实例"""
    return MarkdownParser()