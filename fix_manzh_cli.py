#!/usr/bin/env python3
"""
修复ManZH CLI的输出问题
这个脚本会直接修改manzh/cli.py文件，修复其输出重定向或缓冲问题
"""
import os
import sys
import re

def fix_cli_file():
    """
    修复manzh/cli.py文件的输出问题
    """
    cli_file = os.path.join("manzh", "cli.py")
    
    if not os.path.exists(cli_file):
        print(f"错误: 找不到文件 {cli_file}")
        return False
    
    try:
        # 读取文件内容
        with open(cli_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原始文件
        backup_file = cli_file + ".bak"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已创建备份文件: {backup_file}")
        
        # 修改文件导入部分
        if "import os" not in content:
            content = re.sub(r'import sys', 'import os\nimport sys', content)
        
        # 添加环境变量设置
        if "PYTHONUNBUFFERED" not in content:
            # 在文件开头添加环境变量设置
            content = re.sub(r'(import.*?\n\n)', r'\1# 设置环境变量确保输出不缓冲\nos.environ["PYTHONUNBUFFERED"] = "1"\n\n', content)
        
        # 确保所有print语句后都有flush操作
        modified_content = []
        for line in content.split('\n'):
            modified_content.append(line)
            if 'print(' in line and 'file=sys.stderr' in line and 'sys.stderr.flush()' not in line:
                # 计算缩进级别
                indent = len(line) - len(line.lstrip())
                flush_line = ' ' * indent + 'sys.stderr.flush()'
                modified_content.append(flush_line)
            elif 'print(' in line and 'file=sys.stderr' not in line and 'sys.stdout.flush()' not in line:
                # 计算缩进级别
                indent = len(line) - len(line.lstrip())
                flush_line = ' ' * indent + 'sys.stdout.flush()'
                modified_content.append(flush_line)
        
        new_content = '\n'.join(modified_content)
        
        # 保存修改后的文件
        with open(cli_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"成功修复文件: {cli_file}")
        return True
        
    except Exception as e:
        print(f"修复文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_translate_file():
    """
    修复manzh/translate.py文件的输出问题
    """
    translate_file = os.path.join("manzh", "translate.py")
    
    if not os.path.exists(translate_file):
        print(f"错误: 找不到文件 {translate_file}")
        return False
    
    try:
        # 读取文件内容
        with open(translate_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原始文件
        backup_file = translate_file + ".bak"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已创建备份文件: {backup_file}")
        
        # 确保所有print语句后都有flush操作
        modified_content = []
        for line in content.split('\n'):
            modified_content.append(line)
            if 'print(' in line and 'file=sys.stderr' in line and 'sys.stderr.flush()' not in line:
                # 计算缩进级别
                indent = len(line) - len(line.lstrip())
                flush_line = ' ' * indent + 'sys.stderr.flush()'
                modified_content.append(flush_line)
            elif 'print(' in line and 'file=sys.stderr' not in line and 'sys.stdout.flush()' not in line:
                # 计算缩进级别
                indent = len(line) - len(line.lstrip())
                flush_line = ' ' * indent + 'sys.stdout.flush()'
                modified_content.append(flush_line)
        
        new_content = '\n'.join(modified_content)
        
        # 保存修改后的文件
        with open(translate_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"成功修复文件: {translate_file}")
        return True
        
    except Exception as e:
        print(f"修复文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始修复ManZH CLI的输出问题...")
    
    # 修复cli.py文件
    if fix_cli_file():
        print("成功修复manzh/cli.py文件")
    else:
        print("修复manzh/cli.py文件失败")
    
    # 修复translate.py文件
    if fix_translate_file():
        print("成功修复manzh/translate.py文件")
    else:
        print("修复manzh/translate.py文件失败")
    
    print("\n修复完成！请尝试重新运行 'python run_manzh.py translate <命令> -d'")

if __name__ == "__main__":
    main() 