import os
import sys
import json
import subprocess
from .config_manager import ensure_config_dir_exists, validate_config, ConfigCache, get_default_config_path
from typing import Dict, Any, Optional

def load_config(config_path: str) -> dict:
    """加载配置文件"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败：{str(e)}", file=sys.stderr)
    return None

def save_config(config_path: str, config: dict) -> bool:
    """保存配置文件"""
    try:
        # 确保配置目录存在
        if not ensure_config_dir_exists(config_path):
            return False
            
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置文件失败：{str(e)}", file=sys.stderr)
        return False

def get_length_choice(prompt: str, output: bool = False) -> int:
    """获取长度选择"""
    while True:
        choice = input(prompt).strip()
        try:
            idx = int(choice)
            if output:
                if idx == 1:
                    return 2048
                elif idx == 2:
                    return 4096
                elif idx == 3:
                    return 8192
                elif idx == 4:
                    custom = int(input("请输入自定义长度: ").strip())
                    if custom > 0:
                        return custom
            else:
                if idx == 1:
                    return 4096
                elif idx == 2:
                    return 8192
                elif idx == 3:
                    return 32768
                elif idx == 4:
                    return 65536
                elif idx == 5:
                    custom = int(input("请输入自定义长度: ").strip())
                    if custom > 0:
                        return custom
        except ValueError:
            pass
        print("请输入有效的选项")

def test_translation_service(service_config: dict) -> bool:
    """测试翻译服务是否可用"""
    try:
        from .translate import create_translation_service
        service = create_translation_service(service_config)
        test_text = "Hello World"
        
        # 如果配置中有system_prompt就使用，否则使用默认值
        system_prompt = service_config.get("system_prompt", "请将以下文本从英文翻译成中文")
        
        result = service.translate(test_text, system_prompt)
        return bool(result and isinstance(result, str))
    except Exception as e:
        print(f"\n测试翻译失败：{str(e)}", file=sys.stderr)
        return False

def add_chatgpt_service(config_path: str = None, service_name: str = None) -> bool:
    """添加ChatGPT服务"""
    if config_path is None:
        config_path = get_default_config_path()
        
    if service_name is None:
        service_name = input("请输入服务名称: ").strip()
    
    # 获取API密钥
    api_key = input("请输入 API 密钥: ").strip()
    
    # 选择服务提供商
    print("\n选择服务提供商：")
    print("1) OpenAI")
    print("2) DeepSeek")
    print("3) Ollama")
    print("4) 自定义")
    
    while True:
        provider = input("请选择 [1-4]: ").strip()
        if provider == "1":
            url = "https://api.openai.com/v1/chat/completions"
            break
        elif provider == "2":
            url = "https://api.deepseek.com/v1/chat/completions"
            break
        elif provider == "3":
            url = "http://localhost:11434/api/chat"
            break
        elif provider == "4":
            url = input("请输入API端点URL: ").strip()
            if url.startswith(("http://", "https://")):
                break
        print("请选择有效的选项")
    
    # 选择模型
    print("\n选择模型：")
    print("1) GPT-4")
    print("2) GPT-3.5-Turbo")
    print("3) DeepSeek-Chat")
    print("4) 自定义")
    
    while True:
        model_choice = input("请选择 [1-4]: ").strip()
        if model_choice == "1":
            model = "gpt-4"
            break
        elif model_choice == "2":
            model = "gpt-3.5-turbo"
            break
        elif model_choice == "3":
            model = "deepseek-chat"
            break
        elif model_choice == "4":
            model = input("请输入模型名称: ").strip()
            if model:
                break
        print("请选择有效的选项")
    
    # 选择上下文长度
    print("\n设置上下文长度（字符数）：")
    print("1) 4K  (4096)")
    print("2) 8K  (8192)")
    print("3) 32K (32768)")
    print("4) 64K (65536)")
    print("5) 自定义")
    
    max_context_length = get_length_choice("请选择 [1-5]: ")
    
    # 选择输出长度
    print("\n设置最大输出长度（字符数）：")
    print("1) 2K  (2048)")
    print("2) 4K  (4096)")
    print("3) 8K  (8192)")
    print("4) 自定义")
    
    max_output_length = get_length_choice("请选择 [1-4]: ", output=True)
    
    # 获取语言设置
    language = input("请输入目标语言（默认：zh-CN）: ").strip() or "zh-CN"
    
    # 创建服务配置
    service_config = {
        "type": "chatgpt",
        "api_key": api_key,
        "url": url,
        "model": model,
        "language": language,
        "max_context_length": max_context_length,
        "max_output_length": max_output_length,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
    
    # 保存配置
    config = load_config(config_path) or {"services": {}, "defaults": {}}
    config["services"][service_name] = service_config
    if not config.get("default_service"):
        config["default_service"] = service_name
    
    if save_config(config_path, config):
        print(f"\n服务 '{service_name}' 配置已保存")
        return True
    return False

def interactive_add_service(config_path: str = None) -> bool:
    """交互式添加新的翻译服务"""
    if config_path is None:
        config_path = get_default_config_path()
        
    print("\n=== 添加新的翻译服务 ===\n")
    
    # 获取服务名称
    service_name = input("请输入服务名称: ").strip()
    
    # 选择服务类型
    print("\n选择服务类型：")
    print("1) ChatGPT 兼容接口（OpenAI等）")
    print("2) Google Gemini")
    print("3) DeepSeek")
    print("4) SiliconFlow")
    print("5) OpenRouter")
    print("6) Ollama（本地部署）")
    
    while True:
        type_choice = input("请选择 [1-6]: ").strip()
        if type_choice == "1":
            return add_chatgpt_service(config_path, service_name)
        elif type_choice == "2":
            return add_gemini_service(config_path, service_name)
        elif type_choice == "3":
            return add_deepseek_standalone_service(config_path, service_name)
        elif type_choice == "4":
            return add_siliconflow_standalone_service(config_path, service_name)
        elif type_choice == "5":
            return add_openrouter_standalone_service(config_path, service_name)
        elif type_choice == "6":
            return add_ollama_standalone_service(config_path, service_name)
        else:
            print("请选择有效的选项")

def add_gemini_service(config_path: str = None, service_name: str = None) -> bool:
    """添加Gemini服务"""
    if config_path is None:
        config_path = get_default_config_path()
        
    if service_name is None:
        service_name = input("请输入服务名称: ").strip()
    
    # 获取API密钥
    print("\n=== Gemini 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 Gemini API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    # 获取模型名称
    model = input("请输入模型名称（默认：gemini-pro）: ").strip() or "gemini-pro"
    
    # 选择上下文长度
    print("\n设置上下文长度（字符数）：")
    print("1) 4K  (4096)")
    print("2) 8K  (8192)")
    print("3) 32K (32768)")
    print("4) 64K (65536)")
    print("5) 自定义")
    
    max_context_length = get_length_choice("请选择 [1-5]: ")
    
    # 选择输出长度
    print("\n设置最大输出长度（字符数）：")
    print("1) 2K  (2048)")
    print("2) 4K  (4096)")
    print("3) 8K  (8192)")
    print("4) 自定义")
    
    max_output_length = get_length_choice("请选择 [1-4]: ", output=True)
    
    # 获取语言设置
    language = input("请输入目标语言（默认：zh-CN）: ").strip() or "zh-CN"
    
    # 创建服务配置
    service_config = {
        "type": "gemini",
        "service": "gemini",
        "api_key": api_key,
        "model": model,
        "language": language,
        "max_context_length": max_context_length,
        "max_output_length": max_output_length,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
    
    # 保存配置
    config = load_config(config_path) or {"services": {}, "defaults": {}}
    config["services"][service_name] = service_config
    if save_config(config_path, config):
        print(f"\n服务 '{service_name}' 配置已保存")
        return True
    return False

def interactive_update_service(config_path=None):
    """交互式更新服务配置"""
    try:
        if config_path is None:
            config_path = get_default_config_path()
            
        # 加载配置文件
        config = load_config(config_path)
        if not config:
            print("\n配置文件不存在或为空")
            return
            
        # 确保服务配置存在
        if "services" not in config or not config["services"]:
            print("\n当前没有配置任何服务")
            return
            
        # 显示可用服务
        print("\n可用的服务：")
        services = list(config["services"].keys())
        for i, name in enumerate(services, 1):
            print(f"{i}) {name}")
        print("0) 返回上级菜单")
            
        # 选择要更新的服务
        while True:
            choice = input("\n请选择要更新的服务 [0-{}]: ".format(len(services))).strip()
            
            if choice == "0":
                return
            
            try:
                idx = int(choice)
                if 1 <= idx <= len(services):
                    service_name = services[idx-1]
                    break
                else:
                    print("请输入有效的选项")
            except ValueError:
                print("请输入有效的选项")
        
        # 显示当前配置
        service_config = config["services"][service_name]
        print(f"\n当前配置 - {service_name}:")
        print(json.dumps(service_config, indent=2, ensure_ascii=False))
        
        # 根据服务类型确定可更新的字段
        service_type = service_config.get("type", "").lower()
        
        # 根据不同的服务类型显示可更新的字段
        if service_type == "chatgpt":
            print("\n可更新的字段：")
            fields = [
                "api_key", "url", "base_url", "model", "temperature", "max_tokens", 
                "max_context_length", "max_output_length", "top_p", "frequency_penalty", 
                "presence_penalty", "timeout", "response_format", "language"
            ]
        elif service_type == "gemini":
            print("\n可更新的字段：")
            fields = [
                "api_key", "model", "temperature", "max_tokens", 
                "max_context_length", "max_output_length", "top_p", 
                "top_k", "language"
            ]
        elif service_type == "deepseek":
            print("\n可更新的字段：")
            fields = [
                "api_key", "base_url", "model", "temperature", "max_tokens", 
                "top_p", "frequency_penalty", "presence_penalty", "timeout", 
                "response_format", "system_prompt"
            ]
        elif service_type == "ollama":
            print("\n可更新的字段：")
            fields = [
                "url", "model", "temperature", "max_tokens", 
                "top_p", "top_k", "stream", "system_prompt"
            ]
        elif service_type == "siliconflow":
            print("\n可更新的字段：")
            fields = [
                "api_key", "base_url", "url", "model", "temperature", "max_tokens",
                "top_p", "top_k", "frequency_penalty", "stream", "response_format",
                "system_prompt"
            ]
        elif service_type == "openrouter":
            print("\n可更新的字段：")
            fields = [
                "api_key", "base_url", "url", "model", "temperature", 
                "max_output_length", "top_p", "headers", "system_prompt"
            ]
        else:
            # 通用字段
            fields = list(service_config.keys())
            
        # 如果配置中有字段但不在预定义列表中，添加它们
        for key in service_config.keys():
            if key not in fields and key != "type":
                fields.append(key)
                
        # 显示可更新的字段
        for i, field in enumerate(fields, 1):
            current_value = service_config.get(field, "未设置")
            if isinstance(current_value, dict):
                current_value = json.dumps(current_value)
            print(f"{i}) {field} [当前值: {current_value}]")
        print("0) 返回上级菜单")
        
        # 选择要更新的字段
        while True:
            try:
                choice = input("\n请选择要更新的字段 [0-{}] (输入q返回主菜单): ".format(len(fields))).strip()
                
                if choice.lower() == "q":
                    print("\n返回主菜单...")
                    return False
                
                if choice == "0":
                    return interactive_update_service(config_path)
                
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(fields):
                        field = fields[idx-1]
                        break
                    else:
                        print("请输入有效的选项")
                except ValueError:
                    print("请输入有效的选项")
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return False
                
        # 根据字段类型获取新值
        if field in ["max_context_length", "max_output_length"]:
            if field == "max_context_length":
                print("\n设置上下文长度（字符数）：")
                print("1) 4K  (4096)")
                print("2) 8K  (8192)")
                print("3) 32K (32768)")
                print("4) 64K (65536)")
                print("5) 自定义")
                new_value = get_length_choice("请选择 [1-5]: ")
            else:
                print("\n设置最大输出长度（字符数）：")
                new_value = get_length_choice("请选择 [1-4]: ", output=True)
        elif field == "max_tokens":
            try:
                print("\n设置最大输出长度（tokens）：")
                new_value = int(input("请输入新值 (建议值: 2048, 4096 或 8192): ").strip())
            except ValueError:
                print("输入无效，保持原值")
                new_value = service_config.get(field, 4096)
        elif field == "temperature":
            try:
                print("\n设置温度（0.0-1.0，值越小结果越确定性）：")
                new_value = float(input("请输入新值 (建议值: 0.0-1.0): ").strip())
                if new_value < 0 or new_value > 1:
                    print("值超出范围，保持0-1之间")
                    new_value = max(0, min(1, new_value))
            except ValueError:
                print("输入无效，保持原值")
                new_value = service_config.get(field, 0.7)
        elif field in ["top_p", "top_k"]:
            try:
                if field == "top_p":
                    print("\n设置top_p值（0.0-1.0，控制采样概率）：")
                    new_value = float(input("请输入新值 (建议值: 0.0-1.0): ").strip())
                    if new_value < 0 or new_value > 1:
                        print("值超出范围，保持0-1之间")
                        new_value = max(0, min(1, new_value))
                else:
                    print("\n设置top_k值（控制候选词数量）：")
                    new_value = int(input("请输入新值 (建议值: 1-100): ").strip())
            except ValueError:
                print("输入无效，保持原值")
                new_value = service_config.get(field, 0.7 if field == "top_p" else 40)
        elif field in ["frequency_penalty", "presence_penalty"]:
            try:
                print(f"\n设置{field}值（通常-2.0到2.0，负值鼓励重复，正值抑制重复）：")
                new_value = float(input("请输入新值 (建议值: -2.0到2.0): ").strip())
                if new_value < -2 or new_value > 2:
                    print("值超出推荐范围，请确认这是您想要的设置")
            except ValueError:
                print("输入无效，保持原值")
                new_value = service_config.get(field, 0.0)
        elif field == "timeout":
            try:
                print("\n设置请求超时时间（秒）：")
                new_value = int(input("请输入新值 (建议值: 30-120): ").strip())
                if new_value < 5:
                    print("超时时间过短，已设为最小值5秒")
                    new_value = 5
            except ValueError:
                print("输入无效，保持原值")
                new_value = service_config.get(field, 60)
        elif field == "response_format":
            print("\n设置响应格式：")
            print("1) 文本格式")
            print("2) JSON格式")
            try:
                format_choice = input("请选择 [1-2]: ").strip()
                if format_choice == "1":
                    new_value = {"type": "text"}
                elif format_choice == "2":
                    new_value = {"type": "json"}
                else:
                    print("输入无效，保持原值")
                    new_value = service_config.get(field, {"type": "text"})
            except Exception:
                print("处理输入时出错，保持原值")
                new_value = service_config.get(field, {"type": "text"})
        elif field == "stream":
            try:
                current = service_config.get(field, False)
                print(f"\n当前值: {current}")
                new_value = input("是否启用流式输出？(y/n): ").strip().lower() == 'y'
            except Exception:
                print("处理输入时出错，保持原值")
                new_value = service_config.get(field, False)
        elif field in ["url", "base_url"]:
            print(f"\n设置{field}：")
            current = service_config.get(field, "")
            if current:
                print(f"当前值: {current}")
            new_url = input("请输入新的URL (留空保持原值): ").strip()
            if new_url:
                if not new_url.startswith(("http://", "https://")):
                    print("URL必须以http://或https://开头")
                    if input("添加https://前缀？(y/n): ").strip().lower() == 'y':
                        new_url = "https://" + new_url
                    else:
                        print("URL格式无效，保持原值")
                        new_url = ""
                new_value = new_url or current
            else:
                new_value = current
        else:
            # 通用字段更新
            current = service_config.get(field, "")
            print(f"\n当前值: {current}")
            new_value = input(f"请输入新的{field}值 (留空保持原值): ").strip()
            if not new_value:
                new_value = current
        
        # 更新配置
        if field in service_config and isinstance(service_config[field], (int, float)) and isinstance(new_value, str):
            try:
                if isinstance(service_config[field], int):
                    new_value = int(new_value)
                else:
                    new_value = float(new_value)
            except ValueError:
                print("无法转换为相同类型，使用原始类型")
        
        # 更新服务配置
        service_config[field] = new_value
        config["services"][service_name] = service_config
        
        # 保存配置
        if save_config(config_path, config):
            print(f"\n服务 '{service_name}' 的 '{field}' 已更新为：{new_value}")
            
            # 询问是否继续更新其他字段
            if input("\n是否继续更新该服务的其他字段？(y/N): ").strip().lower() == 'y':
                # 递归调用自身，但传入服务名以继续编辑当前服务
                return interactive_update_service(config_path)
            
            return True
        else:
            print("\n配置保存失败")
            return False
    except KeyboardInterrupt:
        print("\n\n操作已取消，返回上级菜单")
        return False
    except Exception as e:
        print(f"\n更新服务配置时出错：{str(e)}", file=sys.stderr)
        if input("\n是否重试？(y/N): ").strip().lower() == 'y':
            return interactive_update_service(config_path)
        return False

def interactive_delete_service(config_path=None):
    """交互式删除服务配置"""
    try:
        if config_path is None:
            config_path = get_default_config_path()
            
        # 加载配置文件
        config = load_config(config_path)
        if not config:
            print("\n配置文件不存在或为空")
            return
            
        # 确保服务配置存在
        if "services" not in config or not config["services"]:
            print("\n当前没有配置任何服务")
            return
            
        # 显示可用服务
        print("\n可用的服务：")
        services = list(config["services"].keys())
        for i, name in enumerate(services, 1):
            print(f"{i}) {name}")
        print("0) 返回上级菜单")
            
        # 选择要删除的服务
        while True:
            try:
                choice = input("\n请选择要删除的服务 [0-{}] (输入q返回主菜单): ".format(len(services))).strip()
                
                if choice.lower() == "q":
                    print("\n返回主菜单...")
                    return False
                
                if choice == "0":
                    return
                
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(services):
                        service_name = services[idx-1]
                        break
                    else:
                        print("请输入有效的选项")
                except ValueError:
                    print("请输入有效的选项")
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return False
        
        # 确认删除
        confirm = input(f"\n确定要删除服务 '{service_name}'？(y/N): ").strip().lower()
        if confirm != 'y':
            print("\n取消删除")
            return False
            
        # 删除服务配置
        del config["services"][service_name]
        
        # 如果删除的是默认服务，重新设置默认服务
        if config.get("default_service") == service_name:
            if config["services"]:
                config["default_service"] = list(config["services"].keys())[0]
            else:
                if "default_service" in config:
                    del config["default_service"]
        
        # 保存配置
        if save_config(config_path, config):
            print(f"\n服务 '{service_name}' 已删除")
            return True
        else:
            print("\n配置保存失败")
            return False
    except KeyboardInterrupt:
        print("\n\n操作已取消，返回上级菜单")
        return False
    except Exception as e:
        print(f"\n删除服务配置时出错：{str(e)}", file=sys.stderr)
        if input("\n是否重试？(y/N): ").strip().lower() == 'y':
            return interactive_delete_service(config_path)
        return False

def interactive_set_default(config_path=None):
    """交互式设置默认服务"""
    try:
        if config_path is None:
            config_path = get_default_config_path()
            
        # 加载配置文件
        config = load_config(config_path)
        if not config:
            print("\n配置文件不存在或为空")
            return
            
        # 确保服务配置存在
        if "services" not in config or not config["services"]:
            print("\n当前没有配置任何服务")
            return
            
        # 显示当前默认服务
        current_default = config.get("default_service")
        if current_default:
            print(f"\n当前默认服务: {current_default}")
        else:
            print("\n当前未设置默认服务")
            
        # 显示可用服务
        print("\n可用的服务：")
        services = list(config["services"].keys())
        for i, name in enumerate(services, 1):
            print(f"{i}) {name}")
        print("0) 返回上级菜单")
            
        # 选择新的默认服务
        while True:
            try:
                choice = input("\n请选择新的默认服务 [0-{}] (输入q返回主菜单): ".format(len(services))).strip()
                
                if choice.lower() == "q":
                    print("\n返回主菜单...")
                    return False
                
                if choice == "0":
                    return
                
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(services):
                        service_name = services[idx-1]
                        break
                    else:
                        print("请输入有效的选项")
                except ValueError:
                    print("请输入有效的选项")
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return False
        
        # 更新默认服务
        if service_name == current_default:
            print(f"\n'{service_name}' 已经是默认服务")
            return True
            
        config["default_service"] = service_name
        
        # 保存配置
        if save_config(config_path, config):
            print(f"\n默认服务已设置为 '{service_name}'")
            return True
        else:
            print("\n配置保存失败")
            return False
    except KeyboardInterrupt:
        print("\n\n操作已取消，返回上级菜单")
        return False
    except Exception as e:
        print(f"\n设置默认服务时出错：{str(e)}", file=sys.stderr)
        if input("\n是否重试？(y/N): ").strip().lower() == 'y':
            return interactive_set_default(config_path)
        return False

def interactive_config(config_path=None):
    """交互式配置管理"""
    try:
        if config_path is None:
            config_path = get_default_config_path()
            
        while True:
            try:
                print("\n=== 配置管理 ===")
                print("1) 添加新的服务")
                print("2) 更新服务配置")
                print("3) 删除服务")
                print("4) 设置默认服务")
                print("5) 显示当前配置")
                print("0) 返回主菜单")
                
                choice = input("\n请选择操作 [0-5]: ").strip()
                
                if choice == "0":
                    return
                elif choice == "1":
                    interactive_add_service(config_path)
                elif choice == "2":
                    interactive_update_service(config_path)
                elif choice == "3":
                    interactive_delete_service(config_path)
                elif choice == "4":
                    interactive_set_default(config_path)
                elif choice == "5":
                    show_config(config_path)
                else:
                    print("\n无效的选择，请重试")
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                if input("\n返回主菜单？(Y/n): ").strip().lower() != 'n':
                    return
    except KeyboardInterrupt:
        print("\n\n返回主菜单")
        return
    except Exception as e:
        print(f"\n配置管理时出错：{str(e)}", file=sys.stderr)
        if input("\n是否重试？(y/N): ").strip().lower() == 'y':
            return interactive_config(config_path)
        return

def add_openrouter_service(services: Dict[str, Any]) -> bool:
    """添加 OpenRouter 服务配置"""
    print("\n=== OpenRouter 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 OpenRouter API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    app_name = input("应用名称 (可选，用于OpenRouter排名): ").strip()
    site_url = input("网站URL (可选，用于OpenRouter排名): ").strip()
    
    print("\n选择模型：")
    print("1) OpenAI - GPT-4o")
    print("2) OpenAI - GPT-3.5-turbo")
    print("3) Anthropic - Claude 3 Opus")
    print("4) 自定义")
    
    model = ""
    while True:
        model_choice = input("请选择 [1-4]: ").strip()
        if model_choice == "1":
            model = "openai/gpt-4o"
            break
        elif model_choice == "2":
            model = "openai/gpt-3.5-turbo"
            break
        elif model_choice == "3":
            model = "anthropic/claude-3-opus-20240229"
            break
        elif model_choice == "4":
            model = input("请输入模型标识 (例如 openai/gpt-4): ").strip()
            if model:
                break
        else:
            print("请选择有效的选项")
    
    headers = {
        "HTTP-Referer": site_url if site_url else None,
        "X-Title": app_name if app_name else None
    }
    # 移除空值
    headers = {k: v for k, v in headers.items() if v}
    
    service_config = {
        "type": "openrouter",
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "url": "https://openrouter.ai/api/v1/chat/completions",  # 保留完整URL作为后备
        "model": model,
        "language": "zh-CN",
        "max_context_length": 32768,
        "max_output_length": 4096,
        "temperature": 0.7,
        "top_p": 0.7,
        "headers": headers,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
        
    services["openrouter"] = service_config
    return True

def interactive_init_config() -> None:
    """交互式初始化配置文件"""
    print("\n=== ManZH 配置初始化 ===")
    sys.stdout.flush()
    print("这将帮助您创建一个新的配置文件。")
    sys.stdout.flush()
    
    config: Dict[str, Any] = {
        "services": {},
        "translation": {
            "chunk_size": 4000,
            "max_workers": 2,
            "rate_limit_delay": 2.0,
            "max_retries": 3,
            "timeout": 60
        },
        "cache": {
            "enabled": True,
            "dir": os.path.expanduser("~/.cache/manzh/translations")
        },
        "output": {
            "temp_dir": os.path.expanduser("~/.cache/manzh/temp"),
            "man_dir": "/usr/local/share/man/zh_CN"
        }
    }
    
    # 选择默认服务
    print("\n可用的翻译服务：")
    sys.stdout.flush()
    print("1. DeepSeek (推荐，支持缓存和长文本)")
    sys.stdout.flush()
    print("2. Gemini")
    sys.stdout.flush()
    print("3. Ollama (本地部署)")
    sys.stdout.flush()
    print("4. Silicon Flow")
    sys.stdout.flush()
    print("5. OpenRouter (支持多种商业模型)")
    sys.stdout.flush()
    print("6. OpenAI 兼容接口")
    sys.stdout.flush()
    print("0. 退出配置")
    sys.stdout.flush()
    
    service_map = {
        '1': ('deepseek', add_deepseek_service),
        '2': ('gemini', add_gemini_service),
        '3': ('ollama', add_ollama_service),
        '4': ('siliconflow', add_siliconflow_service),
        '5': ('openrouter', add_openrouter_service),
        '6': ('openai_compatible', add_openai_compatible_service)
    }
    
    while True:
        choice = input("\n请选择默认翻译服务 (0-6): ").strip()
        sys.stdout.flush()
        if choice == '0':
            print("\n配置已取消")
            sys.stdout.flush()
            sys.exit(0)
        if choice not in service_map:
            print("无效的选择，请重试。")
            sys.stdout.flush()
            continue
            
        service_name, add_func = service_map[choice]
        if add_func(config["services"]):
            config["default_service"] = service_name
            break
        else:
            print("\n服务添加失败，请重试或选择其他服务。")
            sys.stdout.flush()
    
    # 配置翻译参数
    print("\n=== 翻译参数配置 ===")
    sys.stdout.flush()
    print("（按回车使用默认值，输入 'q' 或 'quit' 退出配置）")
    sys.stdout.flush()
    
    chunk_size = input("每个翻译块的大小 (默认: 4000): ").strip()
    sys.stdout.flush()
    if chunk_size.lower() in ['q', 'quit']:
        print("\n配置已取消")
        sys.stdout.flush()
        sys.exit(0)
    if chunk_size.isdigit():
        config["translation"]["chunk_size"] = int(chunk_size)
    
    max_workers = input("并行翻译线程数 (默认: 2): ").strip()
    sys.stdout.flush()
    if max_workers.lower() in ['q', 'quit']:
        print("\n配置已取消")
        sys.stdout.flush()
        sys.exit(0)
    if max_workers.isdigit():
        config["translation"]["max_workers"] = int(max_workers)
    
    delay = input("请求间隔时间(秒) (默认: 2.0): ").strip()
    sys.stdout.flush()
    if delay.lower() in ['q', 'quit']:
        print("\n配置已取消")
        sys.stdout.flush()
        sys.exit(0)
    if delay and delay.replace('.', '').isdigit():
        config["translation"]["rate_limit_delay"] = float(delay)
    
    # 配置缓存
    print("\n=== 缓存配置 ===")
    sys.stdout.flush()
    cache_enabled = input("是否启用翻译缓存？(Y/n): ").strip().lower()
    sys.stdout.flush()
    if cache_enabled in ['q', 'quit']:
        print("\n配置已取消")
        sys.stdout.flush()
        sys.exit(0)
    config["cache"]["enabled"] = cache_enabled != 'n'
    
    if config["cache"]["enabled"]:
        cache_dir = input(f"缓存目录 (默认: {config['cache']['dir']}): ").strip()
        sys.stdout.flush()
        if cache_dir.lower() in ['q', 'quit']:
            print("\n配置已取消")
            sys.stdout.flush()
            sys.exit(0)
        if cache_dir:
            config["cache"]["dir"] = os.path.expanduser(cache_dir)
    
    # 配置输出
    print("\n=== 输出配置 ===")
    sys.stdout.flush()
    temp_dir = input(f"临时文件目录 (默认: {config['output']['temp_dir']}): ").strip()
    sys.stdout.flush()
    if temp_dir.lower() in ['q', 'quit']:
        print("\n配置已取消")
        sys.stdout.flush()
        sys.exit(0)
    if temp_dir:
        config["output"]["temp_dir"] = os.path.expanduser(temp_dir)
    
    man_dir = input(f"man手册目录 (默认: {config['output']['man_dir']}): ").strip()
    sys.stdout.flush()
    if man_dir.lower() in ['q', 'quit']:
        print("\n配置已取消")
        sys.stdout.flush()
        sys.exit(0)
    if man_dir:
        config["output"]["man_dir"] = os.path.expanduser(man_dir)
    
    # 保存配置
    config_path = get_default_config_path()
    ensure_config_dir_exists(config_path)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n配置文件已保存到: {config_path}")
        sys.stdout.flush()
    except Exception as e:
        print(f"\n保存配置文件失败: {str(e)}")
        sys.stdout.flush()
        return

def add_deepseek_service(services: Dict[str, Any]) -> bool:
    """添加 DeepSeek 服务配置"""
    print("\n=== DeepSeek 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 DeepSeek API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    service_config = {
        "type": "deepseek",  # 使用deepseek类型，而不是chatgpt类型
        "api_key": api_key,
        "base_url": "https://api.deepseek.com",  # 根据文档使用标准base_url
        "model": "deepseek-chat",
        "temperature": 0.3,
        "max_tokens": 8192,
        "language": "zh-CN",
        "max_context_length": 65536,
        "max_output_length": 8192,
        "top_p": 0.7,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 60,
        "response_format": {
            "type": "text"
        },
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
        
    services["deepseek"] = service_config
    return True

def add_gemini_service(services: Dict[str, Any]) -> bool:
    """添加 Gemini 服务配置"""
    print("\n=== Gemini 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 Gemini API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    service_config = {
        "type": "gemini",
        "api_key": api_key,
        "model": "gemini-pro",
        "max_output_length": 2048,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
        
    services["gemini"] = service_config
    return True

def add_ollama_service(services: Dict[str, Any]) -> bool:
    """添加 Ollama 服务配置"""
    print("\n=== Ollama 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    url = input("Ollama API URL (默认: http://localhost:11434/v1/chat/completions): ").strip()
    if url.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    if not url:
        url = "http://localhost:11434/v1/chat/completions"
    
    model = input("模型名称 (默认: qwen2.5:7b): ").strip()
    if model.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    if not model:
        model = "qwen2.5:7b"
    
    service_config = {
        "type": "chatgpt",
        "service": "ollama",
        "api_key": "123",
        "url": url,
        "model": model,
        "language": "zh-CN",
        "max_context_length": 4096,
        "max_output_length": 2048,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
        
    services["ollama"] = service_config
    return True

def add_siliconflow_service(services: Dict[str, Any]) -> bool:
    """添加 Silicon Flow 服务配置"""
    print("\n=== Silicon Flow 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 Silicon Flow API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    service_config = {
        "type": "siliconflow",
        "api_key": api_key,
        "base_url": "https://api.siliconflow.cn",
        "url": "https://api.siliconflow.cn/v1/chat/completions",  # 保留完整URL作为后备
        "model": "deepseek-ai/DeepSeek-V3",
        "language": "zh-CN",
        "max_context_length": 65536,
        "max_output_length": 4096,
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "stream": False,
        "response_format": {
            "type": "text"
        },
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
        
    services["siliconflow"] = service_config
    return True

def add_openai_compatible_service(services: Dict[str, Any]) -> bool:
    """添加 OpenAI 兼容接口服务配置"""
    print("\n=== OpenAI 兼容接口配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    service_name = input("服务名称 (默认: openai_compatible): ").strip() or "openai_compatible"
    if service_name.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    url = input("API 地址 (例如 https://api.openai.com/v1/chat/completions): ").strip()
    if url.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    if not url:
        print("错误: API 地址不能为空")
        return False
    
    api_key = input("API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    if not api_key:
        print("错误: API Key 不能为空")
        return False
    
    model = input("模型名称 (例如 gpt-3.5-turbo): ").strip()
    if model.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    if not model:
        print("错误: 模型名称不能为空")
        return False
    
    service_config = {
        "type": "chatgpt",
        "service": "openai_compatible",
        "api_key": api_key,
        "url": url,
        "model": model,
        "language": "zh-CN",
        "max_context_length": 4096,
        "max_output_length": 2048,
        "temperature": 0.7,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
    
    services[service_name] = service_config
    return True

def add_deepseek_standalone_service(config_path: str = None, service_name: str = None) -> bool:
    """添加DeepSeek服务"""
    if config_path is None:
        config_path = get_default_config_path()
        
    if service_name is None:
        service_name = input("请输入服务名称: ").strip()
    
    # 获取API密钥
    print("\n=== DeepSeek 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 DeepSeek API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    # 创建服务配置
    service_config = {
        "type": "deepseek",  # 使用deepseek类型，而不是chatgpt类型
        "api_key": api_key,
        "base_url": "https://api.deepseek.com",  # 根据文档使用标准base_url
        "model": "deepseek-chat",
        "temperature": 0.3,
        "max_tokens": 8192,
        "language": "zh-CN",
        "max_context_length": 65536,
        "max_output_length": 8192,
        "top_p": 0.7,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 60,
        "response_format": {
            "type": "text"
        },
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
    
    # 保存配置
    config = load_config(config_path) or {"services": {}, "defaults": {}}
    config["services"][service_name] = service_config
    if not config.get("default_service"):
        config["default_service"] = service_name
    
    if save_config(config_path, config):
        print(f"\n服务 '{service_name}' 配置已保存")
        return True
    return False

def add_siliconflow_standalone_service(config_path: str = None, service_name: str = None) -> bool:
    """添加Silicon Flow服务"""
    if config_path is None:
        config_path = get_default_config_path()
        
    if service_name is None:
        service_name = input("请输入服务名称: ").strip()
    
    # 获取API密钥
    print("\n=== Silicon Flow 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 Silicon Flow API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    # 创建服务配置
    service_config = {
        "type": "siliconflow",
        "api_key": api_key,
        "base_url": "https://api.siliconflow.cn",
        "url": "https://api.siliconflow.cn/v1/chat/completions",  # 保留完整URL作为后备
        "model": "deepseek-ai/DeepSeek-V3",
        "language": "zh-CN",
        "max_context_length": 65536,
        "max_output_length": 4096,
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "stream": False,
        "response_format": {
            "type": "text"
        },
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
    
    # 保存配置
    config = load_config(config_path) or {"services": {}, "defaults": {}}
    config["services"][service_name] = service_config
    if not config.get("default_service"):
        config["default_service"] = service_name
    
    if save_config(config_path, config):
        print(f"\n服务 '{service_name}' 配置已保存")
        return True
    return False

def add_openrouter_standalone_service(config_path: str = None, service_name: str = None) -> bool:
    """添加OpenRouter服务"""
    if config_path is None:
        config_path = get_default_config_path()
        
    if service_name is None:
        service_name = input("请输入服务名称: ").strip()
    
    # 获取API密钥
    print("\n=== OpenRouter 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    api_key = input("请输入 OpenRouter API Key: ").strip()
    if api_key.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    
    app_name = input("应用名称 (可选，用于OpenRouter排名): ").strip()
    site_url = input("网站URL (可选，用于OpenRouter排名): ").strip()
    
    print("\n选择模型：")
    print("1) OpenAI - GPT-4o")
    print("2) OpenAI - GPT-3.5-turbo")
    print("3) Anthropic - Claude 3 Opus")
    print("4) 自定义")
    
    model = ""
    while True:
        model_choice = input("请选择 [1-4]: ").strip()
        if model_choice == "1":
            model = "openai/gpt-4o"
            break
        elif model_choice == "2":
            model = "openai/gpt-3.5-turbo"
            break
        elif model_choice == "3":
            model = "anthropic/claude-3-opus-20240229"
            break
        elif model_choice == "4":
            model = input("请输入模型标识 (例如 openai/gpt-4): ").strip()
            if model:
                break
        else:
            print("请选择有效的选项")
    
    headers = {
        "HTTP-Referer": site_url if site_url else None,
        "X-Title": app_name if app_name else None
    }
    # 移除空值
    headers = {k: v for k, v in headers.items() if v}
    
    service_config = {
        "type": "openrouter",
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "url": "https://openrouter.ai/api/v1/chat/completions",  # 保留完整URL作为后备
        "model": model,
        "language": "zh-CN",
        "max_context_length": 32768,
        "max_output_length": 4096,
        "temperature": 0.7,
        "top_p": 0.7,
        "headers": headers,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
        
    # 保存配置
    config = load_config(config_path) or {"services": {}, "defaults": {}}
    config["services"][service_name] = service_config
    if not config.get("default_service"):
        config["default_service"] = service_name
    
    if save_config(config_path, config):
        print(f"\n服务 '{service_name}' 配置已保存")
        return True
    return False

def add_ollama_standalone_service(config_path: str = None, service_name: str = None) -> bool:
    """添加Ollama服务"""
    if config_path is None:
        config_path = get_default_config_path()
        
    if service_name is None:
        service_name = input("请输入服务名称: ").strip()
    
    # 获取API设置
    print("\n=== Ollama 服务配置 ===")
    print("提示：任何输入中输入 'q' 或 'quit' 可退出配置")
    
    url = input("Ollama API URL (默认: http://localhost:11434/v1/chat/completions): ").strip()
    if url.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    if not url:
        url = "http://localhost:11434/v1/chat/completions"
    
    model = input("模型名称 (默认: qwen2.5:7b): ").strip()
    if model.lower() in ['q', 'quit']:
        print("\n配置已取消")
        return False
    if not model:
        model = "qwen2.5:7b"
    
    service_config = {
        "type": "chatgpt",  # Ollama使用chatgpt类型
        "service": "ollama",
        "api_key": "no-key-needed",
        "url": url,
        "model": model,
        "language": "zh-CN",
        "max_context_length": 4096,
        "max_output_length": 2048,
        "system_prompt": "你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。要求：1. 保持原始格式，包括空行和缩进；2. 保留所有命令、选项和示例不翻译；3. 翻译要准确、专业，符合技术文档风格；4. 对于专业术语，在首次出现时可以保留英文原文；5. 保持段落结构不变；6. 保持简洁，不要添加额外的解释；7. 确保输出是中文。"
    }
    
    # 测试翻译服务
    print("\n正在测试翻译服务...")
    if not test_translation_service(service_config):
        print("添加服务失败：翻译测试未通过")
        return False
        
    # 保存配置
    config = load_config(config_path) or {"services": {}, "defaults": {}}
    config["services"][service_name] = service_config
    if not config.get("default_service"):
        config["default_service"] = service_name
    
    if save_config(config_path, config):
        print(f"\n服务 '{service_name}' 配置已保存")
        return True
    return False

def show_config(config_path=None):
    """显示当前配置"""
    try:
        if config_path is None:
            config_path = get_default_config_path()
            
        # 加载配置文件
        config = load_config(config_path)
        if not config:
            print("\n配置文件不存在或为空")
            return False
            
        # 显示配置信息
        print("\n=== 当前配置 ===")
        
        # 显示默认服务
        default_service = config.get("default_service")
        if default_service:
            print(f"默认服务: {default_service}")
        else:
            print("默认服务: 未设置")
            
        # 显示服务列表
        services = config.get("services", {})
        if services:
            print("\n已配置的服务:")
            for name in services:
                service = services[name]
                service_type = service.get("type", "未知")
                model = service.get("model", "未知")
                if name == default_service:
                    print(f"  * {name} (类型: {service_type}, 模型: {model}) [默认]")
                else:
                    print(f"  - {name} (类型: {service_type}, 模型: {model})")
        else:
            print("\n未配置任何服务")
            
        # 显示翻译参数
        translation = config.get("translation", {})
        if translation:
            print("\n翻译参数:")
            for key, value in translation.items():
                print(f"  {key}: {value}")
                
        # 显示缓存配置
        cache = config.get("cache", {})
        if cache:
            print("\n缓存配置:")
            for key, value in cache.items():
                print(f"  {key}: {value}")
                
        # 显示输出配置
        output = config.get("output", {})
        if output:
            print("\n输出配置:")
            for key, value in output.items():
                print(f"  {key}: {value}")
        
        # 输出配置文件路径
        print(f"\n配置文件路径: {config_path}")
        
        return True
    except Exception as e:
        print(f"\n显示配置时出错: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    interactive_config() 