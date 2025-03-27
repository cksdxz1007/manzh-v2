import os
import sys
import shutil
import subprocess
from .man_utils import list_translated_manuals

def clean_manual(command, section=None, man_dir="/usr/local/share/man/zh_CN"):
    """
    清理指定命令的翻译手册
    
    Args:
        command: 命令名称
        section: 章节号（可选）
        man_dir: man手册目录
        
    Returns:
        bool: 是否清理成功
    """
    try:
        if section:
            # 清理指定章节的手册
            target_file = os.path.join(man_dir, f"man{section}", f"{command}.{section}")
            if os.path.exists(target_file):
                subprocess.run(['sudo', 'rm', target_file], check=True)
                print(f"已删除：{target_file}")
                return True
            else:
                print(f"未找到手册：{target_file}")
                return False
        else:
            # 清理所有章节中的该命令手册
            found = False
            manuals = list_translated_manuals(man_dir)
            for sec, commands in manuals.items():
                if command in commands:
                    target_file = os.path.join(man_dir, f"man{sec}", f"{command}.{sec}")
                    subprocess.run(['sudo', 'rm', target_file], check=True)
                    print(f"已删除：{target_file}")
                    found = True
            return found
            
    except subprocess.CalledProcessError as e:
        print(f"删除文件失败：{str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"清理手册时发生错误：{str(e)}", file=sys.stderr)
        return False

def clean_section(section, man_dir="/usr/local/share/man/zh_CN"):
    """
    清理指定章节的所有翻译手册
    
    Args:
        section: 章节号
        man_dir: man手册目录
        
    Returns:
        bool: 是否清理成功
    """
    try:
        section_dir = os.path.join(man_dir, f"man{section}")
        if os.path.exists(section_dir):
            subprocess.run(['sudo', 'rm', '-rf', section_dir], check=True)
            print(f"已删除章节目录：{section_dir}")
            return True
        else:
            print(f"章节目录不存在：{section_dir}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"删除目录失败：{str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"清理章节时发生错误：{str(e)}", file=sys.stderr)
        return False

def clean_all(man_dir="/usr/local/share/man/zh_CN"):
    """
    清理所有翻译手册
    
    Args:
        man_dir: man手册目录
        
    Returns:
        bool: 是否清理成功
    """
    try:
        if os.path.exists(man_dir):
            subprocess.run(['sudo', 'rm', '-rf', man_dir], check=True)
            print(f"已删除所有翻译手册：{man_dir}")
            # 重新创建目录
            subprocess.run(['sudo', 'mkdir', '-p', man_dir], check=True)
            subprocess.run(['sudo', 'chmod', '755', man_dir], check=True)
            return True
        else:
            print(f"手册目录不存在：{man_dir}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"清理目录失败：{str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"清理所有手册时发生错误：{str(e)}", file=sys.stderr)
        return False

def interactive_clean(man_dir="/usr/local/share/man/zh_CN"):
    """交互式清理界面"""
    while True:
        print("\n清理选项：")
        print("1. 清理指定命令的手册")
        print("2. 清理指定章节的所有手册")
        print("3. 清理所有翻译手册")
        print("4. 返回主菜单")
        
        choice = input("\n请选择操作 [1-4]: ").strip()
        
        if choice == "1":
            command = input("请输入要清理的命令名称：").strip()
            section = input("请输入章节号（直接回车清理所有章节）：").strip()
            if section:
                clean_manual(command, section, man_dir)
            else:
                clean_manual(command, None, man_dir)
                
        elif choice == "2":
            section = input("请输入要清理的章节号：").strip()
            if section:
                clean_section(section, man_dir)
            else:
                print("章节号不能为空")
                
        elif choice == "3":
            confirm = input("确定要清理所有翻译手册吗？(y/N): ").strip().lower()
            if confirm == 'y':
                clean_all(man_dir)
                
        elif choice == "4":
            break
            
        else:
            print("无效的选择，请重试")
            
if __name__ == "__main__":
    interactive_clean()
