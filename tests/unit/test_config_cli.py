import os
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from manzh.config_cli import (
    interactive_add_service,
    interactive_update_service,
    interactive_delete_service,
    interactive_set_default,
    interactive_config
)
from manzh.config_manager import get_default_config_path

class TestConfigCLI(unittest.TestCase):
    """配置CLI模块的单元测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "services.json")
        
        # 准备测试配置
        self.test_config = {
            "services": {
                "test_openai": {
                    "type": "chatgpt",
                    "api_key": "test_key_1",
                    "url": "https://api.openai.com/v1/chat/completions",
                    "model": "gpt-3.5-turbo",
                    "max_context_length": 4096,
                    "max_output_length": 2048,
                    "language": "zh_CN"
                }
            },
            "default_service": "test_openai",
            "defaults": {
                "max_context_length": 4096,
                "max_output_length": 2048
            }
        }
        
        # 写入测试配置文件
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.test_config, f, indent=4)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时目录
        shutil.rmtree(self.test_dir)
    
    def test_get_default_config_path(self):
        """测试获取默认配置路径"""
        expected_path = os.path.join(os.path.expanduser("~"), ".config", "manzh", "services.json")
        self.assertEqual(get_default_config_path(), expected_path)
    
    @patch("builtins.input")
    def test_interactive_add_service_chatgpt(self, mock_input):
        """测试添加ChatGPT服务"""
        # 模拟用户输入
        mock_input.side_effect = [
            "test_service",  # 服务名称
            "1",            # 选择ChatGPT
            "test_key",     # API密钥
            "1",            # 选择OpenAI
            "2",            # 选择GPT-3.5-Turbo
            "1",            # 选择4K上下文长度
            "1",            # 选择2K输出长度
            "zh-CN"         # 语言设置
        ]
        
        # 执行测试
        result = interactive_add_service(self.config_path)
        self.assertTrue(result)
        
        # 验证配置文件
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.assertIn("test_service", config["services"])
        service_config = config["services"]["test_service"]
        self.assertEqual(service_config["type"], "chatgpt")
        self.assertEqual(service_config["api_key"], "test_key")
        self.assertEqual(service_config["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(service_config["model"], "gpt-3.5-turbo")
        self.assertEqual(service_config["max_context_length"], 4096)
        self.assertEqual(service_config["max_output_length"], 2048)
        self.assertEqual(service_config["language"], "zh-CN")
    
    def test_interactive_add_service_gemini(self):
        """测试添加Gemini服务"""
        with patch('builtins.input', side_effect=[
            "test_gemini",  # 服务名称
            "2",           # 选择Gemini服务
            "test_key",    # API密钥
            "gemini-pro",  # 模型名称
            "3",           # 选择32K上下文长度
            "3",           # 选择8K输出长度
            "zh-CN"        # 语言设置
        ]) as mock_input:
            result = interactive_add_service(self.config_path)
            self.assertTrue(result)
            
            # 验证配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.assertIn("test_gemini", config["services"])
            service_config = config["services"]["test_gemini"]
            self.assertEqual(service_config["type"], "gemini")
            self.assertEqual(service_config["api_key"], "test_key")
            self.assertEqual(service_config["model"], "gemini-pro")
            self.assertEqual(service_config["max_context_length"], 32768)
            self.assertEqual(service_config["max_output_length"], 8192)
            self.assertEqual(service_config["language"], "zh-CN")
    
    @patch("builtins.input")
    def test_interactive_update_service(self, mock_input):
        """测试更新服务配置"""
        # 模拟用户输入
        mock_input.side_effect = [
            "1",            # 选择第一个服务
            "1",            # 选择更新API密钥
            "new_key"       # 新的API密钥
        ]
        
        # 执行测试
        result = interactive_update_service(self.config_path)
        self.assertTrue(result)
        
        # 验证配置文件
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        self.assertEqual(
            config["services"]["test_openai"]["api_key"],
            "new_key"
        )
    
    @patch("builtins.input")
    def test_interactive_delete_service(self, mock_input):
        """测试删除服务"""
        # 模拟用户输入
        mock_input.side_effect = [
            "1",    # 选择第一个服务
            "y"     # 确认删除
        ]
        
        # 执行测试
        result = interactive_delete_service(self.config_path)
        self.assertTrue(result)
        
        # 验证配置文件
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        self.assertNotIn("test_openai", config["services"])
        self.assertIsNone(config["default_service"])
    
    @patch("builtins.input")
    def test_interactive_set_default(self, mock_input):
        """测试设置默认服务"""
        # 添加另一个服务用于测试
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        config["services"]["test_service2"] = {
            "type": "chatgpt",
            "api_key": "test_key_2",
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "max_context_length": 4096,
            "max_output_length": 2048,
            "language": "zh_CN"
        }
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        
        # 模拟用户输入
        mock_input.side_effect = ["2"]  # 选择第二个服务
        
        # 执行测试
        result = interactive_set_default(self.config_path)
        self.assertTrue(result)
        
        # 验证配置文件
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        self.assertEqual(config["default_service"], "test_service2")
    
    @patch("builtins.input")
    def test_interactive_config_menu(self, mock_input):
        """测试配置管理主菜单"""
        # 模拟用户输入
        mock_input.side_effect = ["5"]  # 选择退出
        
        # 执行测试
        interactive_config()
    
    def test_nonexistent_config_file(self):
        """测试不存在的配置文件"""
        nonexistent_path = os.path.join(self.test_dir, "nonexistent.json")
        
        # 测试各个功能
        result = interactive_update_service(nonexistent_path)
        self.assertFalse(result)
        
        result = interactive_delete_service(nonexistent_path)
        self.assertFalse(result)
        
        result = interactive_set_default(nonexistent_path)
        self.assertFalse(result)
    
    @patch("builtins.input")
    def test_invalid_input(self, mock_input):
        """测试无效输入处理"""
        # 模拟无效输入后有效输入
        mock_input.side_effect = [
            "invalid",  # 无效选择
            "5"        # 有效选择（退出）
        ]
        
        # 执行测试
        interactive_config()

if __name__ == "__main__":
    unittest.main() 