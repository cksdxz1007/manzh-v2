from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
import os
import shutil
import subprocess

def post_install_message():
    """显示安装后的提示信息"""
    message = """
====================================
感谢安装 ManZH 中文手册翻译工具！
====================================

请运行以下命令来完成初始化配置：

    manzh config init

这将帮助您设置翻译服务和其他必要的配置。

命令行自动补全已配置，重新打开终端或运行以下命令使其生效：
    source ~/.zshrc  # 如果您使用zsh
    source ~/.bashrc # 如果您使用bash

如需帮助，请访问：https://github.com/cksdxz1007/ManZH
====================================
"""
    print(message)

def setup_auto_completion():
    """设置自动补全"""
    try:
        # 检测shell类型
        shell = os.environ.get('SHELL', '')
        if not shell:
            print("警告: 无法检测到shell类型，跳过自动补全设置")
            return
            
        # 添加补全脚本
        if 'zsh' in shell:
            setup_zsh_completion()
        elif 'bash' in shell:
            setup_bash_completion()
        else:
            print(f"当前shell类型 ({shell}) 不支持自动安装补全")
            print("您可以手动运行 'manzh completion' 来安装命令行自动补全")
    except Exception as e:
        print(f"设置自动补全时出错: {str(e)}")
        print("您可以手动运行 'manzh completion' 来安装命令行自动补全")

def setup_zsh_completion():
    """设置Zsh自动补全"""
    try:
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
                
        except Exception as e:
            print(f"生成补全脚本时出错: {str(e)}")
            print("您可以手动运行 'manzh completion' 来安装命令行自动补全")
            return False
        
        # 检查zshrc中是否已有配置
        rc_file = os.path.expanduser("~/.zshrc")
        if os.path.exists(rc_file):
            with open(rc_file, "r") as f:
                content = f.read()
                
            if "manzh 自动补全" not in content and "manzh-complete" not in content:
                with open(rc_file, "a") as f:
                    f.write("\n# manzh 自动补全配置\n")
                    f.write("autoload -U bashcompinit\n")
                    f.write("bashcompinit\n")
                    f.write(f"source {completion_script_path}\n")
        
        print("Zsh补全已配置，请运行 'source ~/.zshrc' 使其生效")
        return True
    except Exception as e:
        print(f"设置Zsh补全时出错: {str(e)}")
        print("您可以手动运行 'manzh completion' 来安装命令行自动补全")
        return False

def setup_bash_completion():
    """设置Bash自动补全"""
    try:
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
                
        except Exception as e:
            print(f"生成补全脚本时出错: {str(e)}")
            print("您可以手动运行 'manzh completion' 来安装命令行自动补全")
            return False
            
        # 检查bashrc中是否已有配置
        rc_file = os.path.expanduser("~/.bashrc")
        if os.path.exists(rc_file):
            with open(rc_file, "r") as f:
                content = f.read()
                
            if "manzh 自动补全" not in content and "manzh-complete" not in content:
                with open(rc_file, "a") as f:
                    f.write("\n# manzh 自动补全配置\n")
                    f.write("[ -f ~/.manzh-complete ] && source ~/.manzh-complete\n")
        
        print("Bash补全已配置，请运行 'source ~/.bashrc' 使其生效")
        return True
    except Exception as e:
        print(f"设置Bash补全时出错: {str(e)}")
        print("您可以手动运行 'manzh completion' 来安装命令行自动补全")
        return False

class PostInstallCommand(install):
    """安装后处理"""
    def run(self):
        install.run(self)
        # 设置自动补全
        self.execute(setup_auto_completion, [], msg="设置命令行自动补全...")
        self.execute(post_install_message, [], msg="显示安装后消息")
        # 在安装后运行命令检查，尝试卸载可能存在的旧版本
        try:
            subprocess.run(["pip", "uninstall", "-y", "manzh"], check=False)
        except Exception:
            pass

class PostDevelopCommand(develop):
    """开发模式安装后处理"""
    def run(self):
        develop.run(self)
        # 设置自动补全
        self.execute(setup_auto_completion, [], msg="设置命令行自动补全...")
        self.execute(post_install_message, [], msg="显示安装后消息")

# 清理命令，用于清理旧的安装
class CleanCommand:
    """删除可能冲突的旧文件和缓存"""
    def run(self):
        # 清理Python缓存文件
        dirs_to_clean = ['./__pycache__', './build', './dist', './manzh.egg-info']
        for d in dirs_to_clean:
            if os.path.exists(d):
                shutil.rmtree(d)
                print(f"清理目录: {d}")
        
        # 清理pyc文件
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))
                    print(f"清理文件: {os.path.join(root, file)}")
        
        # 尝试卸载已安装的包
        try:
            subprocess.run(["pip", "uninstall", "-y", "manzh"], check=False)
            print("卸载已安装的manzh包")
        except Exception as e:
            print(f"卸载包时出错: {str(e)}")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="manzh",
    version="1.1.4",
    author="Cynning Li",
    author_email="me@cynning.uk",
    description="Man手册中文翻译工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cksdxz1007/ManZH",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: System :: Systems Administration",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Utilities"
    ],
    python_requires=">=3.6",
    install_requires=requirements + [
        'importlib-metadata>=1.0; python_version < "3.8"',
        'argcomplete>=1.10.0',
    ],
    entry_points={
        "console_scripts": [
            "manzh=manzh.cli:main",
        ],
    },
    # 移除scripts字段，避免冲突
    # scripts=[
    #     "bin/manzh",
    # ],
    package_data={
        "manzh": ["config.json.example"],
    },
    data_files=[
        ("share/man/man1", ["docs/manzh.1"]),
    ],
    py_modules=["main"],
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
        'clean': CleanCommand,
    },
)
