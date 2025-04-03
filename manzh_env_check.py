#!/usr/bin/env python3
"""
ManZH环境检查脚本
用于诊断ManZH运行环境，确认配置和环境变量正确
"""
import os
import sys
import json
import platform
import subprocess

def print_section(title):
    """打印带分隔线的标题"""
    print("\n" + "=" * 50)
    print(f"   {title}")
    print("=" * 50)

def check_python():
    """检查Python环境"""
    print_section("Python环境")
    print(f"Python版本: {platform.python_version()}")
    print(f"Python路径: {sys.executable}")
    print(f"Python实现: {platform.python_implementation()}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    print("\nPython路径:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    print("\n环境变量:")
    for var in ["PYTHONPATH", "PYTHONUNBUFFERED", "PYTHONIOENCODING"]:
        print(f"  {var}: {os.environ.get(var, '未设置')}")

def check_manzh_config():
    """检查ManZH配置文件"""
    print_section("ManZH配置")
    
    # 检查配置目录
    config_dir = os.path.expanduser("~/.config/manzh")
    config_file = os.path.join(config_dir, "services.json")
    
    print(f"配置目录: {config_dir}")
    print(f"配置存在: {'是' if os.path.exists(config_dir) else '否'}")
    
    print(f"\n配置文件: {config_file}")
    print(f"文件存在: {'是' if os.path.exists(config_file) else '否'}")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print("\n配置内容摘要:")
            if "services" in config:
                services = config["services"]
                print(f"  服务数量: {len(services)}")
                for name in services:
                    service = services[name]
                    print(f"  - {name} ({service.get('type', '未知类型')})")
            
            print(f"  默认服务: {config.get('default_service', '未设置')}")
        except Exception as e:
            print(f"\n读取配置文件失败: {str(e)}")

def check_manzh_package():
    """检查ManZH包结构"""
    print_section("ManZH包结构")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    manzh_dir = os.path.join(script_dir, "manzh")
    
    print(f"脚本目录: {script_dir}")
    print(f"ManZH包目录: {manzh_dir}")
    print(f"目录存在: {'是' if os.path.exists(manzh_dir) else '否'}")
    
    if os.path.exists(manzh_dir):
        print("\n包内文件:")
        try:
            files = sorted(os.listdir(manzh_dir))
            for file in files:
                file_path = os.path.join(manzh_dir, file)
                file_type = "目录" if os.path.isdir(file_path) else "文件"
                file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                print(f"  - {file} ({file_type}, {file_size} 字节)")
        except Exception as e:
            print(f"  列出文件失败: {str(e)}")
    
    # 检查模块导入
    print("\n模块导入测试:")
    try:
        import manzh
        print(f"  导入manzh包成功, 版本: {getattr(manzh, '__version__', '未知')}")
        
        from manzh import cli
        print("  导入manzh.cli模块成功")
        
        from manzh.translate import TranslationQueue
        print("  导入manzh.translate.TranslationQueue类成功")
    except Exception as e:
        print(f"  导入失败: {str(e)}")

def check_command(command):
    """检查shell命令是否可用"""
    try:
        result = subprocess.run(
            ["which", command], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception:
        return False, None

def check_dependencies():
    """检查依赖工具"""
    print_section("系统依赖")
    
    commands = ["man", "col", "groff", "sudo"]
    for cmd in commands:
        exists, path = check_command(cmd)
        status = f"{'可用' if exists else '不可用'}"
        path_info = f" - 路径: {path}" if path else ""
        print(f"{cmd}: {status}{path_info}")

def run_simple_test():
    """运行简单测试"""
    print_section("简单测试")
    
    try:
        print("测试stdout输出:")
        for i in range(5):
            print(f"标准输出测试 {i}")
            sys.stdout.flush()
        
        print("\n测试stderr输出:")
        for i in range(5):
            print(f"标准错误测试 {i}", file=sys.stderr)
            sys.stderr.flush()
    except Exception as e:
        print(f"测试失败: {str(e)}")

def main():
    """主函数"""
    print("ManZH环境检查开始...")
    
    # 设置环境变量确保输出不缓冲
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # 运行各项检查
    check_python()
    check_manzh_config()
    check_manzh_package()
    check_dependencies()
    run_simple_test()
    
    print("\n检查完成！请把以上信息提供给技术支持。")

if __name__ == "__main__":
    main() 