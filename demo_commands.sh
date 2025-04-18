#!/bin/bash
# ManZH 命令行模式演示
echo "======================================="
echo "ManZH 命令行模式演示"
echo "======================================="
echo -e "

1. 显示帮助信息："
echo "--------------------------------------"
python main.py --help
echo -e "

2. 显示翻译命令帮助："
echo "--------------------------------------"
python main.py translate --help
echo -e "

3. 显示配置命令帮助："
echo "--------------------------------------"
python main.py config --help
echo -e "

4. 显示当前配置："
echo "--------------------------------------"
python main.py config show
echo -e "

5. 翻译命令示例："
echo "--------------------------------------"
echo "python main.py translate ls -s 1"
echo "(此处仅显示命令，不实际执行)"
echo -e "

6. 清理命令示例："
echo "--------------------------------------"
echo "python main.py clean -a"
echo "(此处仅显示命令，不实际执行)"
echo -e "

======================================"
echo "演示完成！"
echo "======================================"
