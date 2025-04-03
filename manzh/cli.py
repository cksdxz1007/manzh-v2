import sys
import argparse
import os
import subprocess
from .translate import TranslationQueue, create_translation_service
from .config_manager import load_config
from .man_utils import get_man_page, get_help_output, save_man_page
from .list_manuals import list_manuals
from .clean import interactive_clean
from .config_cli import interactive_config, show_config, interactive_init_config
from .optimize import optimize_command, interactive_optimize

# 设置环境变量确保输出不缓冲
os.environ["PYTHONUNBUFFERED"] = "1"

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(description="ManZH - Man手册中文翻译工具")
    parser.add_argument("-d", "--debug", action="store_true", help="启用详细调试输出")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # translate命令
    translate_parser = subparsers.add_parser("translate", help="翻译命令手册")
    translate_parser.add_argument("command_name", metavar="command", help="要翻译的命令名称")
    translate_parser.add_argument("-s", "--section", help="man手册章节号")
    translate_parser.add_argument("--service", help="使用的翻译服务")
    translate_parser.add_argument("-d", "--debug", action="store_true", help="启用详细调试输出")
    
    # config命令
    config_parser = subparsers.add_parser("config", help="配置翻译服务")
    config_subparsers = config_parser.add_subparsers(dest="subcommand", help="配置操作")
    
    # config init子命令
    init_parser = config_subparsers.add_parser("init", help="初始化配置")
    
    # config show子命令
    show_parser = config_subparsers.add_parser("show", help="显示当前配置")
    
    # list命令
    list_parser = subparsers.add_parser("list", help="列出已翻译的手册")
    
    # clean命令
    clean_parser = subparsers.add_parser("clean", help="清理已翻译的手册")
    
    # optimize命令
    optimize_parser = subparsers.add_parser("optimize", help="优化已翻译的手册，移除无意义内容")
    optimize_parser.add_argument("-f", "--file", help="要优化的单个手册文件路径")
    optimize_parser.add_argument("-c", "--command", dest="command_name", help="命令名称")
    optimize_parser.add_argument("-s", "--section", help="man手册章节号")
    optimize_parser.add_argument("-d", "--dir", help="手册目录路径")
    optimize_parser.add_argument("-r", "--recursive", action="store_true", help="递归处理子目录")
    optimize_parser.add_argument("--debug", action="store_true", help="启用详细调试输出")
    
    return parser

def translate_command(args):
    """处理translate命令"""
    debug_mode = args.debug if hasattr(args, 'debug') else False
    
    try:
        # 取得要翻译的命令名称
        command = args.command_name if hasattr(args, 'command_name') else args.command
        
        print(f"开始处理命令: {command}")
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
            print("错误：无法加载配置文件，请先运行 'manzh config init' 创建配置")
            sys.stdout.flush()
            sys.exit(1)
            
        print(f"使用服务: {config.get('default_service', '未指定')}")
        sys.stdout.flush()
        
        # 检查命令是否存在
        if debug_mode:
            print(f"检查命令 '{command}' 是否可用...")
            sys.stdout.flush()
            
        # 尝试使用which命令检查命令是否存在
        which_result = subprocess.run(
            ['which', command], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if which_result.returncode != 0 and command not in ['cd', 'source', 'alias', 'export', 'pwd', 'echo', 'set']:
            if debug_mode:
                print(f"警告: 命令 '{command}' 可能不存在或不在PATH中")
                sys.stdout.flush()
                print("继续尝试获取手册或帮助信息...")
                sys.stdout.flush()
        else:
            if debug_mode:
                print(f"命令 '{command}' 的路径: {which_result.stdout.strip()}")
                sys.stdout.flush()
        
        # 获取man手册内容
        print(f"正在获取 {command} 手册内容...")
        sys.stdout.flush()
        content = get_man_page(command, args.section)
        if not content:
            print(f"找不到 {command} 的man手册，尝试获取帮助信息...")
            sys.stdout.flush()
            # 尝试获取--help输出
            content = get_help_output(command)
            if not content:
                print(f"错误：无法获取{command}的手册或帮助信息")
                sys.stdout.flush()
                
                # 提供更明确的错误信息
                print("\n可能的原因:")
                sys.stdout.flush()
                print(f"1. 命令 '{command}' 可能不存在")
                sys.stdout.flush()
                print(f"2. 该命令可能没有man手册或--help选项")
                sys.stdout.flush()
                print(f"3. 需要特殊方式运行该命令")
                sys.stdout.flush()
                
                print("\n解决方案:")
                sys.stdout.flush()
                print("- 确认命令拼写是否正确")
                sys.stdout.flush()
                print("- 尝试先手动运行该命令")
                sys.stdout.flush()
                print("- 对于特殊命令，可以先手动获取帮助信息，然后手动创建翻译文件")
                sys.stdout.flush()
                
                sys.exit(1)
                
            print(f"成功获取 {command} 的帮助信息")
            sys.stdout.flush()
        else:
            print(f"成功获取 {command} 的man手册")
            sys.stdout.flush()
            
        if debug_mode:
            content_preview = content[:500] if len(content) > 500 else content
            print("\n获取到的内容前500字符:")
            print(content_preview)
            print(f"\n... (总计 {len(content)} 字符)")
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
        while True:
            chunk_data = queue.get_chunk()
            if chunk_data is None:
                break
                
            index, content = chunk_data
            try:
                print(f"正在翻译块 {index+1}/{len(chunks)}...")
                sys.stdout.flush()
                
                if debug_mode:
                    preview = content[:100] if len(content) > 100 else content
                    print(f"块内容前100字符: {preview}")
                    sys.stdout.flush()
                    
                result = service.translate(content, system_prompt)
                
                if debug_mode:
                    result_preview = result[:100] if len(result) > 100 else result
                    print(f"翻译结果前100字符: {result_preview}")
                    sys.stdout.flush()
                    
                queue.add_result(index, result)
                print(f"块 {index+1}/{len(chunks)} 翻译完成")
                sys.stdout.flush()
                
            except Exception as e:
                print(f"\n翻译块 {index+1}/{len(chunks)} 失败：{str(e)}")
                sys.stdout.flush()
                
                if debug_mode:
                    import traceback
                    traceback.print_exc()
                    
                # 记录失败的块    
                queue.add_failed_chunk(index)
                
                # 尝试继续翻译其他块
                print("继续翻译其他块...")
                sys.stdout.flush()
        
        # 检查是否有翻译失败的块
        if hasattr(queue, 'failed_chunks') and queue.failed_chunks:
            print(f"\n警告：有 {len(queue.failed_chunks)} 个块翻译失败")
            sys.stdout.flush()
            
            if len(queue.failed_chunks) >= len(chunks) / 2:
                print("错误：太多块翻译失败，无法生成有用的结果")
                sys.stdout.flush()
                sys.exit(1)
                
            print("继续合并可用的翻译结果...")
            sys.stdout.flush()
        
        # 获取完整翻译结果
        print("正在合并翻译结果...")
        sys.stdout.flush()
        translated_content = queue.get_ordered_results()
        if not translated_content:
            print("错误：翻译失败，没有获得有效的翻译结果")
            sys.stdout.flush()
            sys.exit(1)
        
        # 检查翻译结果是否包含中文内容
        chinese_chars = sum(1 for char in translated_content if '\u4e00' <= char <= '\u9fff')
        if chinese_chars < len(translated_content) * 0.1:
            if debug_mode:
                print(f"警告：翻译结果中中文字符比例过低 ({chinese_chars}/{len(translated_content)})")
                sys.stdout.flush()
                print("继续处理，但结果可能不是有效的中文翻译")
                sys.stdout.flush()
        
        # 保存翻译结果
        section = args.section or "1"
        print(f"正在保存翻译结果到 man 章节 {section}...")
        sys.stdout.flush()
        if save_man_page(translated_content, command, section):
            print("\n翻译完成！")
            print(f"可以使用 'man -M /usr/local/share/man/zh_CN {command}' 查看翻译结果")
            sys.stdout.flush()
        else:
            print("\n翻译完成，但保存失败")
            print("可能需要使用sudo权限来保存结果")
            sys.stdout.flush()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n操作已取消")
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
        from .config_manager import get_default_config_path
        import json
        
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

def main():
    """主函数"""
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
        while True:
            print("\nManZH - Man手册中文翻译工具")
            sys.stdout.flush()
            print("=========================")
            sys.stdout.flush()
            print("1. 翻译命令手册")
            sys.stdout.flush()
            print("2. 配置翻译服务")
            sys.stdout.flush()
            print("3. 查看已翻译手册")
            sys.stdout.flush()
            print("4. 清理已翻译手册")
            sys.stdout.flush()
            print("5. 优化已翻译手册")
            sys.stdout.flush()
            print("6. 退出程序")
            sys.stdout.flush()
            
            choice = input("\n请选择操作 [1-6]: ").strip()
            
            if choice == "1":
                command = input("请输入要翻译的命令名称：").strip()
                section = input("请输入章节号（可选）：").strip()
                service = input("请输入要使用的翻译服务（可选）：").strip()
                debug = input("是否启用调试模式？(y/N): ").strip().lower() == 'y'
                
                args = argparse.Namespace(
                    command_name=command,
                    section=section or None,
                    service=service or None,
                    debug=debug
                )
                translate_command(args)
                
            elif choice == "2":
                interactive_config()
                
            elif choice == "3":
                list_manuals()
                
            elif choice == "4":
                interactive_clean()
                
            elif choice == "5":
                interactive_optimize()
                
            elif choice == "6":
                print("退出程序")
                sys.stdout.flush()
                break
                
            else:
                print("无效的选择，请重试")
                sys.stdout.flush()
    else:
        # 处理命令行参数
        if args.command == "translate":
            translate_command(args)
        elif args.command == "config":
            if hasattr(args, 'subcommand') and args.subcommand == "init":
                # 运行初始化配置并检查单个服务
                interactive_init_config()
                check_and_set_default_service()
            elif hasattr(args, 'subcommand') and args.subcommand == "show":
                show_config()
            else:
                interactive_config()
        elif args.command == "list":
            list_manuals()
        elif args.command == "clean":
            interactive_clean()
        elif args.command == "optimize":
            optimize_command(args)
        else:
            print(f"不支持的命令: {args.command}")
            sys.stdout.flush()
            parser.print_help()

if __name__ == "__main__":
    main()
