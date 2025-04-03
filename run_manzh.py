#!/usr/bin/env python3
"""
ManZH - Man手册中文翻译工具运行脚本
确保环境变量正确设置并运行manzh命令
"""
import os
import sys
import subprocess

def main():
    # 设置环境变量确保输出不缓冲
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # 获取当前脚本所在目录，用于设置PYTHONPATH
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ["PYTHONPATH"] = script_dir
    
    print("启动ManZH - Man手册中文翻译工具...")
    print(f"工作目录: {script_dir}")
    
    # 如果没有参数，显示帮助信息
    if len(sys.argv) == 1:
        print("用法: python run_manzh.py [命令] [选项...]")
        print("例如: python run_manzh.py translate ls -d")
        print("\n可用命令:")
        print("  translate  翻译指定命令的man手册")
        print("  config     配置翻译服务")
        print("  list       列出已翻译的手册")
        print("  clean      清理已翻译的手册")
        return
    
    print(f"执行命令: {' '.join(sys.argv[1:])}")
    
    # 确保当前目录在Python路径中
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # 判断是否为调试模式
    debug_mode = "-d" in sys.argv or "--debug" in sys.argv
    if debug_mode:
        print("调试模式已启用")
    
    try:
        # 使用subprocess运行，确保输出实时显示
        cmd = [sys.executable, "-m", "manzh.cli"]
        cmd.extend(sys.argv[1:])
        
        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = script_dir
        
        print("开始执行...\n")
        sys.stdout.flush()
        
        # 使用实时输出模式运行
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,  # 行缓冲
            env=env     # 传递环境变量
        )
        
        # 实时显示输出
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
        
        # 等待进程结束
        return_code = process.wait()
        if return_code != 0:
            print(f"\n命令执行失败，返回码: {return_code}")
            sys.exit(return_code)
        else:
            print("\n命令执行完成")
        
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        if debug_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 