import sys
from .man_utils import list_translated_manuals

def list_manuals(man_dir="/usr/local/share/man/zh_CN"):
    """
    列出所有已翻译的手册
    
    Args:
        man_dir: man手册目录
    """
    try:
        manuals = list_translated_manuals(man_dir)
        
        if not manuals:
            print("未找到已翻译的手册")
            return
            
        print("\n已翻译的手册列表：")
        print("================\n")
        
        for section, commands in sorted(manuals.items()):
            print(f"第 {section} 章节:")
            print("-" * 20)
            # 按列显示命令，每行5个
            for i in range(0, len(commands), 5):
                row = commands[i:i+5]
                print("  ".join(row))
            print()
            
    except Exception as e:
        print(f"列出手册时发生错误：{str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    list_manuals()
