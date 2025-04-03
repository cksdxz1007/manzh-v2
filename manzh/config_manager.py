import os
import json
import sys
import subprocess
import threading
import time

def get_default_config_path() -> str:
    """
    获取默认配置文件路径
    
    Returns:
        str: 配置文件的完整路径
    """
    home = os.path.expanduser("~")
    return os.path.join(home, ".config", "manzh", "services.json")

class ConfigError(Exception):
    """配置相关错误的基类"""
    pass

class ConfigFileNotFoundError(ConfigError):
    """配置文件不存在错误"""
    pass

class ConfigValidationError(ConfigError):
    """配置验证错误"""
    pass

class ConfigPermissionError(ConfigError):
    """配置文件权限错误"""
    pass

def log_error(message, error=None, exit_code=None):
    """
    记录错误信息
    
    Args:
        message: 错误消息
        error: 原始错误对象
        exit_code: 如果不为None，则退出程序
    """
    error_msg = f"错误：{message}"
    if error:
        error_msg += f"\n详细信息：{str(error)}"
    print(error_msg, file=sys.stderr)
    if exit_code is not None:
        sys.exit(exit_code)

class ProgressDisplay:
    """进度条显示类"""
    
    def __init__(self, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
        """
        初始化进度条
        
        Args:
            total: 总任务数
            prefix: 前缀字符串
            suffix: 后缀字符串
            decimals: 显示小数位数
            length: 进度条长度
            fill: 进度条填充字符
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.iteration = 0
        self.start_time = time.time()
        sys.stdout.flush()
        
    def update(self, iteration=None):
        """
        更新进度条
        
        Args:
            iteration: 当前迭代次数
        """
        if iteration is not None:
            self.iteration = iteration
        else:
            self.iteration += 1
            
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        
        # 计算耗时和预计剩余时间
        elapsed_time = time.time() - self.start_time
        if self.iteration > 0:
            avg_time_per_iter = elapsed_time / self.iteration
            remaining_time = avg_time_per_iter * (self.total - self.iteration)
            time_info = f" [用时: {format_time(elapsed_time)}, 剩余: {format_time(remaining_time)}]"
        else:
            time_info = ""
            
        print(f'\r{self.prefix} |{bar}| {percent}% {self.suffix}{time_info}', end='')
        sys.stdout.flush()
        
    def finish(self):
        """完成进度条"""
        total_time = time.time() - self.start_time
        print(f"\r{self.prefix} |{self.fill * self.length}| 100% {self.suffix} [完成: {format_time(total_time)}]")
        sys.stdout.flush()

class ConfigLoadingProgress:
    """配置加载进度显示类"""
    def __init__(self):
        self.progress = ProgressDisplay(
            total=100,  # 设置总进度为100
            prefix="配置加载中",
            suffix="",
            length=30
        )
        
    def start(self):
        """开始加载"""
        self.progress.update(0)
        
    def update(self, percent):
        """更新加载进度"""
        self.progress.update(percent)
        
    def finish(self, success=True):
        """完成加载"""
        self.progress.finish()
        if success:
            print("配置加载完成", file=sys.stderr)
            sys.stderr.flush()
        else:
            print("配置加载失败", file=sys.stderr)
            sys.stderr.flush()

class ConfigCache:
    """配置文件缓存类"""
    _instance = None
    _config = None
    _config_path = None
    _last_load_time = 0
    _cache_duration = 300  # 缓存有效期（秒）
    _lock = threading.Lock()
    _loading_progress = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigCache, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_config(cls, config_path=None, service_name=None, force_reload=False):
        """
        获取配置，如果缓存有效则使用缓存，否则重新加载
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            service_name: 服务名称
            force_reload: 是否强制重新加载
            
        Returns:
            dict: 配置信息
            
        Raises:
            ConfigFileNotFoundError: 配置文件不存在
            ConfigValidationError: 配置验证失败
            ConfigPermissionError: 配置文件权限错误
            Exception: 其他错误
        """
        if config_path is None:
            config_path = get_default_config_path()
            
        current_time = time.time()
        
        with cls._lock:
            try:
                # 检查是否需要重新加载配置
                if (cls._config is None or 
                    force_reload or 
                    current_time - cls._last_load_time > cls._cache_duration or
                    cls._config_path != config_path):
                    
                    cls._loading_progress = ConfigLoadingProgress()
                    cls._loading_progress.start()
                    
                    cls._config_path = config_path
                    cls._loading_progress.update(10)  # 10% - 初始化完成
                    
                    if not os.path.exists(config_path):
                        # 确保配置目录存在
                        try:
                            if not ensure_config_dir_exists(config_path):
                                raise ConfigFileNotFoundError(f"配置目录创建失败：{os.path.dirname(config_path)}")
                        except PermissionError as e:
                            cls._loading_progress.finish(False)
                            raise ConfigPermissionError(f"创建配置目录失败：权限不足 - {str(e)}")
                        except Exception as e:
                            cls._loading_progress.finish(False)
                            raise ConfigError(f"创建配置目录失败：{str(e)}")
                        raise ConfigFileNotFoundError(f"配置文件不存在：{config_path}")
                    
                    cls._loading_progress.update(30)  # 30% - 目录检查完成
                    
                    try:
                        with open(config_path, "r", encoding='utf-8') as config_file:
                            cls._config = json.load(config_file)
                    except PermissionError as e:
                        cls._loading_progress.finish(False)
                        raise ConfigPermissionError(f"读取配置文件失败：权限不足 - {str(e)}")
                    except json.JSONDecodeError as e:
                        cls._loading_progress.finish(False)
                        raise ConfigValidationError(f"配置文件 JSON 格式错误：{str(e)}")
                    except Exception as e:
                        cls._loading_progress.finish(False)
                        raise ConfigError(f"读取配置文件失败：{str(e)}")
                    
                    cls._loading_progress.update(60)  # 60% - 文件读取完成
                    
                    if not isinstance(cls._config, dict):
                        cls._loading_progress.finish(False)
                        raise ConfigValidationError("配置文件格式错误：根对象必须是字典")
                    
                    if 'services' not in cls._config:
                        cls._loading_progress.finish(False)
                        raise ConfigValidationError("配置文件缺少 'services' 部分")
                    
                    cls._loading_progress.update(80)  # 80% - 基本验证完成
                    
                    cls._last_load_time = current_time
                    cls._loading_progress.finish(True)
                
                if not service_name:
                    service_name = cls._config.get('default_service')
                    if not service_name:
                        raise ConfigValidationError("未设置默认服务且未指定服务名称")
                
                service_config = cls._config.get('services', {}).get(service_name)
                if not service_config:
                    raise ConfigValidationError(f"服务 '{service_name}' 不存在")
                
                # 使用默认值或服务特定值
                defaults = cls._config.get('defaults', {})
                merged_config = defaults.copy()
                merged_config.update(service_config)
                
                # 验证合并后的配置
                is_valid, error_msg = validate_config(merged_config)
                if not is_valid:
                    raise ConfigValidationError(f"配置验证失败：{error_msg}")
                
                return merged_config
                
            except ConfigError as e:
                if cls._loading_progress:
                    cls._loading_progress.finish(False)
                log_error(str(e))
                raise
            except Exception as e:
                if cls._loading_progress:
                    cls._loading_progress.finish(False)
                log_error(f"配置加载失败：{str(e)}")
                raise ConfigError(f"配置加载失败：{str(e)}")

    @classmethod
    def invalidate_cache(cls):
        """清除缓存"""
        with cls._lock:
            cls._config = None
            cls._config_path = None
            cls._last_load_time = 0
            print("配置缓存已清除", file=sys.stderr)

def ensure_config_dir_exists(config_path: str) -> bool:
    """
    确保配置文件所在的目录存在，如果不存在则尝试创建
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 目录是否存在或成功创建
        
    Raises:
        Exception: 当创建目录失败时抛出异常
    """
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        print(f"配置目录不存在：{config_dir}", file=sys.stderr)
        try:
            os.makedirs(config_dir, exist_ok=True)
            print(f"已创建配置目录：{config_dir}", file=sys.stderr)
            return True
        except PermissionError:
            error_msg = "创建配置目录失败：权限不足"
            print(f"{error_msg}", file=sys.stderr)
            print("请确保您有足够的权限，或手动创建目录", file=sys.stderr)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"创建配置目录失败：{str(e)}"
            print(f"{error_msg}", file=sys.stderr)
            print("请确保您有足够的权限，或手动创建目录", file=sys.stderr)
            raise Exception(error_msg)
    return True

def validate_config(config):
    """
    验证配置文件的完整性和正确性
    
    Args:
        config: 配置字典
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    # 基本必需字段
    required_fields = {
        'api_key': str,
        'model': str,
        'type': str
    }
    
    # 根据服务类型确定额外的必需字段
    service_type = config.get('type', '').lower()
    
    if service_type == 'deepseek':
        # DeepSeek 服务需要 base_url 或 url
        if not (config.get('base_url') or config.get('url')):
            return False, "DeepSeek 服务需要 base_url 或 url 配置"
    elif service_type == 'gemini':
        # Gemini 服务不需要 URL 相关字段
        pass
    else:
        # 其他服务需要标准字段
        required_fields.update({
            'url': str,
            'language': str,
            'max_output_length': int,
            'max_context_length': int
        })
    
    # 验证必需字段
    for field, field_type in required_fields.items():
        if field not in config:
            return False, f"缺少必要配置项：{field}"
        if not isinstance(config[field], field_type):
            return False, f"配置项 {field} 类型错误，应为 {field_type.__name__}"
    
    # 验证 URL 格式（对于需要 URL 的服务）
    if service_type != 'gemini':
        url = config.get('url') or config.get('base_url')
        if url and not url.startswith(('http://', 'https://')):
            return False, "URL 格式无效"
    
    # 验证数值范围（对于标准服务）
    if service_type not in ['deepseek', 'gemini']:
        if config['max_output_length'] <= 0:
            return False, "max_output_length 必须大于 0"
        if config['max_context_length'] <= 0:
            return False, "max_context_length 必须大于 0"
        
    return True, ""

def load_config(config_path=None, service_name=None):
    """
    加载配置文件（使用缓存）
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
        service_name: 服务名称
        
    Returns:
        dict: 配置信息
    """
    if config_path is None:
        config_path = get_default_config_path()
    return ConfigCache.get_config(config_path, service_name)

def format_time(seconds):
    """
    格式化时间
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化后的时间字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
