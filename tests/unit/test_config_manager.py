import os
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from manzh.config_manager import ConfigCache, validate_config, ensure_config_dir_exists, get_default_config_path
import subprocess

class TestConfigManager(unittest.TestCase):
    """配置管理模块的单元测试"""
    
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
            
        # 重置ConfigCache
        ConfigCache._instance = None
        ConfigCache._config = None
        ConfigCache._last_load_time = 0
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时目录
        shutil.rmtree(self.test_dir)
        
        # 重置ConfigCache
        ConfigCache._instance = None
        ConfigCache._config = None
        ConfigCache._last_load_time = 0
    
    def test_validate_config_valid_chatgpt(self):
        """测试有效的ChatGPT配置验证"""
        config = {
            "type": "chatgpt",
            "api_key": "test_key",
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "max_context_length": 4096,
            "max_output_length": 2048,
            "language": "zh_CN"
        }
        is_valid, error_msg = validate_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
    
    def test_validate_config_valid_gemini(self):
        """测试有效的Gemini配置验证"""
        config = {
            "type": "gemini",
            "api_key": "test_key",
            "model": "gemini-pro",
            "max_context_length": 8192,
            "max_output_length": 4096,
            "language": "zh_CN"
        }
        is_valid, error_msg = validate_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
    
    def test_validate_config_invalid_missing_field(self):
        """测试缺少必要字段的配置验证"""
        config = {
            "type": "chatgpt",
            "api_key": "test_key"
            # 缺少其他必要字段
        }
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("缺少必要配置项", error_msg)
    
    def test_validate_config_invalid_type(self):
        """测试字段类型错误的配置验证"""
        config = {
            "type": "chatgpt",
            "api_key": "test_key",
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "max_context_length": "4096",  # 应该是整数
            "max_output_length": 2048,
            "language": "zh_CN"
        }
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("类型错误", error_msg)
    
    def test_validate_config_invalid_url(self):
        """测试URL格式无效的配置验证"""
        config = {
            "type": "chatgpt",
            "api_key": "test_key",
            "url": "invalid_url",
            "model": "gpt-3.5-turbo",
            "max_context_length": 4096,
            "max_output_length": 2048,
            "language": "zh_CN"
        }
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "URL 格式无效")
    
    def test_validate_config_invalid_length(self):
        """测试长度值无效的配置验证"""
        config = {
            "type": "chatgpt",
            "api_key": "test_key",
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "max_context_length": 0,  # 无效值
            "max_output_length": 2048,
            "language": "zh_CN"
        }
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "max_context_length 必须大于 0")
    
    @patch("os.makedirs")
    def test_ensure_config_dir_exists_success(self, mock_makedirs):
        """测试成功创建配置目录"""
        mock_makedirs.return_value = None  # os.makedirs 成功时返回 None
        result = ensure_config_dir_exists("/nonexistent/path/config.json")
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("/nonexistent/path", exist_ok=True)
    
    def test_ensure_config_dir_exists_failure(self):
        """测试创建配置目录失败"""
        test_path = "/nonexistent/path/config.json"
        
        # 模拟os.makedirs失败
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Permission denied")
            
            with self.assertRaises(Exception) as context:
                ensure_config_dir_exists(test_path)
            
            self.assertIn("创建配置目录失败", str(context.exception))
    
    def test_config_cache_singleton(self):
        """测试ConfigCache的单例模式"""
        cache1 = ConfigCache()
        cache2 = ConfigCache()
        self.assertIs(cache1, cache2)
    
    def test_config_cache_get_config(self):
        """测试获取配置（包括缓存机制）"""
        # 第一次获取配置
        config1 = ConfigCache.get_config(self.config_path)
        self.assertIsInstance(config1, dict)
        self.assertEqual(config1['model'], 'gpt-3.5-turbo')
        
        # 第二次获取配置（应该使用缓存）
        config2 = ConfigCache.get_config(self.config_path)
        self.assertEqual(config1['model'], config2['model'])
        
        # 使用不同的路径应该重新加载
        new_config_path = os.path.join(self.test_dir, "config2.json")
        with open(new_config_path, "w", encoding="utf-8") as f:
            json.dump({
                "services": {
                    "test_openai": {
                        "type": "chatgpt",
                        "api_key": "test_key_2",
                        "url": "https://api.openai.com/v1/chat/completions",
                        "model": "gpt-4",
                        "max_context_length": 8192,
                        "max_output_length": 4096,
                        "language": "zh_CN"
                    }
                },
                "default_service": "test_openai",
                "defaults": {
                    "max_context_length": 4096,
                    "max_output_length": 2048
                }
            }, f, indent=4)
        
        config3 = ConfigCache.get_config(new_config_path)
        self.assertEqual(config3['model'], 'gpt-4')
        self.assertNotEqual(config1['model'], config3['model'])
    
    def test_config_cache_invalid_json(self):
        """测试加载无效JSON配置文件"""
        # 写入无效的JSON
        with open(self.config_path, "w") as f:
            f.write("invalid json")
            
        with self.assertRaises(SystemExit):
            ConfigCache.get_config(self.config_path)
    
    def test_config_cache_nonexistent_service(self):
        """测试请求不存在的服务"""
        with self.assertRaises(ValueError):
            ConfigCache.get_config(self.config_path, "nonexistent_service")
    
    def test_config_cache_invalidate(self):
        """测试清除缓存"""
        # 首先加载配置
        config1 = ConfigCache.get_config(self.config_path)
        self.assertIsNotNone(config1)
        
        # 清除缓存
        ConfigCache.invalidate_cache()
        
        # 验证缓存已清除
        self.assertIsNone(ConfigCache._config)
        self.assertEqual(ConfigCache._last_load_time, 0)

    def test_get_default_config_path(self):
        """测试获取默认配置路径"""
        expected_path = os.path.join(os.path.expanduser("~"), ".config", "manzh", "services.json")
        self.assertEqual(get_default_config_path(), expected_path)

if __name__ == "__main__":
    unittest.main() 