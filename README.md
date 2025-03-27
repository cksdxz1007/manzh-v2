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

### v1.0.4
- 改进错误处理机制
  - 修复翻译失败时仍保存空文件的问题
  - 添加翻译内容有效性检查
  - 完善翻译失败时的错误提示
- 添加完整的命令行接口
  - 支持所有功能的命令行操作
  - 添加参数解析和帮助信息
  - 优化错误处理和返回值
- 代码结构优化
  - 重构翻译服务抽象层
  - 改进配置文件缓存机制
  - 优化多线程翻译队列
- 翻译服务增强
  - 完善翻译服务错误重试机制
  - 优化翻译缓存策略
  - 改进翻译进度显示

### v1.0.3
- 添加 Google Gemini API 支持
  - 支持 gemini-2.0-flash-exp 模型
  - 优化翻译服务配置结构
  - 添加服务类型验证
- 改进清理功能
  - 添加交互式清理菜单
  - 支持按章节列出已翻译命令
  - 支持删除指定命令的手册
  - 支持清空所有翻译
  - 优化错误日志管理
- 代码优化
  - 添加翻译服务抽象基类
  - 改进配置文件验证
  - 增强错误处理机制
  - 优化进度显示

### v1.0.2
- 修复翻译后的手册无法在列表中显示的问题
- 修复 man 手册和 --help 输出的保存问题
- 改进 --help 翻译的保存格式
- 添加翻译文件保存路径的提示
- 优化命令检查和错误提示逻辑

### v1.0.1
- 添加对 --help 输出的翻译支持
- 优化无 man 手册命令的处理
- 改进翻译提示信息
- 添加上下文长度和输出长度配置
- 优化配置文件兼容性处理

### v1.0.0
- 初始版本发布
- 支持多种翻译服务
- 添加交互式界面
- 支持多线程翻译

## 平台支持

### macOS
- 使用 `man -M` 选项查看翻译后的手册
- 需要安装 groff 以支持手册格式化：`brew install groff`
- 使用 Homebrew 安装依赖

### Linux
- 直接支持 `man -M` 和 `MANPATH` 设置
- 通过包管理器安装依赖
- 支持主流发行版（Ubuntu、Debian、CentOS、RHEL 等）

## 安装依赖

安装脚本会自动安装所需依赖，但如果您选择手动安装，可以参考以下命令：

### macOS
```bash
# 安装基础依赖
brew install jq python3 groff

# 安装 Python 依赖
pip3 install requests

# 可选：安装最新版 man
brew install man-db
```

### Linux
```bash
# Ubuntu/Debian
sudo apt install jq python3 python3-requests man-db groff

# CentOS/RHEL
sudo yum install jq python3 python3-requests man-db groff
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

例如：
```bash
man -M /usr/local/share/man/zh_CN ls
```
