#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
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

class ManZHDemo:
    """ManZH 演示程序"""
    
    def __init__(self):
        self.config_path = get_default_config_path()
        self.manuals_dir = "/usr/local/share/man/zh_CN"
        self.temp_dir = os.path.expanduser("~/.cache/manzh/temp")
        self.check_config()
    
    def check_config(self):
        """检查配置文件是否存在，不存在则引导用户创建"""
        if not os.path.exists(self.config_path):
            print("\n未找到配置文件，需要先进行初始化设置。")
            interactive_init_config()
    
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
            
            command = input("\n请输入要翻译的命令: ").strip()
            
            if not command or command == "0":
                return
                
            try:
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
                    
            except Exception as e:
                print(f"\n翻译失败：{str(e)}", file=sys.stderr)
            
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
                    
        except Exception as e:
            print(f"\n查看手册失败：{str(e)}", file=sys.stderr)
            input("\n按回车键继续...")
    
    def show_config(self):
        """显示当前配置"""
        try:
            config = ConfigCache.get_config()
            print("\n当前配置：")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            input("\n按回车键继续...")
        except Exception as e:
            print(f"\n读取配置失败：{str(e)}", file=sys.stderr)
            input("\n按回车键继续...")
    
    def main_menu(self):
        """主菜单"""
        while True:
            print("\n=== ManZH 中文手册翻译工具 ===")
            print("1. 翻译命令手册")
            print("2. 配置管理")
            print("3. 清除已翻译手册")
            print("0. 退出")
            
            choice = input("\n请选择功能: ").strip()
            
            if choice == "0":
                print("\n感谢使用！")
                break
            elif choice == "1":
                self.translate_manual()
            elif choice == "2":
                interactive_config()
            elif choice == "3":
                self.clear_manuals()
            else:
                print("\n无效的选择，请重试。")

if __name__ == "__main__":
    demo = ManZHDemo()
    demo.main_menu() 