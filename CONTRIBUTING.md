# 贡献指南

感谢您对 ManZH 项目感兴趣！我们欢迎任何形式的贡献，包括但不限于：

- 代码贡献
- 文档改进
- 问题报告
- 功能建议
- 翻译优化

## 开发环境设置

1. 确保您的系统满足以下要求：
   - Python 3.6+
   - Git
   - pip
   - virtualenv（推荐）

2. Fork 并克隆仓库：
   ```bash
   git clone https://github.com/YOUR_USERNAME/ManZH.git
   cd ManZH
   ```

3. 设置开发环境：
   ```bash
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   source venv/bin/activate  # Linux/macOS
   # 或
   .\venv\Scripts\activate   # Windows
   
   # 安装开发依赖
   pip install -e ".[dev]"
   ```

## 代码规范

### Python 代码风格
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 4 空格缩进
- 最大行长度 120 字符
- 使用类型注解（Python 3.6+）
- 使用 f-strings 进行字符串格式化（Python 3.6+）

### 文档规范
- 所有新功能必须包含文档字符串
- 使用 Google 风格的文档字符串格式
- 重要的函数和类必须包含使用示例
- 更新 README.md 和相关文档

### 提交信息规范
使用清晰的提交信息，格式如下：
```
类型(范围): 简短描述

详细描述（如果需要）

相关问题: #123
```

类型包括：
- feat: 新功能
- fix: 错误修复
- docs: 文档更改
- style: 代码风格更改
- refactor: 代码重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

## 开发流程

1. 创建新分支：
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-fix-name
   ```

2. 进行更改并测试：
   ```bash
   # 运行单元测试
   pytest tests/
   
   # 运行代码风格检查
   flake8 manzh/
   
   # 运行类型检查
   mypy manzh/
   ```

3. 提交更改：
   ```bash
   git add .
   git commit -m "feat(translate): 添加新的翻译服务支持"
   ```

4. 推送到您的 Fork：
   ```bash
   git push origin feature/your-feature-name
   ```

5. 创建 Pull Request

## Pull Request 指南

1. 确保 PR 标题清晰描述了更改内容
2. 在描述中详细说明更改的原因和影响
3. 包含相关的测试用例
4. 确保所有测试通过
5. 如果添加了新功能，请更新文档
6. 如果修复了 bug，请添加回归测试

## 问题报告指南

报告问题时，请包含以下信息：

1. 操作系统和版本
2. Python 版本
3. ManZH 版本
4. 错误信息和堆栈跟踪
5. 重现步骤
6. 预期行为和实际行为

## 发布流程

1. 更新版本号（遵循语义化版本）
2. 更新 CHANGELOG.md
3. 更新文档
4. 创建发布标签
5. 发布到 PyPI

## 行为准则

- 尊重所有贡献者
- 保持专业和友好的交流
- 接受建设性的批评
- 关注问题本身而不是个人

## 许可证

通过提交 PR，您同意您的贡献将在 MIT 许可证下发布。

## 联系方式

如有任何问题，请通过以下方式联系我们：

- 提交 Issue
- 发送邮件至维护者
- 在讨论区发帖

感谢您的贡献！ 