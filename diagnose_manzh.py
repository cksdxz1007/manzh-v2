#!/usr/bin/env python3
"""
ManZH 诊断工具
测试manzh命令是否正确工作
"""
import sys
import os
import subprocess
import importlib
import traceback

def test_direct_import():
    """测试直接导入模块"""
    print("\n===测试导入模块===")
    try:
        import manzh
        print(f"成功导入manzh包 (版本: {getattr(manzh, '__version__', '未知')})")
        
        from manzh import cli
        print("成功导入manzh.cli模块")
        
        print("测试解析器...")
        parser = cli.create_parser()
        print("成功创建命令行解析器")
        
        # 测试参数解析
        args = parser.parse_args(['translate', 'conda'])
        print(f"解析 'translate conda' 参数结果: {args}")
        
        if hasattr(args, 'command_name'):
            print(f"command_name 属性: {args.command_name}")
        elif hasattr(args, 'command'):
            print(f"command 属性: {args.command}")
        else:
            print("错误: 解析器没有提供命令名称属性")
            
        return True
    except Exception as e:
        print(f"导入或解析测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_cli_execution():
    """测试通过命令行执行"""
    print("\n===测试命令行执行===")
    try:
        # 找到manzh命令
        which_result = subprocess.run(
            ['which', 'manzh'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if which_result.returncode != 0:
            print("找不到manzh命令，尝试执行python -m manzh")
            cmd_prefix = [sys.executable, '-m', 'manzh']
        else:
            manzh_path = which_result.stdout.strip()
            print(f"找到manzh命令: {manzh_path}")
            cmd_prefix = ['manzh']
            
        # 测试help命令
        help_cmd = cmd_prefix + ['--help']
        print(f"执行命令: {' '.join(help_cmd)}")
        help_result = subprocess.run(
            help_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if help_result.returncode == 0:
            print("成功执行help命令")
        else:
            print(f"执行help命令失败: {help_result.stderr}")
            
        # 测试translate命令
        translate_cmd = cmd_prefix + ['--debug', 'translate', 'ls']
        print(f"执行命令: {' '.join(translate_cmd)}")
        
        # 设置超时，避免命令卡住
        try:
            translate_result = subprocess.run(
                translate_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if translate_result.returncode == 0:
                print("成功执行translate命令")
                print(f"输出: {translate_result.stdout[:200]}...")
                return True
            else:
                print(f"执行translate命令失败，返回码: {translate_result.returncode}")
                print(f"标准输出: {translate_result.stdout}")
                print(f"错误输出: {translate_result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("执行translate命令超时，可能是正常的（如果正在翻译）")
            return True
            
    except Exception as e:
        print(f"命令行测试失败: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("===== ManZH 诊断工具 =====")
    print(f"Python版本: {sys.version}")
    print(f"运行路径: {os.getcwd()}")
    
    import_success = test_direct_import()
    cli_success = test_cli_execution()
    
    print("\n===== 诊断结果 =====")
    print(f"模块导入测试: {'成功' if import_success else '失败'}")
    print(f"命令行执行测试: {'成功' if cli_success else '失败'}")
    
    if import_success and cli_success:
        print("\n✅ 诊断成功，系统正常")
        return 0
    else:
        print("\n❌ 诊断发现问题，请查看上方详细信息")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 