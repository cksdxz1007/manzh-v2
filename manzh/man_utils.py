import os
import subprocess
import sys

def get_man_page(command, section=None):
    """
    获取命令的man手册内容
    
    Args:
        command: 命令名称
        section: man手册章节号（可选）
        
    Returns:
        str: man手册内容，如果不存在则返回None
    """
    try:
        # 构建man命令
        man_cmd = ['man']
        if section:
            man_cmd.extend([section, command])
        else:
            man_cmd.append(command)
            
        # 使用col命令去除格式控制字符
        process = subprocess.Popen(
            man_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        col_process = subprocess.Popen(
            ['col', '-b'],
            stdin=process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 关闭管道
        process.stdout.close()
        
        # 获取输出
        output, error = col_process.communicate()
        
        # 检查返回码
        if col_process.returncode != 0:
            print(f"获取man手册时出错：{error.decode()}", file=sys.stderr)
            return None
            
        return output.decode('utf-8')
        
    except subprocess.CalledProcessError as e:
        print(f"执行man命令失败：{str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"获取man手册时发生错误：{str(e)}", file=sys.stderr)
        return None

def get_help_output(command):
    """
    获取命令的--help输出
    
    Args:
        command: 命令名称
        
    Returns:
        str: help输出内容，如果失败则返回None
    """
    try:
        result = subprocess.run(
            [command, '--help'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 如果--help失败，尝试-h
        if result.returncode != 0:
            result = subprocess.run(
                [command, '-h'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"获取{command}帮助信息失败：{result.stderr}", file=sys.stderr)
            return None
            
    except FileNotFoundError:
        print(f"命令不存在：{command}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"获取帮助信息时发生错误：{str(e)}", file=sys.stderr)
        return None

def save_man_page(content, command, section=1, target_dir="/usr/local/share/man/zh_CN"):
    """
    保存翻译后的man手册
    
    Args:
        content: 翻译后的内容
        command: 命令名称
        section: man手册章节号
        target_dir: 目标目录
        
    Returns:
        bool: 是否保存成功
    """
    try:
        # 确保目标目录存在
        section_dir = os.path.join(target_dir, f"man{section}")
        if not os.path.exists(section_dir):
            subprocess.run(['sudo', 'mkdir', '-p', section_dir], check=True)
            subprocess.run(['sudo', 'chmod', '755', section_dir], check=True)
            
        # 保存文件
        target_file = os.path.join(section_dir, f"{command}.{section}")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # 设置权限
        subprocess.run(['sudo', 'chmod', '644', target_file], check=True)
        
        print(f"已保存翻译结果到：{target_file}", file=sys.stderr)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"设置文件权限失败：{str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"保存翻译结果时发生错误：{str(e)}", file=sys.stderr)
        return False

def list_translated_manuals(man_dir="/usr/local/share/man/zh_CN"):
    """
    列出已翻译的手册
    
    Args:
        man_dir: man手册目录
        
    Returns:
        dict: 按章节分类的手册列表
    """
    result = {}
    try:
        # 遍历所有章节目录
        for section_dir in os.listdir(man_dir):
            if section_dir.startswith('man'):
                section = section_dir[3:]  # 提取章节号
                full_path = os.path.join(man_dir, section_dir)
                
                if os.path.isdir(full_path):
                    manuals = []
                    for file in os.listdir(full_path):
                        if file.endswith(f".{section}"):
                            command = file[:-len(f".{section}")]
                            manuals.append(command)
                    
                    if manuals:
                        result[section] = sorted(manuals)
                        
        return result
        
    except Exception as e:
        print(f"列出已翻译手册时发生错误：{str(e)}", file=sys.stderr)
        return {}
