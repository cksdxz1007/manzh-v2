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
    debug = os.environ.get('MANZH_DEBUG') == '1'
    if debug:
        print(f"调试: 尝试获取命令 '{command}' 的man手册" + (f" 章节 {section}" if section else ""), file=sys.stderr)
    
    try:
        # 构建man命令
        man_cmd = ['man']
        if section:
            man_cmd.extend([section, command])
        else:
            man_cmd.append(command)
            
        if debug:
            print(f"调试: 执行命令: {' '.join(man_cmd)}", file=sys.stderr)
            
        # 使用col命令去除格式控制字符
        process = subprocess.Popen(
            man_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 获取man命令的错误输出
        man_stdout, man_stderr = process.communicate()
        if process.returncode != 0:
            if debug:
                print(f"调试: man命令执行失败: {man_stderr.decode()}", file=sys.stderr)
            return None
        
        # 使用col命令去除格式控制字符
        col_process = subprocess.Popen(
            ['col', '-b'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 传递man输出到col
        col_stdout, col_stderr = col_process.communicate(input=man_stdout)
        
        # 检查返回码
        if col_process.returncode != 0:
            if debug:
                print(f"调试: col命令执行失败: {col_stderr.decode()}", file=sys.stderr)
            print(f"获取man手册时出错：{col_stderr.decode()}", file=sys.stderr)
            return None
            
        result = col_stdout.decode('utf-8')
        if debug:
            print(f"调试: 成功获取man手册，长度: {len(result)} 字符", file=sys.stderr)
        return result
        
    except subprocess.CalledProcessError as e:
        if debug:
            print(f"调试: 执行man命令异常: {str(e)}", file=sys.stderr)
        print(f"执行man命令失败：{str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        if debug:
            print(f"调试: 获取man手册时发生异常: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc()
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
    debug = os.environ.get('MANZH_DEBUG') == '1'
    if debug:
        print(f"调试: 尝试获取命令 '{command}' 的帮助输出")
        sys.stdout.flush()
    
    try:
        # 检查命令是否是shell内置命令
        if command in ['cd', 'source', 'alias', 'export', 'pwd', 'echo', 'set']:
            if debug:
                print(f"调试: {command} 是shell内置命令，使用help命令")
                sys.stdout.flush()
            result = subprocess.run(
                ['bash', '-c', f'help {command}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                if debug:
                    print(f"调试: 成功获取help输出，长度: {len(result.stdout)} 字符")
                    sys.stdout.flush()
                return result.stdout
        
        # 对于conda命令，尝试几种不同的方式获取帮助
        if command == 'conda':
            if debug:
                print(f"调试: 针对conda命令使用特殊处理")
                sys.stdout.flush()
            
            # 尝试方式列表
            attempt_methods = [
                ['conda', '-h'],                # 标准帮助选项
                ['conda', '--help'],            # 标准帮助选项
                ['conda', 'help'],              # conda特有的help子命令
                ['bash', '-c', 'conda -h'],     # 通过bash执行
                ['bash', '-c', 'conda --help'], # 通过bash执行
                ['bash', '-c', 'conda help'],   # 通过bash执行
                ['which', 'conda']              # 查找conda路径
            ]
            
            for method in attempt_methods:
                if debug:
                    print(f"调试: 尝试执行 {' '.join(method)}")
                    sys.stdout.flush()
                try:
                    result = subprocess.run(
                        method,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=5  # 设置超时防止命令卡住
                    )
                    
                    # 如果是which命令，获取conda路径后再尝试
                    if method[0] == 'which' and result.returncode == 0:
                        conda_path = result.stdout.strip()
                        if debug:
                            print(f"调试: 找到conda路径: {conda_path}")
                            sys.stdout.flush()
                        
                        if conda_path:
                            help_result = subprocess.run(
                                [conda_path, '--help'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=5
                            )
                            if help_result.returncode == 0 and help_result.stdout:
                                if debug:
                                    print(f"调试: 成功通过路径获取conda帮助")
                                    sys.stdout.flush()
                                return help_result.stdout
                    
                    # 检查正常输出
                    if result.returncode == 0 and result.stdout:
                        if debug:
                            print(f"调试: 成功获取conda帮助输出，长度: {len(result.stdout)} 字符")
                            sys.stdout.flush()
                        return result.stdout
                    
                    # 有些命令会输出到stderr而不是stdout
                    if result.stderr and len(result.stderr) > 100:  # 假设有意义的帮助信息至少有100个字符
                        if debug:
                            print(f"调试: 从stderr获取到可能的帮助信息，长度: {len(result.stderr)} 字符")
                            sys.stdout.flush()
                        return result.stderr
                        
                except subprocess.TimeoutExpired:
                    if debug:
                        print(f"调试: 执行 {' '.join(method)} 超时")
                        sys.stdout.flush()
                    continue
                except Exception as e:
                    if debug:
                        print(f"调试: 执行 {' '.join(method)} 失败: {str(e)}")
                        sys.stdout.flush()
                    continue
            
            # 如果所有尝试都失败，创建一个基本的说明文本
            if debug:
                print("调试: 所有获取conda帮助的方法都失败，生成基本说明")
                sys.stdout.flush()
            
            return """CONDA(1)                    Conda Package Manager                    CONDA(1)

NAME
       conda - Conda Package Manager

DESCRIPTION
       Conda is an open source package management system and environment management system that runs on Windows, macOS, Linux and z/OS.
       Conda quickly installs, runs, and updates packages and their dependencies.
       Conda easily creates, saves, loads, and switches between environments on your local computer.

COMMANDS
       clean        Remove unused packages and caches
       compare      Compare packages between conda environments
       config       Modify configuration values in .condarc
       create       Create a new conda environment from a list of specified packages
       info         Display information about current conda install
       init         Initialize conda for shell interaction
       install      Installs a list of packages into a specified conda environment
       list         List installed packages in a conda environment
       package      Low-level conda package utility
       remove       Remove a list of packages from a specified conda environment
       uninstall    Alias for conda remove
       run          Run an executable in a conda environment
       search       Search for packages and display associated information
       update       Updates conda packages to the latest compatible version
       upgrade      Alias for conda update

OPTIONS
       -h, --help   Show help message and exit
       -V, --version Show the conda version number and exit

EXAMPLES
       conda create -n myenv python
       conda activate myenv
       conda install -c conda-forge numpy
       conda list
       conda update --all
       conda remove numpy
       conda deactivate
"""
        
        # 尝试直接执行命令的--help
        try:
            if debug:
                print(f"调试: 执行 {command} --help")
                sys.stdout.flush()
                
            result = subprocess.run(
                [command, '--help'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10  # 设置合理的超时时间
            )
            
            # 检查--help输出
            if result.returncode == 0 and result.stdout:
                if debug:
                    print(f"调试: 成功获取--help输出，长度: {len(result.stdout)} 字符")
                    sys.stdout.flush()
                return result.stdout
                
            # 有些命令会输出到stderr
            if result.stderr and len(result.stderr) > 50:
                if debug:
                    print(f"调试: 从stderr获取到--help输出，长度: {len(result.stderr)} 字符")
                    sys.stdout.flush()
                return result.stderr
                
            # 如果--help失败，尝试-h
            if debug:
                print(f"调试: --help失败，尝试 {command} -h")
                sys.stdout.flush()
                
            result = subprocess.run(
                [command, '-h'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                if debug:
                    print(f"调试: 成功获取-h输出，长度: {len(result.stdout)} 字符")
                    sys.stdout.flush()
                return result.stdout
                
            # 有些命令会输出到stderr
            if result.stderr and len(result.stderr) > 50:
                if debug:
                    print(f"调试: 从stderr获取到-h输出，长度: {len(result.stderr)} 字符")
                    sys.stdout.flush()
                return result.stderr
                
        except FileNotFoundError:
            if debug:
                print(f"调试: 命令 {command} 不存在")
                sys.stdout.flush()
            return None
        except subprocess.TimeoutExpired:
            if debug:
                print(f"调试: 执行 {command} --help 超时")
                sys.stdout.flush()
            return None
        except Exception as e:
            if debug:
                print(f"调试: 执行 {command} --help 失败: {str(e)}")
                sys.stdout.flush()
            return None
            
        # 如果以上方法都失败，尝试通过bash运行
        try:
            if debug:
                print(f"调试: 通过bash执行 {command} --help")
                sys.stdout.flush()
                
            result = subprocess.run(
                ['bash', '-c', f'{command} --help'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                if debug:
                    print(f"调试: 成功通过bash获取--help输出")
                    sys.stdout.flush()
                return result.stdout
                
            if result.stderr and len(result.stderr) > 50:
                if debug:
                    print(f"调试: 通过bash从stderr获取--help输出")
                    sys.stdout.flush()
                return result.stderr
                
        except Exception as e:
            if debug:
                print(f"调试: 通过bash执行失败: {str(e)}")
                sys.stdout.flush()
            
        if debug:
            print(f"调试: 无法获取 {command} 的帮助信息")
            sys.stdout.flush()
        return None
            
    except Exception as e:
        if debug:
            print(f"调试: 获取帮助输出时发生异常: {str(e)}")
            sys.stdout.flush()
        return None

def save_man_page(content, command, section="1", output_dir=None):
    """
    保存man手册到指定路径
    
    Args:
        content: 手册内容
        command: 命令名称
        section: 手册章节号
        output_dir: 自定义输出目录，如果为None则使用默认目录
        
    Returns:
        bool: 是否保存成功
    """
    try:
        # 如果未提供输出目录，则从配置中获取或使用默认值
        if output_dir is None:
            try:
                from .config_manager import ConfigCache
                config = ConfigCache.get_config()
                output_dir = config.get("output", {}).get("man_dir", "/usr/local/share/man/zh_CN")
                print(f"未在命令行指定输出目录，使用配置值: {output_dir}")
                sys.stdout.flush()
            except Exception:
                output_dir = "/usr/local/share/man/zh_CN"
                print(f"未在配置中找到man_dir，使用默认目录：{output_dir}")
                sys.stdout.flush()
        else:
            print(f"使用命令行指定的输出目录: {output_dir}")
            sys.stdout.flush()
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"创建输出目录: {output_dir}")
                sys.stdout.flush()
            except PermissionError:
                print(f"无权限创建目录: {output_dir}，尝试使用sudo")
                sys.stdout.flush()
                subprocess.run(['sudo', 'mkdir', '-p', output_dir], check=True)
                
        # 创建章节目录
        section_dir = os.path.join(output_dir, f"man{section}")
        print(f"保存目标目录: {section_dir}")
        sys.stdout.flush()
        
        if not os.path.exists(section_dir):
            try:
                os.makedirs(section_dir, exist_ok=True)
            except PermissionError:
                print(f"无权限创建目录: {section_dir}，尝试使用sudo")
                sys.stdout.flush()
                subprocess.run(['sudo', 'mkdir', '-p', section_dir], check=True)
        
        # 保存文件
        target_file = os.path.join(section_dir, f"{command}.{section}")
        print(f"正在保存文件: {target_file}")
        sys.stdout.flush()
        
        # 检查是否有权限写入
        if os.access(section_dir, os.W_OK):
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已保存翻译结果到：{target_file}")
            sys.stdout.flush()
        else:
            print(f"无权限写入目录: {section_dir}，尝试使用sudo")
            sys.stdout.flush()
            
            # 先保存到临时文件
            temp_file = os.path.join('/tmp', f"{command}.{section}.temp")
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 使用sudo复制
            subprocess.run(['sudo', 'cp', temp_file, target_file], check=True)
            subprocess.run(['sudo', 'chmod', '644', target_file], check=True)
            print(f"已使用sudo保存翻译结果到：{target_file}")
            sys.stdout.flush()
            
            # 清理临时文件
            os.remove(temp_file)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"执行sudo命令失败: {str(e)}")
        sys.stdout.flush()
        print("您可能需要手动执行以下命令:")
        sys.stdout.flush()
        print(f"sudo mkdir -p {section_dir}")
        sys.stdout.flush()
        print(f"sudo cp /tmp/{command}.{section}.temp {target_file}")
        sys.stdout.flush()
        print(f"sudo chmod 644 {target_file}")
        sys.stdout.flush()
        return False
    except Exception as e:
        print(f"保存翻译结果失败: {str(e)}")
        sys.stdout.flush()
        if os.environ.get('MANZH_DEBUG') == '1':
            import traceback
            traceback.print_exc()
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
