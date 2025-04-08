#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ManZH - 示例命令查询模块
用于查询命令的示例用法
"""

import sys
import os
import subprocess
import tempfile
import io
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from .config_manager import load_config
from .translate import create_translation_service

def show_with_pager(content):
    """
    使用pager显示内容，支持滚动，使用Rich库渲染Markdown格式
    
    Args:
        content: 要显示的内容
    """
    # 使用Rich渲染Markdown
    rendered_content = render_markdown_with_rich(content)
    
    # 创建临时文件存储内容
    fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='manzh_example_')
    try:
        # 写入内容到临时文件
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        # 使用less命令显示内容，支持滚动，-R参数支持ANSI颜色
        less_cmd = ['less', '-R', temp_path]
        subprocess.run(less_cmd)
    finally:
        # 删除临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def render_markdown_with_rich(content):
    """
    使用Rich库渲染Markdown格式，比自定义的process_markdown函数功能更强大
    
    Args:
        content: Markdown格式的内容
        
    Returns:
        str: 渲染后的内容，带有ANSI颜色代码
    """
    # 创建字符串IO对象，用于捕获Rich输出
    string_io = io.StringIO()
    
    # 创建控制台对象，输出到字符串IO
    console = Console(file=string_io, width=120, highlight=True)
    
    # 创建Markdown对象
    markdown = Markdown(content)
    
    # 渲染Markdown到字符串IO
    console.print(markdown)
    
    # 获取渲染后的内容
    return string_io.getvalue()

# 保留process_markdown函数作为备用方案
def process_markdown(content):
    """
    处理Markdown格式，将其转换为带有ANSI颜色的文本，以提升终端显示效果
    参考：https://github.com/MichaelMure/go-term-markdown
    
    Args:
        content: Markdown格式的内容
        
    Returns:
        str: 处理后的内容，带有ANSI颜色代码
    """
    lines = content.split('\n')
    result = []
    
    # ANSI颜色代码
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    RESET = '\033[0m'
    
    in_code_block = False
    code_block_lang = ""
    in_table = False
    table_header_separator = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 处理代码块
        if line.startswith("```"):
            in_code_block = not in_code_block
            if in_code_block and len(line) > 3:
                code_block_lang = line[3:].strip()
                result.append(f"{YELLOW}```{code_block_lang}{RESET}")
            else:
                result.append(f"{YELLOW}```{RESET}")
            i += 1
            continue
            
        # 在代码块内
        if in_code_block:
            result.append(f"{CYAN}{line}{RESET}")
            i += 1
            continue
        
        # 检测表格
        import re
        is_table_row = bool(re.match(r'^\s*\|(.+\|)+\s*$', line))
        is_table_separator = bool(re.match(r'^\s*\|(\s*[-:]+\s*\|)+\s*$', line))
        
        # 处理表格
        if is_table_row or is_table_separator:
            if not in_table and not is_table_separator:
                in_table = True
                
            if is_table_separator:
                table_header_separator = True
                result.append(f"{YELLOW}{line}{RESET}")
            elif table_header_separator:
                # 这是表头下面的行，应用粗体
                cells = line.split('|')
                formatted_cells = []
                for cell in cells:
                    formatted_cells.append(f"{BOLD}{BLUE}{cell}{RESET}")
                result.append('|'.join(formatted_cells))
                table_header_separator = False
            else:
                # 普通表格行
                cells = line.split('|')
                formatted_cells = []
                for cell in cells:
                    formatted_cells.append(f"{BLUE}{cell}{RESET}")
                result.append('|'.join(formatted_cells))
            i += 1
            continue
        else:
            in_table = False
            table_header_separator = False
            
        # 处理标题
        if line.startswith("# "):
            result.append(f"{BOLD}{RED}{line}{RESET}")
            i += 1
            continue
        if line.startswith("## "):
            result.append(f"{BOLD}{RED}{line}{RESET}")
            i += 1
            continue
        if line.startswith("### "):
            result.append(f"{BOLD}{RED}{line}{RESET}")
            i += 1
            continue
        if line.startswith("#### "):
            result.append(f"{BOLD}{RED}{line}{RESET}")
            i += 1
            continue
            
        # 处理列表
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            result.append(f"{GREEN}{line}{RESET}")
            i += 1
            continue
        
        # 处理数字列表
        if re.match(r'^\s*\d+\.\s+', line):
            result.append(f"{GREEN}{line}{RESET}")
            i += 1
            continue
            
        # 处理粗体和斜体（简化处理，可能有边界情况未考虑）
        line_with_format = line
        # 处理粗体 **text**
        line_with_format = re.sub(r'\*\*([^*]+)\*\*', f'{BOLD}\\1{RESET}', line_with_format)
        # 处理斜体 *text*
        line_with_format = re.sub(r'\*([^*]+)\*', f'{ITALIC}\\1{RESET}', line_with_format)
        # 处理代码 `text`
        line_with_format = re.sub(r'`([^`]+)`', f'{CYAN}\\1{RESET}', line_with_format)
        
        result.append(line_with_format)
        i += 1
    
    return '\n'.join(result)

def get_command_example(command_name, debug=False):
    """
    获取命令示例
    
    Args:
        command_name: 命令名称
        debug: 调试模式
    
    Returns:
        bool: 操作是否成功
    """
    try:
        if debug:
            print(f"正在查询命令 '{command_name}' 的示例...")
            sys.stdout.flush()
        
        # 加载配置
        print("正在加载配置...")
        sys.stdout.flush()
        config = load_config()
        if not config:
            print("错误：无法加载配置文件，请先运行 'manzh config init' 创建配置")
            sys.stdout.flush()
            return False
            
        print(f"使用服务: {config.get('default_service', '未指定')}")
        sys.stdout.flush()
        
        # 创建翻译服务
        print("正在初始化服务...")
        sys.stdout.flush()
        try:
            service = create_translation_service(config)
            print("服务初始化成功")
            sys.stdout.flush()
        except Exception as e:
            print(f"错误：初始化服务失败 - {str(e)}")
            sys.stdout.flush()
            return False
        
        # 设置系统提示
        system_prompt = (
            "你是一个Linux/Unix命令专家，请提供以下命令的常用用法示例。"
            "要求："
            "1. 简单解释命令的主要功能；"
            "2. 提供3-5个最常用的实用示例，并简要说明每个示例的作用；"
            "3. 使用Markdown格式，确保代码块正确格式化；"
            "4. 示例应直接可用，无需额外修改；"
            "5. 保持简洁明了，避免冗长解释。"
        )
        
        # 准备请求内容
        content = f"命令名称：{command_name}\n请提供该命令的用法示例。"
        
        # 发送请求
        print("正在查询示例...")
        sys.stdout.flush()
        try:
            result = service.translate(content, system_prompt)
            if not result:
                print("错误：未获取到有效的示例内容")
                sys.stdout.flush()
                return False
                
            # 使用分页器显示内容
            print("\n命令示例查询结果：")
            sys.stdout.flush()
            show_with_pager(result)
            return True
            
        except Exception as e:
            print(f"查询示例失败：{str(e)}")
            sys.stdout.flush()
            if debug:
                import traceback
                traceback.print_exc()
            return False
            
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.stdout.flush()
        return False
    except Exception as e:
        print(f"发生错误：{str(e)}")
        sys.stdout.flush()
        if debug:
            import traceback
            traceback.print_exc()
        return False

def example_command(args):
    """
    处理example命令
    
    Args:
        args: 命令行参数
    """
    debug_mode = args.debug if hasattr(args, 'debug') else False
    command_name = args.command_name
    
    if not command_name:
        print("错误：缺少命令名称")
        sys.stdout.flush()
        return False
        
    return get_command_example(command_name, debug_mode)

def interactive_example():
    """交互式示例查询界面"""
    try:
        while True:
            print("\n命令示例查询")
            print("============")
            print("输入q或exit退出")
            sys.stdout.flush()
            
            command = input("\n请输入要查询的命令名称: ").strip()
            if command.lower() in ('q', 'exit', 'quit'):
                return
                
            if not command:
                print("命令名称不能为空，请重新输入")
                sys.stdout.flush()
                continue
                
            debug = input("是否启用调试模式? (y/N): ").strip().lower() == 'y'
            get_command_example(command, debug)
            
            if input("\n是否继续查询其他命令? (Y/n): ").strip().lower() == 'n':
                return
                
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.stdout.flush() 