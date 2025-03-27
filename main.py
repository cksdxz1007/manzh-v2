#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ManZH - 中文手册翻译工具
主程序入口
"""

import os
import sys
import json
import argparse
import subprocess
import traceback
import signal
from manzh.config_cli import (
    interactive_add_service,
    interactive_update_service,
    interactive_delete_service,
    interactive_set_default,
    interactive_config,
    interactive_init_config
)
from manzh.config_manager import get_default_config_path, ConfigCache
from manzh.translate import translate_command
from manzh.clean import clean_manual, clean_section, clean_all
from manzh.list_manuals import list_manuals

# 全局信号处理
def signal_handler(sig, frame):
    print("\n\n程序被中断，正在退出...")
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)

class ManZHMain:
    """ManZH 中文手册翻译工具主程序"""
    
    def __init__(self):
        self.config_path = get_default_config_path()
        self.manuals_dir = "/usr/local/share/man/zh_CN"
        self.temp_dir = os.path.expanduser("~/.cache/manzh/temp")
        self.version = "1.0.4"
        self.check_config()
        self.show_welcome()
    
    def check_config(self):
        """检查配置文件是否存在，不存在则引导用户创建"""
        try:
            if not os.path.exists(self.config_path):
                print("\n未找到配置文件，需要先进行初始化设置。")
                interactive_init_config()
                print("\n配置初始化完成！")
        except KeyboardInterrupt:
            print("\n\n配置初始化被中断，退出程序...")
            sys.exit(1)
        except Exception as e:
            print(f"\n配置初始化失败：{str(e)}")
            print("\n请尝试手动创建配置文件，或重新运行程序。")
            sys.exit(1)
    
    def show_welcome(self):
        """显示欢迎信息"""
        print(f"""
╭─────────────────────────────────────────╮
│                                         │
│       ManZH 中文手册翻译工具 v{self.version}       │
│                                         │
│    将英文man手册翻译成中文的实用工具    │
│                                         │
╰─────────────────────────────────────────╯
""")
    
    def clear_manuals(self):
        """清除已翻译的手册"""
        from manzh.clean import interactive_clean
        try:
            print("\n=== 清除已翻译手册 ===")
            interactive_clean()
        except KeyboardInterrupt:
            print("\n\n操作已取消")
        except Exception as e:
            print(f"\n清除失败：{str(e)}")
            if "--debug" in sys.argv:
                traceback.print_exc()
            input("\n按回车键继续...")
    
    def translate_manual(self):
        """翻译命令手册"""
        while True:
            print("\n=== 翻译命令手册 ===")
            print("提示：")
            print("1. 输入命令名称开始翻译")
            print("2. 支持带章节号的命令，如：ls.1")
            print("3. 没有man手册的命令将自动翻译--help输出")
            print("4. 翻译结果需要sudo权限才能保存到系统目录")
            print("5. 已翻译过的命令将使用缓存，除非选择重新翻译")
            print("0. 返回主菜单")
            
            try:
                command = input("\n请输入要翻译的命令: ").strip()
                
                if not command or command == "0":
                    return
                    
                # 检查命令是否存在
                which_result = subprocess.run(['which', command.split('.')[0]], 
                                           capture_output=True, 
                                           text=True)
                                           
                if which_result.returncode != 0:
                    print(f"\n警告：找不到命令 '{command}'")
                    if input("是否继续翻译？(y/N): ").lower() != 'y':
                        continue
                
                # 解析命令和章节
                section = "1"  # 默认章节
                name = command
                if "." in command:
                    name, section = command.split(".")
                
                # 检查是否已有缓存
                cache_path = os.path.join(os.path.expanduser("~/.cache/manzh/translations"), 
                                        f"{name}.{section}.cache")
                if os.path.exists(cache_path):
                    print(f"\n发现已有的翻译缓存。")
                    force_translate = input("是否重新翻译？(y/N): ").lower() == 'y'
                else:
                    force_translate = False
                
                print(f"\n开始{'重新' if force_translate else ''}翻译 {command} ...")
                
                # 调用翻译函数
                success = translate_command(name, section, force_translate)
                
                if success:
                    print("\n翻译完成！")
                    print(f"手册已保存到：{self.manuals_dir}")
                    
                    if input("\n是否立即查看翻译结果？(Y/n): ").lower() != 'n':
                        # 首先尝试系统目录
                        manual_path = os.path.join(self.manuals_dir, f"man{section}", f"{name}.{section}")
                        if os.path.exists(manual_path):
                            subprocess.run(['man', manual_path])
                        else:
                            # 如果系统目录不存在，尝试临时目录
                            temp_path = os.path.join(self.temp_dir, f"{name}.{section}")
                            if os.path.exists(temp_path):
                                subprocess.run(['man', temp_path])
                            else:
                                print(f"\n错误：找不到翻译后的手册文件")
                else:
                    print("\n翻译失败！")
                    print("请检查配置、网络连接和权限。")
                    
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return
            except Exception as e:
                print(f"\n翻译失败：{str(e)}", file=sys.stderr)
                if "--debug" in sys.argv:
                    traceback.print_exc()
            
            input("\n按回车键继续...")
    
    def view_translated_manuals(self):
        """查看已翻译的手册"""
        try:
            if not os.path.exists(self.manuals_dir):
                print("\n还没有翻译过任何手册。")
                input("\n按回车键继续...")
                return
                
            while True:
                print("\n=== 已翻译的手册 ===")
                # 遍历所有章节目录
                all_manuals = []
                for section in sorted(os.listdir(self.manuals_dir)):
                    if section.startswith('man'):
                        section_dir = os.path.join(self.manuals_dir, section)
                        if os.path.isdir(section_dir):
                            section_num = section[3:]
                            manuals = [f for f in os.listdir(section_dir) 
                                     if f.endswith('.' + section_num)]
                            for manual in manuals:
                                name = manual.rsplit('.', 1)[0]
                                all_manuals.append((name, section_num, 
                                                  os.path.join(section_dir, manual)))
                
                if not all_manuals:
                    print("还没有翻译过任何手册。")
                    input("\n按回车键继续...")
                    return
                    
                # 按名称排序并显示
                all_manuals.sort(key=lambda x: x[0])
                print("\n按章节显示：")
                current_section = None
                for name, section, _ in all_manuals:
                    if section != current_section:
                        current_section = section
                        print(f"\n第 {section} 章:")
                    print(f"  - {name}")
                
                print("\n选项：")
                print("1. 查看特定手册")
                print("0. 返回主菜单")
                
                try:
                    choice = input("\n请选择 [0-1]: ").strip()
                    
                    if choice == "0":
                        return
                    elif choice == "1":
                        name = input("\n请输入要查看的命令名称: ").strip()
                        section = input("请输入章节号（直接回车默认为1）: ").strip() or "1"
                        
                        # 查找手册
                        manual_path = os.path.join(self.manuals_dir, f"man{section}", f"{name}.{section}")
                        if os.path.exists(manual_path):
                            subprocess.run(['man', manual_path])
                        else:
                            print(f"\n错误：找不到手册文件：{manual_path}")
                            input("\n按回车键继续...")
                    else:
                        print("\n无效选项")
                        input("\n按回车键继续...")
                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    return
                    
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            return
        except Exception as e:
            print(f"\n查看手册失败：{str(e)}", file=sys.stderr)
            if "--debug" in sys.argv:
                traceback.print_exc()
            input("\n按回车键继续...")
    
    def show_config(self):
        """显示当前配置"""
        try:
            config = ConfigCache.get_config()
            print("\n当前配置：")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            input("\n按回车键继续...")
        except KeyboardInterrupt:
            print("\n\n操作已取消")
        except Exception as e:
            print(f"\n读取配置失败：{str(e)}", file=sys.stderr)
            if "--debug" in sys.argv:
                traceback.print_exc()
            input("\n按回车键继续...")
    
    def main_menu(self):
        """主菜单"""
        while True:
            try:
                print("\n=== ManZH 中文手册翻译工具 ===")
                print("1. 翻译命令手册")
                print("2. 查看已翻译手册")
                print("3. 配置管理")
                print("4. 清除已翻译手册")
                print("5. 显示当前配置")
                print("0. 退出")
                
                choice = input("\n请选择功能 [0-5]: ").strip()
                
                if choice == "0":
                    print("\n感谢使用！")
                    break
                elif choice == "1":
                    self.translate_manual()
                elif choice == "2":
                    self.view_translated_manuals()
                elif choice == "3":
                    interactive_config()
                elif choice == "4":
                    self.clear_manuals()
                elif choice == "5":
                    self.show_config()
                else:
                    print("\n无效的选择，请重试。")
            except KeyboardInterrupt:
                print("\n\n程序被中断")
                confirm = input("是否退出程序？(Y/n): ").strip().lower()
                if confirm != 'n':
                    print("\n感谢使用！")
                    break
            except Exception as e:
                print(f"\n发生错误：{str(e)}", file=sys.stderr)
                if "--debug" in sys.argv:
                    traceback.print_exc()
                input("\n按回车键继续...")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="ManZH - 中文手册翻译工具")
    
    # 使用子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # translate 命令
    translate_parser = subparsers.add_parser("translate", help="翻译命令手册")
    translate_parser.add_argument("name", help="要翻译的命令名称")
    translate_parser.add_argument("-s", "--section", help="手册章节号，默认为1", default="1")
    translate_parser.add_argument("-f", "--force", help="强制重新翻译，忽略缓存", action="store_true")
    translate_parser.add_argument("--service", help="指定使用的翻译服务")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出已翻译的手册")
    list_parser.add_argument("-s", "--section", help="只列出指定章节的手册")
    
    # clean 命令
    clean_parser = subparsers.add_parser("clean", help="清除已翻译的手册")
    clean_parser.add_argument("target", nargs="?", help="要清除的命令名称或章节号")
    clean_parser.add_argument("-s", "--section", help="与命令名称一起使用，指定章节号")
    clean_parser.add_argument("-a", "--all", help="清除所有已翻译的手册", action="store_true")
    
    # config 命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument("action", nargs="?", choices=["add", "update", "delete", "default", "show", "init"],
                             help="配置操作：add(添加服务), update(更新服务), delete(删除服务), default(设置默认服务), show(显示配置), init(初始化配置)")
    
    # 版本信息
    parser.add_argument("-v", "--version", action="version", version=f"ManZH v1.0.4")
    
    # 调试模式
    parser.add_argument("--debug", help="启用调试模式，显示详细错误信息", action="store_true")
    
    return parser.parse_args()

def handle_command_args(args):
    """处理命令行参数"""
    if args.command == "translate":
        # 翻译命令
        return translate_command(args.name, args.section, args.force)
        
    elif args.command == "list":
        # 列出已翻译的手册
        return list_manuals(args.section)
        
    elif args.command == "clean":
        # 清除已翻译的手册
        if args.all:
            # 清除所有手册
            return clean_all()
        elif args.target:
            # 检查target是否是数字（章节号）
            if args.target.isdigit():
                # 清除指定章节
                return clean_section(args.target)
            else:
                # 清除指定命令
                return clean_manual(args.target, args.section)
        else:
            # 交互式清除
            from manzh.clean import interactive_clean
            return interactive_clean()
            
    elif args.command == "config":
        # 配置管理
        if args.action == "add":
            return interactive_add_service()
        elif args.action == "update":
            return interactive_update_service()
        elif args.action == "delete":
            return interactive_delete_service()
        elif args.action == "default":
            return interactive_set_default()
        elif args.action == "show":
            config = ConfigCache.get_config()
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return True
        elif args.action == "init":
            return interactive_init_config()
        else:
            # 无子命令，进入交互式配置
            return interactive_config()
    
    return False

def main():
    """程序主入口"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 如果指定了命令，执行命令行模式
        if args.command:
            success = handle_command_args(args)
            sys.exit(0 if success else 1)
        
        # 否则启动交互式界面
        app = ManZHMain()
        app.main_menu()
        
    except KeyboardInterrupt:
        print("\n\n程序被中断，已退出")
        sys.exit(1)
    except Exception as e:
        print(f"\n程序运行出错：{str(e)}", file=sys.stderr)
        if getattr(args, "debug", False):
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 