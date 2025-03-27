import sys
import argparse
from .translate import TranslationQueue, create_translation_service
from .config_manager import load_config
from .man_utils import get_man_page, get_help_output, save_man_page
from .list_manuals import list_manuals
from .clean import interactive_clean
from .config_cli import interactive_config

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(description="ManZH - Man手册中文翻译工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # translate命令
    translate_parser = subparsers.add_parser("translate", help="翻译命令手册")
    translate_parser.add_argument("command", help="要翻译的命令名称")
    translate_parser.add_argument("-s", "--section", help="man手册章节号")
    translate_parser.add_argument("--service", help="使用的翻译服务")
    
    # config命令
    config_parser = subparsers.add_parser("config", help="配置翻译服务")
    
    # list命令
    list_parser = subparsers.add_parser("list", help="列出已翻译的手册")
    
    # clean命令
    clean_parser = subparsers.add_parser("clean", help="清理已翻译的手册")
    
    return parser

def translate_command(args):
    """处理translate命令"""
    try:
        # 加载配置
        config = load_config(service_name=args.service)
        
        # 获取man手册内容
        content = get_man_page(args.command, args.section)
        if not content:
            # 尝试获取--help输出
            content = get_help_output(args.command)
            if not content:
                print(f"错误：无法获取{args.command}的手册或帮助信息", file=sys.stderr)
                sys.exit(1)
        
        # 创建翻译服务
        service = create_translation_service(config)
        
        # 创建翻译队列
        queue = TranslationQueue()
        chunks = queue.prepare_content(content)
        
        # 添加翻译任务
        for i, chunk in enumerate(chunks):
            queue.add_chunk(i, chunk)
        
        # 设置系统提示
        system_prompt = (
            "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。"
            "保持原始格式，不要修改任何命令名称、选项和示例代码。翻译时注意专业性和准确性。"
        )
        
        # 开始翻译
        print("开始翻译...", file=sys.stderr)
        
        # 处理每个块
        while True:
            chunk_data = queue.get_chunk()
            if chunk_data is None:
                break
                
            index, content = chunk_data
            try:
                result = service.translate(content, system_prompt)
                queue.add_result(index, result)
            except Exception as e:
                print(f"\n翻译块 {index} 失败：{str(e)}", file=sys.stderr)
                queue.add_failed_chunk(index)
        
        # 获取完整翻译结果
        translated_content = queue.get_ordered_results()
        
        # 保存翻译结果
        section = args.section or "1"
        if save_man_page(translated_content, args.command, section):
            print("\n翻译完成！", file=sys.stderr)
        else:
            print("\n翻译完成，但保存失败", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"翻译过程中发生错误：{str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        # 显示交互式菜单
        while True:
            print("\nManZH - Man手册中文翻译工具")
            print("=========================")
            print("1. 翻译命令手册")
            print("2. 配置翻译服务")
            print("3. 查看已翻译手册")
            print("4. 清理已翻译手册")
            print("5. 退出程序")
            
            choice = input("\n请选择操作 [1-5]: ").strip()
            
            if choice == "1":
                command = input("请输入要翻译的命令名称：").strip()
                section = input("请输入章节号（可选）：").strip()
                service = input("请输入要使用的翻译服务（可选）：").strip()
                
                args = argparse.Namespace(
                    command=command,
                    section=section or None,
                    service=service or None
                )
                translate_command(args)
                
            elif choice == "2":
                interactive_config()
                
            elif choice == "3":
                list_manuals()
                
            elif choice == "4":
                interactive_clean()
                
            elif choice == "5":
                break
                
            else:
                print("无效的选择，请重试")
    else:
        # 处理命令行参数
        if args.command == "translate":
            translate_command(args)
        elif args.command == "config":
            interactive_config()
        elif args.command == "list":
            list_manuals()
        elif args.command == "clean":
            interactive_clean()

if __name__ == "__main__":
    main()
