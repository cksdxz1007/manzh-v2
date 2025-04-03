#!/usr/bin/env python3
"""
ManZH修复程序
这个脚本提供了一个修复版本的manzh命令行工具
"""
import os
import sys
import json
import argparse
import subprocess
import shutil
from manzh.config_manager import load_config, get_default_config_path
from manzh.man_utils import get_man_page, get_help_output, save_man_page
from manzh.translate import TranslationQueue, create_translation_service

def translate_command_fixed(args):
    """修复版的translate_command函数"""
    debug_mode = args.debug if hasattr(args, 'debug') else False
    
    try:
        print(f"开始处理命令: {args.command}")
        sys.stdout.flush()
        
        # 如果开启了调试模式，设置环境变量
        if debug_mode:
            print("调试模式已启用，将显示详细输出")
            sys.stdout.flush()
            os.environ['MANZH_DEBUG'] = '1'
        
        # 加载配置
        print("正在加载配置...")
        sys.stdout.flush()
        config = load_config(service_name=args.service)
        if not config:
            print("错误：无法加载配置文件，请先运行 'python manzh_fixer.py config init' 创建配置")
            sys.stdout.flush()
            sys.exit(1)
        
        # 获取配置中的服务名
        service_name = config.get('default_service', '未指定')
        print(f"使用服务: {service_name}")
        sys.stdout.flush()
        
        # 获取man手册内容
        print(f"正在获取 {args.command} 手册内容...")
        sys.stdout.flush()
        content = get_man_page(args.command, args.section)
        if not content:
            print(f"找不到 {args.command} 的man手册，尝试获取帮助信息...")
            sys.stdout.flush()
            # 尝试获取--help输出
            content = get_help_output(args.command)
            if not content:
                print(f"错误：无法获取{args.command}的手册或帮助信息")
                sys.stdout.flush()
                sys.exit(1)
            print(f"成功获取 {args.command} 的帮助信息")
            sys.stdout.flush()
        else:
            print(f"成功获取 {args.command} 的man手册")
            sys.stdout.flush()
            
        if debug_mode:
            print("\n获取到的内容前500字符:")
            print(content[:500])
            print("\n...")
            sys.stdout.flush()
        
        # 创建翻译服务
        print("正在初始化翻译服务...")
        sys.stdout.flush()
        try:
            service = create_translation_service(config)
            print("翻译服务初始化成功")
            sys.stdout.flush()
        except Exception as e:
            print(f"错误：初始化翻译服务失败 - {str(e)}")
            sys.stdout.flush()
            sys.exit(1)
        
        # 创建翻译队列
        print("正在准备翻译内容...")
        sys.stdout.flush()
        queue = TranslationQueue()
        chunks = queue.prepare_content(content)
        print(f"内容已分割为 {len(chunks)} 个块")
        sys.stdout.flush()
        
        # 添加翻译任务
        for i, chunk in enumerate(chunks):
            queue.add_chunk(i, chunk)
        
        # 设置系统提示
        system_prompt = (
            "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。"
            "保持原始格式，不要修改任何命令名称、选项和示例代码。翻译时注意专业性和准确性。"
        )
        
        # 开始翻译
        print("开始翻译...")
        sys.stdout.flush()
        
        # 处理每个块
        for i in range(len(chunks)):
            chunk_data = queue.get_chunk()
            if chunk_data is None:
                break
                
            index, chunk_content = chunk_data
            try:
                print(f"正在翻译块 {index+1}/{len(chunks)}...")
                sys.stdout.flush()
                
                if debug_mode:
                    print(f"块内容前100字符: {chunk_content[:100]}")
                    sys.stdout.flush()
                    
                result = service.translate(chunk_content, system_prompt)
                
                if debug_mode:
                    print(f"翻译结果前100字符: {result[:100]}")
                    sys.stdout.flush()
                    
                queue.add_result(index, result)
                print(f"块 {index+1}/{len(chunks)} 翻译完成")
                sys.stdout.flush()
            except Exception as e:
                print(f"\n翻译块 {index+1}/{len(chunks)} 失败：{str(e)}")
                sys.stdout.flush()
                queue.add_failed_chunk(index)
        
        # 获取完整翻译结果
        print("正在合并翻译结果...")
        sys.stdout.flush()
        translated_content = queue.get_ordered_results()
        if not translated_content:
            print("错误：翻译失败，没有获得有效的翻译结果")
            sys.stdout.flush()
            sys.exit(1)
        
        # 保存翻译结果
        section = args.section or "1"
        print(f"正在保存翻译结果到 man 章节 {section}...")
        sys.stdout.flush()
        if save_man_page(translated_content, args.command, section):
            print("\n翻译完成！")
            sys.stdout.flush()
        else:
            print("\n翻译完成，但保存失败")
            sys.stdout.flush()
            sys.exit(1)
            
    except Exception as e:
        print(f"翻译过程中发生错误：{str(e)}")
        sys.stdout.flush()
        if debug_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def check_and_set_default_service():
    """
    检查配置文件，如果只有一个服务但没有设置默认服务，则自动设置为默认服务
    
    Returns:
        bool: 是否成功设置默认服务
    """
    try:
        config_path = get_default_config_path()
        if not os.path.exists(config_path):
            print(f"配置文件不存在: {config_path}")
            sys.stdout.flush()
            return False
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 检查服务列表
        if 'services' not in config or not config['services']:
            print("配置文件中没有配置服务")
            sys.stdout.flush()
            return False
            
        services = config['services']
        if len(services) == 1 and ('default_service' not in config or not config['default_service']):
            # 只有一个服务，将其设置为默认服务
            service_name = list(services.keys())[0]
            config['default_service'] = service_name
            
            # 保存更新后的配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            print(f"已自动将 {service_name} 设置为默认服务")
            sys.stdout.flush()
            return True
            
        return False
    except Exception as e:
        print(f"检查默认服务时出错: {str(e)}")
        sys.stdout.flush()
        return False

def run_config_init():
    """
    运行配置初始化，并在完成后检查是否需要自动设置默认服务
    """
    try:
        # 调用原始的配置初始化工具
        cmd = [sys.executable, "-m", "manzh.cli", "config", "init"]
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(cmd, env=env)
        
        if result.returncode == 0:
            # 配置初始化成功，检查是否需要设置默认服务
            check_and_set_default_service()
    except Exception as e:
        print(f"配置初始化过程中发生错误: {str(e)}")
        sys.stdout.flush()
        sys.exit(1)

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(description="ManZH - Man手册中文翻译工具 (修复版)")
    parser.add_argument("-d", "--debug", action="store_true", help="启用详细调试输出")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # translate命令
    translate_parser = subparsers.add_parser("translate", help="翻译命令手册")
    translate_parser.add_argument("cmd", help="要翻译的命令名称")
    translate_parser.add_argument("-s", "--section", help="man手册章节号")
    translate_parser.add_argument("--service", help="使用的翻译服务")
    translate_parser.add_argument("-d", "--debug", action="store_true", help="启用详细调试输出")
    
    # config命令
    config_parser = subparsers.add_parser("config", help="配置翻译服务")
    config_subparsers = config_parser.add_subparsers(dest="subcommand", help="配置操作")
    
    # config init子命令
    init_parser = config_subparsers.add_parser("init", help="初始化配置")
    
    # install命令 - 将自己安装为系统命令
    install_parser = subparsers.add_parser("install", help="将此脚本安装为系统命令")
    
    return parser

def install_as_system_command():
    """
    将脚本安装为系统命令
    通过创建符号链接或复制脚本到系统PATH中的位置
    """
    try:
        # 获取当前脚本路径
        script_path = os.path.abspath(__file__)
        print(f"当前脚本路径: {script_path}")
        sys.stdout.flush()
        
        # 确定目标路径
        target_dirs = [
            '/usr/local/bin',  # macOS和大多数Linux系统
            '/usr/bin',        # 其他Linux系统
            os.path.expanduser('~/.local/bin')  # 用户目录（不需要管理员权限）
        ]
        
        # 检查目标目录是否存在且可写
        for target_dir in target_dirs:
            if os.path.exists(target_dir) and os.access(target_dir, os.W_OK):
                target_path = os.path.join(target_dir, 'manzh')
                
                # 检查是否已存在，并备份
                if os.path.exists(target_path):
                    backup_path = f"{target_path}.bak"
                    print(f"已存在manzh命令，备份到: {backup_path}")
                    sys.stdout.flush()
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(target_path, backup_path)
                
                # 创建符号链接或复制文件
                try:
                    os.symlink(script_path, target_path)
                    print(f"已创建符号链接: {target_path} -> {script_path}")
                    sys.stdout.flush()
                except OSError:
                    # 如果无法创建符号链接，则复制文件
                    shutil.copy2(script_path, target_path)
                    os.chmod(target_path, 0o755)  # 设置可执行权限
                    print(f"已复制脚本到: {target_path}")
                    sys.stdout.flush()
                
                print(f"\n安装成功！现在可以使用 'manzh' 命令运行此脚本")
                print(f"示例: manzh translate ls")
                sys.stdout.flush()
                return True
        
        # 如果没有找到合适的目录
        print("\n错误: 找不到可写的系统目录。您可能需要使用sudo运行此命令。")
        print("示例: sudo python manzh_fixer.py install")
        sys.stdout.flush()
        return False
    
    except Exception as e:
        print(f"安装过程中发生错误: {str(e)}")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    # 设置环境变量确保输出不缓冲
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # 解析命令行参数
    parser = create_parser()
    args = parser.parse_args()
    
    # 检查调试模式
    debug_mode = args.debug if hasattr(args, 'debug') else False
    if debug_mode:
        print("调试模式已启用")
        sys.stdout.flush()
        os.environ['MANZH_DEBUG'] = '1'
    
    if not args.command:
        # 显示交互式菜单
        print("\nManZH - Man手册中文翻译工具 (修复版)")
        print("==============================================")
        print("1. 翻译命令手册")
        print("2. 配置翻译服务")
        print("3. 检查配置并设置默认服务")
        print("4. 安装为系统命令")
        print("0. 退出程序")
        sys.stdout.flush()
        
        choice = input("\n请选择操作 [0-4]: ").strip()
        
        if choice == "1":
            command = input("请输入要翻译的命令名称：").strip()
            section = input("请输入章节号（可选）：").strip()
            service = input("请输入要使用的翻译服务（可选）：").strip()
            debug = input("是否启用调试模式？(y/N): ").strip().lower() == 'y'
            
            translate_args = argparse.Namespace(
                command=command,
                section=section or None,
                service=service or None,
                debug=debug
            )
            translate_command_fixed(translate_args)
            
        elif choice == "2":
            print("\n配置类型:")
            print("1. 初始化配置 (创建新配置)")
            print("2. 配置管理 (修改现有配置)")
            print("0. 返回上级菜单")
            sys.stdout.flush()
            
            config_choice = input("\n请选择操作 [0-2]: ").strip()
            
            if config_choice == "1":
                run_config_init()
            elif config_choice == "2":
                # 调用原始配置工具
                cmd = [sys.executable, "-m", "manzh.cli", "config"]
                env = os.environ.copy()
                env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
                subprocess.run(cmd, env=env)
            
        elif choice == "3":
            if check_and_set_default_service():
                print("已检查并更新默认服务")
            else:
                print("没有需要自动设置的默认服务")
            sys.stdout.flush()
        
        elif choice == "4":
            install_as_system_command()
            
        elif choice == "0":
            print("退出程序")
            sys.stdout.flush()
            return
        else:
            print("无效的选择，请重试")
            sys.stdout.flush()
            
    else:
        # 处理命令行参数
        if args.command == "translate":
            # 将cmd转换为command（与原始接口兼容）
            args.command = args.cmd
            translate_command_fixed(args)
        elif args.command == "config":
            if hasattr(args, 'subcommand'):
                if args.subcommand == "init":
                    run_config_init()
                else:
                    # 调用原始配置工具
                    cmd = [sys.executable, "-m", "manzh.cli", "config"]
                    if args.subcommand:
                        cmd.append(args.subcommand)
                        
                    env = os.environ.copy()
                    env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
                    
                    subprocess.run(cmd, env=env)
            else:
                # 调用原始配置工具
                cmd = [sys.executable, "-m", "manzh.cli", "config"]
                env = os.environ.copy()
                env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
                subprocess.run(cmd, env=env)
        elif args.command == "install":
            install_as_system_command()
        else:
            print(f"不支持的命令: {args.command}")
            sys.stdout.flush()
            parser.print_help()

if __name__ == "__main__":
    main() 