# ManZH v2 - Man手册中文翻译工具

> 这是ManZH的重构版本，提供更高效的命令手册翻译体验

一个用于将 Linux/Unix man 手册翻译成中文的自动化工具，支持多种翻译服务。

## 功能特点

- 自动获取和翻译命令的 man 手册
- 支持翻译命令的 --help 输出（当没有 man 手册时）
- 支持多个翻译服务（OpenAI、DeepSeek、Ollama 等）
- 支持自定义上下文长度和输出长度
- 智能适配不同翻译服务的参数
- 支持多章节手册的批量翻译
- 保留原始格式和代码块
- 交互式配置界面
- 多线程并行翻译
- 支持断点续传
- 显示翻译进度
- 错误日志记录

## 系统要求

- Linux/Unix 操作系统或 macOS
- Python 3.6+
- 依赖包：
  - requests
  - typing-extensions
  - 对于 Gemini 支持：google-generativeai

## 安装

### 从源码安装

1. 克隆或下载仓库：
```bash
git clone https://github.com/cksdxz1007/ManZH.git
cd ManZH
```

2. 使用 pip 安装：
```bash
# 开发模式安装
pip install -e .

# 或构建并安装
python -m build
pip install dist/manzh-*-py3-none-any.whl
```

完成安装后，你可以通过以下命令验证安装：
```bash
# 查看命令是否可用
which manzh

# 查看版本
manzh --version

# 查看帮助
manzh --help
```

## 使用方法

### 首次使用配置

安装完成后，首次使用前需要初始化配置：

```bash
# 初始化配置（交互式）
manzh config init
```

或直接进入配置菜单：

```bash
manzh config
```

按照提示添加翻译服务（如 OpenAI、DeepSeek、Ollama 等）。

### 交互式界面

直接运行主程序：
```bash
manzh
```

将显示交互式菜单，包含以下选项：
1. 翻译命令手册
2. 查看已翻译手册
3. 配置管理
4. 清除已翻译手册
5. 显示当前配置
0. 退出

### 命令行模式

ManZH 支持功能完整的命令行模式，可以直接执行特定功能：

#### 翻译命令手册

```bash
# 翻译指定命令手册
manzh translate ls

# 指定章节号
manzh translate ls -s 1

# 强制重新翻译
manzh translate ls -f

# 指定使用的翻译服务
manzh translate ls --service deepseek
```

#### 查看已翻译的手册

```bash
# 列出所有已翻译的手册
manzh list

# 只列出指定章节的手册
manzh list -s 1
```

#### 清除已翻译的手册

```bash
# 清除特定命令的手册
manzh clean ls

# 清除特定命令的特定章节
manzh clean ls -s 1

# 清除特定章节的所有手册
manzh clean 1

# 清除所有已翻译的手册
manzh clean -a

# 交互式清除
manzh clean
```

#### 配置管理

```bash
# 交互式配置管理
manzh config

# 初始化配置
manzh config init

# 添加新的翻译服务
manzh config add

# 更新服务配置
manzh config update

# 删除服务
manzh config delete

# 设置默认服务
manzh config default

# 显示当前配置
manzh config show
```

#### 其他选项

```bash
# 显示帮助信息
manzh --help

# 显示版本信息
manzh --version

# 调试模式
manzh --debug
```

## 配置翻译服务

支持多种翻译服务，可以通过配置管理工具进行管理：

```bash
manzh config
```

支持的服务：

### 1. OpenAI 兼容接口类型
- OpenAI (GPT-4, GPT-3.5-turbo)
- DeepSeek
- Ollama (本地模型)
- 任何兼容 OpenAI API 格式的服务

### 2. Google Gemini 类型
- Google Gemini (gemini-2.0-flash-exp 等模型)

## 翻译结果

翻译后的手册将保存在：
```
/usr/local/share/man/zh_CN/man<章节号>/
```

查看翻译后的手册：
```bash
man -M /usr/local/share/man/zh_CN <命令>
```

例如：
```bash
man -M /usr/local/share/man/zh_CN ls
```

注：对于没有 man 手册的命令（如 conda），ManZH 会自动尝试翻译 --help 输出：
```bash
# 翻译 conda 命令的帮助信息
manzh translate conda

# 查看翻译结果
man -M /usr/local/share/man/zh_CN conda
```

## 目录结构

```
.
├── main.py            # 主程序入口
├── bin/manzh          # 命令行脚本
├── manzh/             # 核心模块
│   ├── translate.py   # 翻译服务实现
│   ├── config_cli.py  # 配置管理UI
│   ├── config_manager.py # 配置管理器
│   ├── clean.py       # 清理功能
│   ├── list_manuals.py # 列出手册
│   └── man_utils.py   # 手册处理工具
├── docs/              # 文档目录
│   └── manzh.1        # man手册页
└── README.md          # 说明文档
```

## 注意事项

1. 需要 root 权限来安装翻译后的手册
2. 首次使用前请先配置翻译服务
3. 翻译质量取决于所选用的翻译服务
4. 建议在网络稳定的环境下使用
5. 注意 API 使用配额限制

## 高级使用技巧

### 批量翻译常用命令

创建一个脚本批量翻译常用命令：

```bash
#!/bin/bash
COMMANDS=(
  "ls" "cd" "grep" "find" "awk" "sed"
  "tar" "cp" "mv" "rm" "mkdir" "chmod"
)

for cmd in "${COMMANDS[@]}"; do
  echo "正在翻译: $cmd"
  manzh translate "$cmd"
  echo "-------------------"
done
```

### 集成到系统 man 命令

在 `~/.bashrc` 或 `~/.zshrc` 中添加以下函数：

```bash
# 优先使用中文手册，如果没有则使用英文手册
function man() {
  LANG=zh_CN command man -M /usr/local/share/man/zh_CN "$@" 2>/dev/null || command man "$@"
}
```

## 许可证

MIT

## 作者

cynning

## 更新日志

### v2.0.0
- 完全重构的代码结构
  - 基于Python包结构，支持pip安装
  - 抽象化翻译服务接口，便于扩展
  - 改进命令行界面和参数处理
- 添加新的翻译服务支持
  - DeepSeek专属接口支持
  - Google Gemini API集成
  - 本地模型(Ollama)集成
- 交互式配置管理
  - 多种翻译服务统一配置界面
  - 配置初始化向导
  - 命令行和菜单式配置管理
- 翻译功能增强
  - 智能处理不同手册格式
  - 支持--help输出的翻译
  - 改进翻译缓存机制和重试策略
  - 增加翻译进度显示
- 错误处理和调试
  - 完善的错误提示和恢复机制
  - 调试模式支持
  - 敏感信息保护和安全配置

## 平台支持

### macOS
- 使用 `man -M` 选项查看翻译后的手册
- 需要安装 groff 以支持手册格式化：`brew install groff`

### Linux
- 直接支持 `man -M` 和 `MANPATH` 设置
- 支持主流发行版（Ubuntu、Debian、CentOS、RHEL 等）

## 安装依赖

如果您选择手动安装依赖，可以参考以下命令：

### macOS
```bash
# 安装基础依赖
brew install python3 groff

# 安装 Python 依赖
pip3 install requests typing-extensions

# 可选：安装 Gemini 支持
pip3 install google-generativeai
```

### Linux
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip man-db groff

# 安装 Python 依赖
pip3 install requests typing-extensions
```

查看翻译后的手册：

方法一：使用 MANPATH（推荐）
```bash
# 设置过 MANPATH 后可以直接使用
man ls
```

方法二：使用 -M 参数
```bash
man -M /usr/local/share/man/zh_CN <命令>
```

# ManZH 修复工具

## 问题描述

ManZH工具在执行过程中存在输出缓冲问题，导致在某些环境中运行时看不到实时输出信息，特别是在通过Python模块方式调用时。这个问题主要表现为：

1. 调用Python模块时输出被缓冲，只有在程序结束时才能看到全部输出
2. 在调试模式下，只能看到"调试模式已启用"的信息，无法看到后续的翻译进度
3. 通过包装脚本调用时，subprocess的输出捕获可能导致实时输出丢失

## 解决方案

我们提供了一个修复版本的包装脚本 `manzh_fixer.py`，它解决了上述问题：

1. 对每个输出语句后添加 `sys.stdout.flush()` 确保实时显示输出
2. 修改了命令行参数解析逻辑，使其更加健壮
3. 提供了交互式菜单，更容易使用
4. 保留了原始命令行工具的全部功能
5. 添加了更详细的错误处理和进度显示

## 使用方法

### 直接运行修复版工具

```bash
# 最简单的方式
python3 manzh_fixer.py

# 或者使用命令行参数（与原始工具兼容）
python3 manzh_fixer.py translate ls
python3 manzh_fixer.py --debug translate ls
```

### 作为模块导入

```python
# 如果您需要在自己的Python脚本中使用修复后的功能
import os
import sys
from manzh_fixer import translate_command_fixed
from argparse import Namespace

# 设置参数
args = Namespace(
    command="ls",
    section=None,
    service=None,
    debug=True
)

# 调用修复后的翻译函数
translate_command_fixed(args)
```

## 环境检查

如果您仍然遇到问题，可以使用我们提供的环境检查脚本来诊断问题：

```bash
python3 manzh_env_check.py
```

该脚本会检查您的Python环境、ManZH配置、包结构和系统依赖，帮助定位可能的问题。

## 后续改进

未来的改进方向：

1. 将修复合并到主要的ManZH包中
2. 添加更多的日志功能来更好地诊断问题
3. 改进翻译服务的错误处理和重试机制
4. 提供更多的本地化选项和配置项

## 贡献

欢迎提交问题报告和改进建议！

## 命令参考

### 翻译命令手册

```bash
manzh translate <command> [-s section] [--service service_name] [-d/--debug]
```

### 配置翻译服务

```bash
manzh config [init|show]
```

### 列出已翻译手册

```bash
manzh list
```

### 清理已翻译手册

```bash
manzh clean
```

### 优化已翻译手册

```bash
manzh optimize [-f file] [-c command] [-s section] [-d directory] [-r] [--debug]
```

优化已翻译的手册页，移除无意义的符号和行，同时保持文档结构完整。

参数:
- `-f, --file`: 指定要优化的手册文件路径
- `-c, --command`: 指定要优化的命令名称
- `-s, --section`: 指定手册章节号
- `-d, --dir`: 指定手册目录路径
- `-r, --recursive`: 递归处理子目录
- `--debug`: 启用详细调试输出

示例:
```bash
# 优化特定命令的手册
manzh optimize -c conda -s 1

# 优化指定目录下的所有手册
manzh optimize -d /usr/local/share/man/zh_CN -r

# 优化单个手册文件
manzh optimize -f /usr/local/share/man/zh_CN/man1/conda.1
```
