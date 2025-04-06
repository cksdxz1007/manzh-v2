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
        if check_existing_completion("~/.bashrc", "manzh"):
            print("Bash 补全已安装，无需重复操作")
            return True
            
        # 获取激活补全的命令
        activate_cmd = "eval \"$(python -m argcomplete.bash_completion manzh)\""
        
        # 检查补全目录是否存在
        completion_dir = os.path.expanduser("~/.bash_completion.d")
        if not os.path.exists(completion_dir):
            os.makedirs(completion_dir)
            print(f"创建目录: {completion_dir}")
            
        # 创建补全脚本
        completion_script = os.path.join(completion_dir, "manzh.sh")
        with open(completion_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# manzh 命令自动补全\n")
            f.write("eval \"$(python -m argcomplete.bash_completion manzh)\"\n")
            
        print(f"补全脚本已保存到: {completion_script}")
        
        # 为脚本添加执行权限
        os.chmod(completion_script, 0o755)
        
        # 在bashrc中添加引用
        with open(os.path.expanduser("~/.bashrc"), "a") as f:
            f.write("\n# manzh 自动补全\n")
            f.write(f"if [ -f {completion_script} ]; then\n")
            f.write(f"    source {completion_script}\n")
            f.write("fi\n")
            
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
        if check_existing_completion("~/.zshrc", "manzh"):
            print("Zsh 补全已安装，无需重复操作")
            return True
            
        # 创建补全目录（如果不存在）
        completion_dir = os.path.expanduser("~/.zsh/completion")
        if not os.path.exists(completion_dir):
            os.makedirs(completion_dir)
            print(f"创建目录: {completion_dir}")
            
        # 创建补全脚本
        completion_script = os.path.join(completion_dir, "_manzh")
        with open(completion_script, "w") as f:
            f.write("# manzh 命令自动补全\n")
            f.write("if type compdef &>/dev/null; then\n")
            f.write("  autoload -U bashcompinit\n")
            f.write("  bashcompinit\n")
            f.write("  eval \"$(python -m argcomplete.bash_completion manzh)\"\n")
            f.write("fi\n")
            
        print(f"补全脚本已保存到: {completion_script}")
        
        # 修改zshrc
        with open(os.path.expanduser("~/.zshrc"), "a") as f:
            f.write("\n# manzh 自动补全\n")
            f.write("fpath=(~/.zsh/completion $fpath)\n")
            f.write("autoload -U compinit\n")
            f.write("compinit\n")
            f.write(f"source {completion_script}\n")
            
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
            if "manzh 自动补全" in content:
                return True
        return False
    except Exception:
        return False

def print_manual_instructions():
    """打印手动安装说明"""
    print("\n手动安装说明:")
    print("1. 为 bash 安装自动补全:")
    print("   echo 'eval \"$(python -m argcomplete.bash_completion manzh)\"' >> ~/.bashrc")
    print("   source ~/.bashrc")
    print("")
    print("2. 为 zsh 安装自动补全:")
    print("   autoload -U bashcompinit")
    print("   bashcompinit")
    print("   echo 'eval \"$(python -m argcomplete.bash_completion manzh)\"' >> ~/.zshrc")
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