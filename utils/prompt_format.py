#!/usr/bin/env python3
"""
文件自动换行工具
用法: python format_text.py input.txt [output.txt] [--width=100] [--markdown]

默认功能：
1. 自动识别 \n 为换行
2. 将 **text** 识别为 Markdown 加粗
3. 自动换行到指定宽度
"""

import sys
import re
import json
from pathlib import Path
from typing import Optional, List

class TextFormatter:
    """文本格式化器"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取文件内容
        self.content = file_path.read_text(encoding='utf-8')
        self.is_json = self._detect_json()
    
    def _detect_json(self) -> bool:
        """检测是否为 JSON 格式"""
        content = self.content.strip()
        if content.startswith('[') or content.startswith('{'):
            try:
                json.loads(content)
                return True
            except:
                pass
        return False
    
    def format_text(self, width: int = 100, to_markdown: bool = False) -> str:
        """
        格式化文本
        
        Args:
            width: 每行最大宽度
            to_markdown: 是否转换为 Markdown 格式
            
        Returns:
            格式化后的文本
        """
        if self.is_json:
            return self._format_json(width, to_markdown)
        else:
            return self._format_plain_text(width, to_markdown)
    
    def _format_json(self, width: int, to_markdown: bool) -> str:
        """格式化 JSON 内容"""
        try:
            data = json.loads(self.content)
            
            if isinstance(data, list) and len(data) > 0 and 'content' in data[0]:
                # 处理消息格式的 JSON
                result_lines = []
                for i, item in enumerate(data):
                    if isinstance(item, dict) and 'content' in item:
                        result_lines.append(f"--- 消息 {i+1} ---")
                        result_lines.append(f"角色: {item.get('role', 'unknown')}")
                        result_lines.append("内容:")
                        content = item.get('content', '')
                        
                        if to_markdown:
                            formatted_content = self._process_markdown(content, width)
                        else:
                            formatted_content = self._wrap_text(content, width)
                        
                        result_lines.append(formatted_content)
                        result_lines.append("")  # 空行分隔
                
                return '\n'.join(result_lines)
            else:
                # 普通 JSON，美化输出
                formatted = json.dumps(data, ensure_ascii=False, indent=2)
                if to_markdown:
                    formatted = f"```json\n{formatted}\n```"
                return formatted
                
        except json.JSONDecodeError as e:
            print(f"警告: JSON 解析失败，按普通文本处理: {e}")
            return self._format_plain_text(width, to_markdown)
    
    def _format_plain_text(self, width: int, to_markdown: bool) -> str:
        """格式化普通文本"""
        if to_markdown:
            return self._to_markdown(width)
        else:
            return self._wrap_text(self.content, width)
    
    def _to_markdown(self, width: int) -> str:
        """转换为 Markdown 格式"""
        lines = self.content.split('\n')
        result_lines = []
        
        for line in lines:
            # 处理转义字符
            line = self._unescape(line)
            
            # 处理内联格式
            line = self._process_inline_formatting(line)
            
            # 检测标题
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                result_lines.append(line)
                continue
            
            # 检测列表项
            if re.match(r'^\s*[-*+•]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                result_lines.append(line)
                continue
            
            # 检测代码块
            if line.strip().startswith('```') or line.strip().startswith('`'):
                result_lines.append(line)
                continue
            
            # 普通文本，自动换行
            if len(line) <= width:
                result_lines.append(line)
            else:
                wrapped = self._smart_wrap(line, width)
                result_lines.extend(wrapped)
        
        return '\n'.join(result_lines)
    
    def _wrap_text(self, text: str, width: int) -> str:
        """简单的文本换行"""
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            # 处理转义字符
            line = self._unescape(line)
            
            if len(line) <= width:
                result_lines.append(line)
            else:
                # 智能换行
                wrapped = self._smart_wrap(line, width)
                result_lines.extend(wrapped)
        
        return '\n'.join(result_lines)
    
    def _unescape(self, text: str) -> str:
        """处理转义字符"""
        # 处理 \n
        text = text.replace('\\n', '\n')
        # 处理 \t
        text = text.replace('\\t', '\t')
        # 处理 \\
        text = text.replace('\\\\', '\\')
        return text
    
    def _process_inline_formatting(self, text: str) -> str:
        """处理内联格式"""
        # 处理加粗：**bold**
        text = re.sub(r'\*\*(.+?)\*\*', r'**\1**', text)
        # 处理斜体：*italic*
        text = re.sub(r'\*(?!\*)(.+?)(?<!\*)\*', r'*\1*', text)
        return text
    
    def _smart_wrap(self, line: str, width: int) -> List[str]:
        """智能换行"""
        if len(line) <= width:
            return [line]
        
        result = []
        current = ""
        
        for char in line:
            if len(current) >= width and char in [' ', '，', '。', '；', '、', ',', '.', ';', '?', '!', '？', '！']:
                result.append(current.strip())
                current = char
            else:
                current += char
        
        if current:
            result.append(current.strip())
        
        return result
    
    def _process_markdown(self, text: str, width: int) -> str:
        """处理 Markdown 内容"""
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            # 处理转义字符
            line = self._unescape(line)
            
            # 处理内联格式
            line = self._process_inline_formatting(line)
            
            if len(line) <= width:
                result_lines.append(line)
            else:
                wrapped = self._smart_wrap(line, width)
                result_lines.extend(wrapped)
        
        return '\n'.join(result_lines)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python format_text.py 输入文件 [输出文件] [选项]")
        print("\n选项:")
        print("  --width=N    设置每行宽度（默认: 80")
        print("  --markdown   转换为 Markdown 格式")
        print("  --help       显示帮助")
        print("\n示例:")
        print("  python format_text.py input.txt")
        print("  python format_text.py input.txt output.txt")
        print("  python format_text.py input.txt --width=80")
        print("  python format_text.py input.txt --markdown")
        return
    
    # 解析参数
    input_file = None
    output_file = None
    width = 80
    to_markdown = True
    
    for arg in sys.argv[1:]:
        if arg == '--help':
            print(__doc__)
            return
        elif arg.startswith('--width='):
            try:
                width = int(arg.split('=')[1])
            except:
                print(f"错误: 无效的宽度参数: {arg}")
                return
        elif arg == '--markdown':
            to_markdown = True
        elif arg.startswith('--'):
            print(f"警告: 未知选项: {arg}")
        elif input_file is None:
            input_file = Path(arg)
        elif output_file is None:
            output_file = Path(arg)
        else:
            print(f"警告: 忽略多余的参数: {arg}")
    
    if input_file is None:
        print("错误: 请指定输入文件")
        return
    
    try:
        # 创建格式化器
        formatter = TextFormatter(input_file)
        
        # 格式化文本
        print(f"正在处理文件: {input_file}")
        if to_markdown:
            print("模式: Markdown 转换")
        print(f"行宽: {width} 字符")
        
        formatted_text = formatter.format_text(width=width, to_markdown=to_markdown)
        
        # 确定输出文件
        if output_file is None:
            if to_markdown:
                output_file = input_file.with_suffix('.md')
            else:
                output_file = input_file.with_name(f"{input_file.stem}_formatted{input_file.suffix}")
        
        # 保存文件
        output_file.write_text(formatted_text, encoding='utf-8')
        print(f"✅ 格式化完成，保存到: {output_file}")
        
        # 显示统计信息
        original_length = len(formatter.content)
        formatted_length = len(formatted_text)
        original_lines = len(formatter.content.split('\n'))
        formatted_lines = len(formatted_text.split('\n'))
        
        print(f"原始: {original_length} 字符, {original_lines} 行")
        print(f"结果: {formatted_length} 字符, {formatted_lines} 行")
        
        # 预览
        print("\n=== 预览（前10行）===")
        for i, line in enumerate(formatted_text.split('\n')[:10]):
            line_num = f"{i+1:3d}:"
            # 截断过长的行用于预览
            if len(line) > 100:
                preview_line = line[:97] + "..."
            else:
                preview_line = line
            print(f"{line_num} {preview_line}")
        
        if formatted_lines > 10:
            print("...")
            
    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()