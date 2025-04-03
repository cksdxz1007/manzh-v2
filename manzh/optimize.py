import os
import sys
import re
import subprocess
import argparse
from pathlib import Path

def optimize_man_page(file_path, save=True, debug=False):
    """
    优化man页面文件内容，移除无意义符号和行
    
    Args:
        file_path: man页面文件路径
        save: 是否保存更改
        debug: 是否启用调试输出
    
    Returns:
        tuple: (优化后的内容, 统计信息)
    """
    if debug:
        print(f"处理文件: {file_path}")
        sys.stdout.flush()
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        sys.stdout.flush()
        return None, None
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_size = len(content)
        original_lines = content.count('\n') + 1
        
        if debug:
            print(f"原始大小: {original_size} 字节, {original_lines} 行")
            sys.stdout.flush()
        
        # 保存原始内容副本用于比较
        original_content = content
        
        # 优化步骤
        
        # 1. 移除文件开头和结尾的()行
        content = re.sub(r'^\s*\(\)\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*\(\)\s*$', '', content, flags=re.MULTILINE)
        
        # 2. 移除单独的()行
        content = re.sub(r'^\s*\(\)\s*$\n', '', content, flags=re.MULTILINE)
        
        # 3. 移除行尾多余的空格
        content = re.sub(r' +$', '', content, flags=re.MULTILINE)
        
        # 4. 移除仅包含空格的行
        content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
        
        # 5. 移除开头和结尾的空行
        content = content.strip()
        
        # 6. 处理超过两个的连续空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 计算统计信息
        optimized_size = len(content)
        optimized_lines = content.count('\n') + 1
        size_diff = original_size - optimized_size
        line_diff = original_lines - optimized_lines
        
        stats = {
            "original_size": original_size,
            "original_lines": original_lines,
            "optimized_size": optimized_size,
            "optimized_lines": optimized_lines,
            "size_reduction": size_diff,
            "size_reduction_percent": (size_diff / original_size * 100) if original_size > 0 else 0,
            "line_reduction": line_diff
        }
        
        if debug:
            print(f"优化后大小: {optimized_size} 字节, {optimized_lines} 行")
            print(f"减少了: {size_diff} 字节 ({stats['size_reduction_percent']:.1f}%), {line_diff} 行")
            sys.stdout.flush()
            
            if original_content != content:
                print("文件内容已更改")
            else:
                print("文件内容未更改")
            sys.stdout.flush()
        
        # 保存优化后的内容
        if save and original_content != content:
            # 为防止权限问题，使用sudo写入
            try:
                with open(file_path + '.tmp', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 使用sudo移动临时文件到原始位置
                subprocess.run(['sudo', 'mv', file_path + '.tmp', file_path], check=True)
                subprocess.run(['sudo', 'chmod', '644', file_path], check=True)
                
                if debug:
                    print(f"已保存优化后的内容到 {file_path}")
                    sys.stdout.flush()
            except Exception as e:
                print(f"保存文件时出错: {str(e)}")
                sys.stdout.flush()
                if os.path.exists(file_path + '.tmp'):
                    os.remove(file_path + '.tmp')
        
        return content, stats
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        sys.stdout.flush()
        if debug:
            import traceback
            traceback.print_exc()
        return None, None

def optimize_man_directory(directory, recursive=True, debug=False):
    """
    优化目录中所有man页面文件
    
    Args:
        directory: man页面目录
        recursive: 是否递归处理子目录
        debug: 是否启用调试输出
    
    Returns:
        dict: 处理统计信息
    """
    if not os.path.exists(directory):
        print(f"错误: 目录不存在 - {directory}")
        sys.stdout.flush()
        return None
    
    total_stats = {
        "total_files": 0,
        "processed_files": 0,
        "failed_files": 0,
        "unchanged_files": 0,
        "total_size_reduction": 0,
        "total_line_reduction": 0
    }
    
    # 获取所有man文件
    if recursive:
        files = list(Path(directory).rglob("*.[0-9]"))
    else:
        files = list(Path(directory).glob("*.[0-9]"))
    
    total_stats["total_files"] = len(files)
    
    if debug:
        print(f"找到 {len(files)} 个手册文件")
        sys.stdout.flush()
    
    for file_path in files:
        file_path_str = str(file_path)
        content, stats = optimize_man_page(file_path_str, save=True, debug=debug)
        
        if content is not None:
            total_stats["processed_files"] += 1
            
            if stats["size_reduction"] > 0:
                total_stats["total_size_reduction"] += stats["size_reduction"]
                total_stats["total_line_reduction"] += stats["line_reduction"]
            else:
                total_stats["unchanged_files"] += 1
        else:
            total_stats["failed_files"] += 1
    
    # 显示总结
    print(f"\n优化处理完成:")
    print(f"- 总文件数: {total_stats['total_files']}")
    print(f"- 成功处理: {total_stats['processed_files']}")
    print(f"- 处理失败: {total_stats['failed_files']}")
    print(f"- 无变化文件: {total_stats['unchanged_files']}")
    print(f"- 总减少字节: {total_stats['total_size_reduction']} 字节")
    print(f"- 总减少行数: {total_stats['total_line_reduction']} 行")
    sys.stdout.flush()
    
    return total_stats

def interactive_optimize(man_dir="/usr/local/share/man/zh_CN"):
    """交互式优化界面"""
    print("\n手册页优化工具")
    print("=============")
    sys.stdout.flush()
    
    while True:
        print("\n优化选项：")
        print("1. 优化指定的手册页文件")
        print("2. 优化指定章节的所有手册页")
        print("3. 优化所有中文手册页")
        print("4. 返回主菜单")
        sys.stdout.flush()
        
        choice = input("\n请选择操作 [1-4]: ").strip()
        
        if choice == "1":
            command = input("请输入命令名称: ").strip()
            section = input("请输入章节号 (默认为1): ").strip() or "1"
            file_path = os.path.join(man_dir, f"man{section}", f"{command}.{section}")
            
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                sys.stdout.flush()
                continue
            
            debug = input("是否启用调试模式? (y/N): ").strip().lower() == 'y'
            optimize_man_page(file_path, save=True, debug=debug)
            
        elif choice == "2":
            section = input("请输入章节号: ").strip()
            if not section:
                print("章节号不能为空")
                sys.stdout.flush()
                continue
                
            section_dir = os.path.join(man_dir, f"man{section}")
            if not os.path.exists(section_dir):
                print(f"章节目录不存在: {section_dir}")
                sys.stdout.flush()
                continue
                
            debug = input("是否启用调试模式? (y/N): ").strip().lower() == 'y'
            optimize_man_directory(section_dir, recursive=False, debug=debug)
            
        elif choice == "3":
            if not os.path.exists(man_dir):
                print(f"中文手册目录不存在: {man_dir}")
                sys.stdout.flush()
                continue
                
            debug = input("是否启用调试模式? (y/N): ").strip().lower() == 'y'
            optimize_man_directory(man_dir, recursive=True, debug=debug)
            
        elif choice == "4":
            break
            
        else:
            print("无效的选择，请重试")
            sys.stdout.flush()

def optimize_command(args):
    """处理optimize命令"""
    debug_mode = args.debug if hasattr(args, 'debug') else False
    
    try:
        if hasattr(args, 'file') and args.file:
            # 优化单个文件
            file_path = args.file
            if not os.path.exists(file_path):
                print(f"错误: 文件不存在 - {file_path}")
                sys.stdout.flush()
                sys.exit(1)
                
            optimize_man_page(file_path, save=True, debug=debug_mode)
            
        elif hasattr(args, 'command_name') and args.command_name:
            # 根据命令名和章节号优化
            command = args.command_name
            section = args.section or "1"
            man_dir = args.dir or "/usr/local/share/man/zh_CN"
            
            file_path = os.path.join(man_dir, f"man{section}", f"{command}.{section}")
            if not os.path.exists(file_path):
                print(f"错误: 文件不存在 - {file_path}")
                sys.stdout.flush()
                sys.exit(1)
                
            optimize_man_page(file_path, save=True, debug=debug_mode)
            
        elif hasattr(args, 'section') and args.section:
            # 优化特定章节
            section = args.section
            man_dir = args.dir or "/usr/local/share/man/zh_CN"
            
            section_dir = os.path.join(man_dir, f"man{section}")
            if not os.path.exists(section_dir):
                print(f"错误: 章节目录不存在 - {section_dir}")
                sys.stdout.flush()
                sys.exit(1)
                
            optimize_man_directory(section_dir, recursive=False, debug=debug_mode)
            
        elif hasattr(args, 'dir') and args.dir:
            # 优化整个目录
            directory = args.dir
            if not os.path.exists(directory):
                print(f"错误: 目录不存在 - {directory}")
                sys.stdout.flush()
                sys.exit(1)
                
            recursive = args.recursive if hasattr(args, 'recursive') else True
            optimize_man_directory(directory, recursive=recursive, debug=debug_mode)
            
        else:
            # 默认优化所有中文手册
            man_dir = "/usr/local/share/man/zh_CN"
            if not os.path.exists(man_dir):
                print(f"错误: 中文手册目录不存在 - {man_dir}")
                sys.stdout.flush()
                sys.exit(1)
                
            optimize_man_directory(man_dir, recursive=True, debug=debug_mode)
            
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.stdout.flush()
        sys.exit(1)
    except Exception as e:
        print(f"优化过程中发生错误: {str(e)}")
        sys.stdout.flush()
        if debug_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # 直接运行此模块时的命令行参数解析
    parser = argparse.ArgumentParser(description="优化man手册页面，移除无意义内容")
    parser.add_argument("-f", "--file", help="要优化的单个手册文件路径")
    parser.add_argument("-c", "--command", dest="command_name", help="命令名称")
    parser.add_argument("-s", "--section", help="man手册章节号")
    parser.add_argument("-d", "--dir", help="手册目录路径")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归处理子目录")
    parser.add_argument("--debug", action="store_true", help="启用详细调试输出")
    
    args = parser.parse_args()
    
    if len(sys.argv) > 1:
        optimize_command(args)
    else:
        interactive_optimize() 