#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动补全安装脚本
"""
import os
import sys
import argcomplete
import subprocess
import argparse

def install_completion():
    """安装自动补全功能"""
    print("正在为 manzh 安装命令行自动补全功能...")
    
    # 检测当前shell
    shell = os.environ.get('SHELL', '')
    if 'zsh' in shell:
        install_zsh_completion()
    elif 'bash' in shell:
        install_bash_completion()
    else:
        print(f"未识别的 shell 类型: {shell}")
        print("仅支持 Bash 和 Zsh 的自动补全安装")
        print("请参考手动安装说明: https://github.com/cksdxz1007/ManZH#自动补全")
        return False
    
    return True

def install_bash_completion():
    """安装Bash自动补全"""
    try:
        # 检查是否已安装
        if check_existing_completion("~/.bashrc", "manzh-complete"):
            print("Bash 补全已安装，无需重复操作")
            return True
            
        # 生成补全脚本到独立文件
        completion_script_path = os.path.expanduser("~/.manzh-complete")
        
        try:
            completion_content = subprocess.check_output(
                ["register-python-argcomplete", "manzh"], 
                stderr=subprocess.DEVNULL, 
                text=True
            )
            
            with open(completion_script_path, "w") as f:
                f.write(completion_content)
                
            print(f"补全脚本已保存到: {completion_script_path}")
                
        except Exception as e:
            print(f"生成补全脚本时出错: {str(e)}")
            return False
            
        # 在bashrc中添加引用
        with open(os.path.expanduser("~/.bashrc"), "a") as f:
            f.write("\n# manzh 自动补全配置\n")
            f.write("[ -f ~/.manzh-complete ] && source ~/.manzh-complete\n")
            
        print("Bash 补全配置已添加到 ~/.bashrc")
        print("请运行以下命令激活补全功能:")
        print(f"  source ~/.bashrc")
        print("或重新打开终端窗口")
        
        return True
    except Exception as e:
        print(f"安装 Bash 补全时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def install_zsh_completion():
    """安装Zsh自动补全"""
    try:
        # 检查是否已安装
        if check_existing_completion("~/.zshrc", "manzh-complete"):
            print("Zsh 补全已安装，无需重复操作")
            return True
            
        # 生成补全脚本到独立文件
        completion_script_path = os.path.expanduser("~/.manzh-complete")
        
        try:
            completion_content = subprocess.check_output(
                ["register-python-argcomplete", "manzh"], 
                stderr=subprocess.DEVNULL, 
                text=True
            )
            
            with open(completion_script_path, "w") as f:
                f.write(completion_content)
                
            print(f"补全脚本已保存到: {completion_script_path}")
                
        except Exception as e:
            print(f"生成补全脚本时出错: {str(e)}")
            return False
            
        # 修改zshrc
        with open(os.path.expanduser("~/.zshrc"), "a") as f:
            f.write("\n# manzh 自动补全配置\n")
            f.write("autoload -U bashcompinit\n")
            f.write("bashcompinit\n")
            f.write(f"source {completion_script_path}\n")
            
        print("Zsh 补全配置已添加到 ~/.zshrc")
        print("请运行以下命令激活补全功能:")
        print(f"  source ~/.zshrc")
        print("或重新打开终端窗口")
        
        return True
    except Exception as e:
        print(f"安装 Zsh 补全时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_existing_completion(rc_file, command):
    """检查是否已存在补全配置"""
    try:
        with open(os.path.expanduser(rc_file), "r") as f:
            content = f.read()
            if command == "manzh-complete":
                return "source ~/.manzh-complete" in content
            else:
                return f"register-python-argcomplete {command}" in content
        return False
    except Exception:
        return False

def print_manual_instructions():
    """打印手动安装说明"""
    print("\n手动安装说明:")
    print("1. 为 bash 安装自动补全:")
    print("   register-python-argcomplete manzh > ~/.manzh-complete")
    print("   echo '[ -f ~/.manzh-complete ] && source ~/.manzh-complete' >> ~/.bashrc")
    print("   source ~/.bashrc")
    print("")
    print("2. 为 zsh 安装自动补全:")
    print("   register-python-argcomplete manzh > ~/.manzh-complete")
    print("   echo 'autoload -U bashcompinit' >> ~/.zshrc")
    print("   echo 'bashcompinit' >> ~/.zshrc")
    print("   echo 'source ~/.manzh-complete' >> ~/.zshrc")
    print("   source ~/.zshrc")

def main(args=None):
    """主函数"""
    if args is None:
        parser = argparse.ArgumentParser(description="manzh 命令行自动补全安装")
        parser.add_argument("--manual", action="store_true", help="只显示手动安装说明")
        args = parser.parse_args()
    
    if hasattr(args, 'manual') and args.manual:
        print_manual_instructions()
        return
        
    if not install_completion():
        print_manual_instructions()

if __name__ == "__main__":
    main() 