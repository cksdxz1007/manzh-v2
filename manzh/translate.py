import sys
import json
import time
import requests
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import Timeout, RequestException
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import subprocess
import google.generativeai as genai
from abc import ABC, abstractmethod
from .config_manager import ProgressDisplay
import shutil
from typing import List

class TranslationService(ABC):
    """翻译服务的抽象基类"""
    
    @abstractmethod
    def translate(self, content, system_prompt):
        """
        翻译内容的抽象方法
        
        Args:
            content: 要翻译的内容
            system_prompt: 系统提示
            
        Returns:
            str: 翻译后的内容
        """
        pass

class ChatGPTService(TranslationService):
    """ChatGPT翻译服务实现"""
    
    def __init__(self, config):
        self.config = config
        self.session = create_retry_session()
        
    def translate(self, content, system_prompt):
        """
        使用ChatGPT API翻译内容
        
        Args:
            content: 要翻译的内容
            system_prompt: 系统提示
            
        Returns:
            str: 翻译后的内容
        """
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": self.config["max_output_length"]
        }
        
        try:
            response = self.session.post(
                self.config["url"],
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("API返回结果格式错误")
                
        except Exception as e:
            print(f"翻译请求失败：{str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise

class GeminiService(TranslationService):
    """Google Gemini翻译服务实现"""
    
    def __init__(self, config):
        self.config = config
        genai.configure(api_key=config["api_key"])
        self.model = genai.GenerativeModel(config["model"])
        
    def translate(self, content, system_prompt):
        """
        使用Gemini API翻译内容
        
        Args:
            content: 要翻译的内容
            system_prompt: 系统提示
            
        Returns:
            str: 翻译后的内容
        """
        try:
            prompt = f"{system_prompt}\n\n{content}"
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                raise ValueError("API返回结果为空")
                
        except Exception as e:
            print(f"Gemini翻译请求失败：{str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise

class DeepSeekAPIError(Exception):
    """DeepSeek API 错误"""
    def __init__(self, message, status_code=None, error_code=None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code

class DeepSeekService(TranslationService):
    """DeepSeek 翻译服务实现"""
    
    def __init__(self, config):
        self.config = config
        # 验证必要的配置项
        if not config.get("api_key"):
            raise ValueError("配置验证失败：缺少必要配置项：api_key")
        if not config.get("model"):
            raise ValueError("配置验证失败：缺少必要配置项：model")
        if not (config.get("url") or config.get("base_url")):
            raise ValueError("配置验证失败：缺少必要配置项：url 或 base_url")
            
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        
    def _get_api_url(self):
        """获取 API URL"""
        base = self.config.get("url") or self.config.get("base_url")
        return f"{base}/chat/completions"
        
    def _handle_api_error(self, response):
        """处理 API 错误响应"""
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "未知错误")
            error_code = error_data.get("error", {}).get("code")
            
            if response.status_code == 401:
                raise DeepSeekAPIError("API 密钥无效或已过期", response.status_code, error_code)
            elif response.status_code == 429:
                raise DeepSeekAPIError("请求过于频繁，请降低请求速率", response.status_code, error_code)
            elif response.status_code == 400:
                raise DeepSeekAPIError(f"请求参数错误: {error_message}", response.status_code, error_code)
            elif response.status_code >= 500:
                raise DeepSeekAPIError("DeepSeek 服务器错误，请稍后重试", response.status_code, error_code)
            else:
                raise DeepSeekAPIError(f"API 调用失败: {error_message}", response.status_code, error_code)
        except ValueError:
            raise DeepSeekAPIError(f"API 响应格式错误: {response.text}", response.status_code)
        
    def translate(self, content, system_prompt):
        """
        使用 DeepSeek API 翻译内容
        
        Args:
            content: 要翻译的内容
            system_prompt: 系统提示
            
        Returns:
            str: 翻译后的内容
            
        Raises:
            DeepSeekAPIError: API 调用错误
            requests.exceptions.RequestException: 网络请求错误
            ValueError: 响应格式错误
        """
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config.get("temperature", 0.3),
            "max_tokens": self.config.get("max_tokens", 8192),
            "response_format": self.config.get("response_format", {"type": "text"}),
            "stream": False,
            "top_p": self.config.get("top_p", 0.7),
            "frequency_penalty": self.config.get("frequency_penalty", 0.0),
            "presence_penalty": self.config.get("presence_penalty", 0.0)
        }
        
        try:
            response = self.session.post(
                self._get_api_url(),
                headers=headers,
                json=data,
                timeout=self.config.get("timeout", 60)
            )
            
            if response.status_code != 200:
                self._handle_api_error(response)
                
            result = response.json()
            
            # 输出缓存命中情况
            if "usage" in result:
                usage = result["usage"]
                if "prompt_cache_hit_tokens" in usage:
                    print(f"\n缓存命中: {usage['prompt_cache_hit_tokens']} tokens (0.1元/百万tokens)")
                    sys.stdout.flush()
                if "prompt_cache_miss_tokens" in usage:
                    print(f"缓存未命中: {usage['prompt_cache_miss_tokens']} tokens (1元/百万tokens)")
                    sys.stdout.flush()
                print(f"完成 tokens: {usage.get('completion_tokens', 0)}")
                sys.stdout.flush()
                print(f"总计 tokens: {usage.get('total_tokens', 0)}")
                sys.stdout.flush()
            
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                finish_reason = choice.get("finish_reason")
                
                if finish_reason == "length":
                    print("\n警告：输出被截断，因为达到了最大长度限制")
                    sys.stdout.flush()
                elif finish_reason == "content_filter":
                    print("\n警告：输出被内容过滤策略截断")
                    sys.stdout.flush()
                elif finish_reason == "insufficient_system_resource":
                    print("\n警告：由于系统资源不足，输出被中断")
                    sys.stdout.flush()
                
                return choice["message"]["content"].strip()
            else:
                raise ValueError("API返回结果格式错误：缺少 choices 字段")
                
        except requests.exceptions.Timeout:
            print(f"\n错误：请求超时（{self.config.get('timeout', 60)}秒）", file=sys.stderr)
            sys.stderr.flush()
            raise
        except requests.exceptions.ConnectionError:
            print("\n错误：网络连接失败", file=sys.stderr)
            sys.stderr.flush()
            raise
        except requests.exceptions.RequestException as e:
            print(f"\n错误：请求失败 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise
        except ValueError as e:
            print(f"\n错误：响应解析失败 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise
        except Exception as e:
            print(f"\n错误：未知错误 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise

def create_translation_service(config):
    """
    创建翻译服务实例
    
    Args:
        config: 服务配置
        
    Returns:
        TranslationService: 翻译服务实例
    """
    service_type = config.get("type", "").lower()
    
    if service_type == "deepseek":
        return DeepSeekService(config)
    elif service_type == "chatgpt":
        return ChatGPTService(config)
    elif service_type == "gemini":
        return GeminiService(config)
    elif service_type == "siliconflow":
        return SiliconFlowService(config)
    elif service_type == "openrouter":
        return OpenRouterService(config)
    else:
        raise ValueError(f"不支持的翻译服务类型：{service_type}")

class TranslationQueue:
    """翻译队列管理类"""
    
    def __init__(self, chunk_size=2000, max_workers=3, max_retries=3):
        """
        初始化翻译队列
        
        Args:
            chunk_size: 每个块的大小
            max_workers: 最大并行工作线程数
            max_retries: 最大重试次数
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.queue = Queue()
        self.results = {}
        self.failed_chunks = set()
        self.lock = threading.Lock()
        self.total_chunks = 0
        self.completed_chunks = 0
        self.rate_limit_delay = 1.0  # 请求间隔时间（秒）
        self.is_cancelled = False
        self.executor = None
        self.progress = None
        self.start_time = time.time()
        self.translated_chunks = 0
        
    def prepare_content(self, text: str) -> List[str]:
        """
        将文本分割成多个块以便翻译
        
        Args:
            text: 要翻译的文本
            
        Returns:
            List[str]: 分割后的文本块列表
        """
        # 检查配置和参数
        raw_lines = text.splitlines()
        max_chars = self.chunk_size
        chunks = []
        current_chunk = []
        current_size = 0
        
        # 逐行添加内容，当超过最大块大小时创建新块
        for line in raw_lines:
            # 如果是空行，直接添加到当前块
            if not line.strip():
                current_chunk.append(line)
                current_size += len(line) + 1  # +1 是换行符
                continue
                
            # 如果当前行加上当前块的大小超过最大值，创建新块
            if current_size + len(line) + 1 > max_chars and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
                
            current_chunk.append(line)
            current_size += len(line) + 1  # +1 是换行符
        
        # 添加最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        # 更新进度条
        self.total_chunks = len(chunks)
        self.translated_chunks = 0
        self.update_progress_bar()
        
        return chunks
        
    def add_chunk(self, index, content):
        """添加一个块到队列"""
        self.queue.put((index, content))
        
    def add_result(self, index, result):
        """添加翻译结果"""
        with self.lock:
            self.results[index] = result
            self.completed_chunks += 1
            self._update_progress()
            
    def add_failed_chunk(self, index):
        """添加失败的块"""
        with self.lock:
            self.failed_chunks.add(index)
            self.completed_chunks += 1
            self._update_progress()
            
    def _update_progress(self):
        """更新进度显示"""
        if self.progress:
            self.progress.update(self.completed_chunks)
            
    def update_progress_bar(self):
        """更新进度条显示"""
        if not hasattr(self, 'progress') or self.progress is None:
            self.progress = ProgressDisplay(
                total=self.total_chunks,
                prefix="翻译进度",
                suffix="",
                length=40,
                fill='█'
            )
        
        elapsed = time.time() - self.start_time
        if self.translated_chunks > 0:
            remaining = elapsed / self.translated_chunks * (self.total_chunks - self.translated_chunks)
        else:
            remaining = 0
            
        progress_percent = self.translated_chunks / self.total_chunks * 100 if self.total_chunks > 0 else 0
        suffix = f" [用时: {self._format_time(elapsed)}, 剩余: {self._format_time(remaining)}]"
        
        # 更新进度条 - 只传递一个参数
        self.progress.update(self.translated_chunks)
        sys.stdout.flush()
        
    def get_ordered_results(self):
        """获取按顺序排列的翻译结果"""
        if not self.results or len(self.results) != self.total_chunks:
            return None
        
        # 按索引排序结果
        ordered_results = [self.results[i] for i in range(self.total_chunks)]
        return '\n'.join(ordered_results)
        
    def _format_time(self, seconds):
        """格式化时间为 mm:ss 格式"""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
        
    def cancel_translation(self):
        """取消翻译任务"""
        self.is_cancelled = True
        if self.executor:
            self.executor.shutdown(wait=False)
        if self.progress:
            self.progress.finish()
        print("\n\n已取消翻译任务", file=sys.stderr)
        sys.stderr.flush()
        
    def process_queue(self, service, system_prompt):
        """并行处理翻译队列"""
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                self.executor = executor
                futures = []
                
                # 提交所有任务
                while not self.queue.empty() and not self.is_cancelled:
                    index, chunk = self.queue.get()
                    future = executor.submit(self.translate_chunk, service, chunk, system_prompt, index)
                    futures.append(future)
                
                # 等待所有任务完成
                for future in as_completed(futures):
                    if self.is_cancelled:
                        break
                    try:
                        future.result()
                    except Exception as e:
                        print(f"\n任务执行失败: {str(e)}", file=sys.stderr)
                        sys.stderr.flush()
                        
        except KeyboardInterrupt:
            self.cancel_translation()
            raise
        finally:
            self.executor = None
            if self.progress:
                self.progress.finish()
                
    def translate_chunk(self, service, chunk, system_prompt, index):
        """翻译单个块"""
        retries = 0
        while retries < self.max_retries and not self.is_cancelled:
            try:
                # 添加请求间隔
                time.sleep(self.rate_limit_delay)
                result = service.translate(chunk, system_prompt)
                self.add_result(index, result)
                self.translated_chunks += 1
                return True
            except Exception as e:
                retries += 1
                print(f"\n翻译块 {index} 失败 (尝试 {retries}/{self.max_retries}): {str(e)}", file=sys.stderr)
                sys.stderr.flush()
                if retries == self.max_retries:
                    self.add_failed_chunk(index)
                    return False
                # 指数退避
                time.sleep(2 ** retries)
        return False

    def get_chunk(self):
        """
        从队列中获取一个块
        
        Returns:
            tuple: (索引, 内容) 元组，如果队列为空则返回None
        """
        try:
            if self.queue.empty():
                return None
            return self.queue.get(block=False)
        except Exception as e:
            print(f"获取任务失败: {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            sys.stderr.flush()
            return None

def create_retry_session(retries=3, backoff_factor=0.3, 
                        status_forcelist=(500, 502, 504)):
    """创建带有重试机制的会话"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class TranslationCache:
    """翻译结果缓存管理类"""
    
    def __init__(self):
        self.cache_dir = os.path.expanduser("~/.cache/manzh/translations")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_path(self, command_name, section):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{command_name}.{section}.cache")
    
    def get_cached_translation(self, command_name, section):
        """获取缓存的翻译结果"""
        cache_path = self.get_cache_path(command_name, section)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"读取缓存失败：{str(e)}", file=sys.stderr)
                sys.stderr.flush()
        return None
    
    def save_translation(self, command_name, section, content):
        """保存翻译结果到缓存"""
        cache_path = self.get_cache_path(command_name, section)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"保存缓存失败：{str(e)}", file=sys.stderr)
            sys.stderr.flush()
            return False

# 创建全局缓存实例
translation_cache = TranslationCache()

def translate_command(command_name, section="1", force_translate=False):
    """
    翻译指定命令的手册
    
    Args:
        command_name: 命令名称
        section: 手册章节号，默认为1
        force_translate: 是否强制重新翻译，忽略缓存
        
    Returns:
        bool: 翻译是否成功
    """
    queue = None
    try:
        # 检查缓存
        if not force_translate:
            cached_content = translation_cache.get_cached_translation(command_name, section)
            if cached_content:
                print("\n使用缓存的翻译结果...")
                sys.stdout.flush()
                print("\n验证缓存内容...")
                sys.stdout.flush()
                if not is_chinese_content(cached_content):
                    print("缓存内容不是中文，将重新翻译", file=sys.stderr)
                    sys.stderr.flush()
                    force_translate = True
                else:
                    return save_man_page(cached_content, command_name, section)
        
        # 获取man手册内容
        man_result = subprocess.run(['man', command_name], 
                                 capture_output=True, 
                                 text=True)
        
        if man_result.returncode != 0:
            # 尝试获取--help输出
            help_result = subprocess.run([command_name, '--help'], 
                                      capture_output=True, 
                                      text=True)
            if help_result.returncode != 0:
                print(f"错误：无法获取命令 '{command_name}' 的手册或帮助信息")
                sys.stdout.flush()
                return False
            content = help_result.stdout
        else:
            # 使用col命令去除格式控制字符
            col_process = subprocess.Popen(['col', '-b'], 
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        text=True)
            content, _ = col_process.communicate(input=man_result.stdout)
        
        print("\n原始内容长度:", len(content), "字符")
        sys.stdout.flush()
        
        # 获取配置
        from manzh.config_manager import ConfigCache
        config = ConfigCache.get_config()
        
        # 创建翻译服务
        service = create_translation_service(config)
        
        # 设置翻译提示
        system_prompt = f"""
        你是一个专业的技术文档翻译专家。请将以下Linux/Unix命令手册从英文翻译成中文。
        要求：
        1. 保持原始格式，包括空行和缩进
        2. 保留所有命令、选项和示例不翻译
        3. 翻译要准确、专业，符合技术文档风格
        4. 对于专业术语，在首次出现时可以保留英文原文
        5. 保持段落结构不变
        6. 保持简洁，不要添加额外的解释
        7. 确保输出是中文
        """
        
        # 创建翻译队列
        queue = TranslationQueue(
            chunk_size=config.get("translation", {}).get("chunk_size", 4000),
            max_workers=config.get("translation", {}).get("max_workers", 2),
            max_retries=config.get("translation", {}).get("max_retries", 3)
        )
        queue.rate_limit_delay = config.get("translation", {}).get("rate_limit_delay", 2.0)
        
        chunks = queue.prepare_content(content)
        
        # 添加所有块到队列
        for i, chunk in enumerate(chunks):
            queue.add_chunk(i, chunk)
        
        # 开始翻译
        print("\n开始翻译...")
        sys.stdout.flush()
        print(f"总计 {len(chunks)} 个块，使用 {queue.max_workers} 个并行线程")
        sys.stdout.flush()
        print("按 Ctrl+C 可以随时中断翻译")
        sys.stdout.flush()
        
        # 使用并行处理
        queue.process_queue(service, system_prompt)
        
        # 检查是否有失败的块或被取消
        if queue.is_cancelled:
            print("\n翻译已被用户取消")
            sys.stdout.flush()
            return False
            
        if queue.failed_chunks:
            print(f"\n翻译失败：{len(queue.failed_chunks)} 个块翻译失败")
            sys.stdout.flush()
            return False
            
        print("\n整理翻译结果...")
        sys.stdout.flush()
        translated_content = queue.get_ordered_results()
        
        if translated_content is None:
            print("\n错误：无法获取完整的翻译结果")
            sys.stdout.flush()
            return False
            
        print("\n翻译后内容长度:", len(translated_content), "字符")
        sys.stdout.flush()
        
        # 验证翻译结果是否为中文
        if not is_chinese_content(translated_content):
            print("\n错误：翻译结果不包含中文内容，可能翻译失败", file=sys.stderr)
            sys.stderr.flush()
            return False
            
        # 保存翻译结果到缓存
        if config.get("cache", {}).get("enabled", True):
            print("\n保存到缓存...")
            sys.stdout.flush()
            if not translation_cache.save_translation(command_name, section, translated_content):
                print("\n警告：保存到缓存失败", file=sys.stderr)
                sys.stderr.flush()
        
        # 保存翻译结果
        print("\n保存翻译结果...")
        sys.stdout.flush()
        return save_man_page(translated_content, command_name, section)
            
    except KeyboardInterrupt:
        print("\n\n正在清理并退出...", file=sys.stderr)
        sys.stderr.flush()
        if queue:
            queue.cancel_translation()
        return False
    except Exception as e:
        print(f"翻译过程失败：{str(e)}", file=sys.stderr)
        sys.stderr.flush()
        return False

def is_chinese_content(text):
    """
    检查文本是否包含中文内容
    
    Args:
        text: 要检查的文本
        
    Returns:
        bool: 是否包含中文
    """
    if not text:
        return False
        
    # 统计中文字符的数量
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    
    # 如果中文字符数量超过总长度的10%，认为是中文内容
    return chinese_chars > len(text) * 0.1

def save_man_page(content, command_name, section):
    """
    保存翻译后的手册页面
    
    Args:
        content: 翻译后的内容
        command_name: 命令名称
        section: 手册章节号
        
    Returns:
        bool: 保存是否成功
    """
    try:
        if not content:
            print("\n错误：要保存的内容为空", file=sys.stderr)
            sys.stderr.flush()
            return False
            
        if not is_chinese_content(content):
            print("\n错误：要保存的内容不是中文", file=sys.stderr)
            sys.stderr.flush()
            return False
            
        # 创建临时目录
        temp_dir = os.path.expanduser("~/.cache/manzh/temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存到临时文件
        temp_file = os.path.join(temp_dir, f"{command_name}.{section}")
        print(f"\n保存到临时文件：{temp_file}")
        sys.stdout.flush()
        
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        # 验证临时文件
        if not os.path.exists(temp_file):
            print("\n错误：临时文件未创建成功", file=sys.stderr)
            sys.stderr.flush()
            return False
            
        with open(temp_file, "r", encoding="utf-8") as f:
            saved_content = f.read()
            if not is_chinese_content(saved_content):
                print("\n错误：临时文件内容不是中文", file=sys.stderr)
                sys.stderr.flush()
                return False
        
        # 目标目录和文件
        target_dir = os.path.join("/usr/local/share/man/zh_CN", f"man{section}")
        target_file = os.path.join(target_dir, f"{command_name}.{section}")
        
        print(f"\n目标文件路径：{target_file}")
        sys.stdout.flush()
        
        # 使用sudo命令创建目录和复制文件
        try:
            # 检测操作系统类型
            if sys.platform == "darwin":  # macOS
                print("\n在 macOS 上创建目录和复制文件...")
                sys.stdout.flush()
                subprocess.run(['sudo', 'mkdir', '-p', target_dir], check=True)
                subprocess.run(['sudo', 'cp', temp_file, target_file], check=True)
                subprocess.run(['sudo', 'chown', 'root:wheel', target_file], check=True)
                subprocess.run(['sudo', 'chmod', '644', target_file], check=True)
            else:  # Linux
                print("\n在 Linux 上创建目录和复制文件...")
                sys.stdout.flush()
                subprocess.run(['sudo', 'mkdir', '-p', target_dir], check=True)
                subprocess.run(['sudo', 'cp', temp_file, target_file], check=True)
                subprocess.run(['sudo', 'chown', 'root:root', target_file], check=True)
                subprocess.run(['sudo', 'chmod', '644', target_file], check=True)
            
            # 验证目标文件
            if not os.path.exists(target_file):
                print("\n错误：目标文件未创建成功", file=sys.stderr)
                sys.stderr.flush()
                return False
                
            print(f"\n手册已保存到：{target_file}")
            sys.stdout.flush()
            print("\n请使用 'man -L zh_CN <命令>' 查看翻译后的手册")
            sys.stdout.flush()
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n保存手册失败：需要sudo权限")
            sys.stdout.flush()
            print("请使用以下命令手动复制文件：")
            sys.stdout.flush()
            print(f"sudo mkdir -p {target_dir}")
            sys.stdout.flush()
            print(f"sudo cp {temp_file} {target_file}")
            sys.stdout.flush()
            print(f"sudo chown root:{'wheel' if sys.platform == 'darwin' else 'root'} {target_file}")
            sys.stdout.flush()
            print(f"sudo chmod 644 {target_file}")
            sys.stdout.flush()
            return False
            
    except Exception as e:
        print(f"保存手册失败：{str(e)}", file=sys.stderr)
        sys.stderr.flush()
        return False

def main_menu():
    """主菜单"""
    while True:
        print("\n=== ManZH 中文手册翻译工具 ===")
        sys.stdout.flush()
        print("1. 翻译命令手册")
        sys.stdout.flush()
        print("2. 配置管理")
        sys.stdout.flush()
        print("0. 退出")
        sys.stdout.flush()
        
        try:
            choice = input("\n请选择操作 [0-2]: ")
            
            if choice == "0":
                print("\n感谢使用！")
                sys.stdout.flush()
                break
            elif choice == "1":
                command = input("\n请输入要翻译的命令名称：")
                section = input("请输入手册章节号（默认为1）：").strip() or "1"
                force = input("是否强制重新翻译？(y/N): ").lower() == 'y'
                translate_command(command, section, force)
            elif choice == "2":
                config_menu()
            else:
                print("\n无效的选择，请重试")
                sys.stdout.flush()
                
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            sys.stdout.flush()
            continue
        except Exception as e:
            print(f"\n操作失败：{str(e)}", file=sys.stderr)
            sys.stderr.flush()
            continue

class SiliconFlowService(TranslationService):
    """Silicon Flow 翻译服务实现"""
    
    def __init__(self, config):
        self.config = config
        # 验证必要的配置项
        if not config.get("api_key"):
            raise ValueError("配置验证失败：缺少必要配置项：api_key")
        if not config.get("model"):
            raise ValueError("配置验证失败：缺少必要配置项：model")
        if not (config.get("url") or config.get("base_url")):
            raise ValueError("配置验证失败：缺少必要配置项：url 或 base_url")
            
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        
    def _get_api_url(self):
        """获取 API URL"""
        if self.config.get("url"):
            return self.config.get("url")
        base = self.config.get("base_url")
        return f"{base}/v1/chat/completions"
        
    def translate(self, content, system_prompt):
        """
        使用 Silicon Flow API 翻译内容
        
        Args:
            content: 要翻译的内容
            system_prompt: 系统提示
            
        Returns:
            str: 翻译后的内容
        """
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2048),
            "response_format": self.config.get("response_format", {"type": "text"}),
            "stream": False,
            "top_p": self.config.get("top_p", 0.7),
            "top_k": self.config.get("top_k", 50),
            "frequency_penalty": self.config.get("frequency_penalty", 0.5)
        }
        
        try:
            response = self.session.post(
                self._get_api_url(),
                headers=headers,
                json=data,
                timeout=self.config.get("timeout", 60)
            )
            
            if response.status_code != 200:
                print(f"\n错误：API返回状态码 {response.status_code}")
                sys.stdout.flush()
                print(f"详细信息：{response.text}")
                sys.stdout.flush()
                raise ValueError(f"API返回错误：{response.text}")
                
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("API返回结果格式错误：缺少 choices 字段")
                
        except requests.exceptions.Timeout:
            print(f"\n错误：请求超时（{self.config.get('timeout', 60)}秒）", file=sys.stderr)
            sys.stderr.flush()
            raise
        except requests.exceptions.ConnectionError:
            print("\n错误：网络连接失败", file=sys.stderr)
            sys.stderr.flush()
            raise
        except requests.exceptions.RequestException as e:
            print(f"\n错误：请求失败 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise
        except ValueError as e:
            print(f"\n错误：响应解析失败 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise
        except Exception as e:
            print(f"\n错误：未知错误 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise

class OpenRouterService(TranslationService):
    """OpenRouter 翻译服务实现"""
    
    def __init__(self, config):
        self.config = config
        # 验证必要的配置项
        if not config.get("api_key"):
            raise ValueError("配置验证失败：缺少必要配置项：api_key")
        if not config.get("model"):
            raise ValueError("配置验证失败：缺少必要配置项：model")
        if not (config.get("url") or config.get("base_url")):
            raise ValueError("配置验证失败：缺少必要配置项：url 或 base_url")
            
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        
    def _get_api_url(self):
        """获取 API URL"""
        if self.config.get("url"):
            return self.config.get("url")
        base = self.config.get("base_url")
        return f"{base}/chat/completions"
        
    def translate(self, content, system_prompt):
        """
        使用 OpenRouter API 翻译内容
        
        Args:
            content: 要翻译的内容
            system_prompt: 系统提示
            
        Returns:
            str: 翻译后的内容
        """
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        # 添加可选的标题和引用头
        if self.config.get("headers"):
            headers.update(self.config.get("headers"))
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_output_length", 4096),
            "top_p": self.config.get("top_p", 0.7),
            "stream": False
        }
        
        try:
            response = self.session.post(
                self._get_api_url(),
                headers=headers,
                json=data,
                timeout=self.config.get("timeout", 60)
            )
            
            if response.status_code != 200:
                print(f"\n错误：API返回状态码 {response.status_code}")
                sys.stdout.flush()
                print(f"详细信息：{response.text}")
                sys.stdout.flush()
                raise ValueError(f"API返回错误：{response.text}")
                
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("API返回结果格式错误：缺少 choices 字段")
                
        except requests.exceptions.Timeout:
            print(f"\n错误：请求超时（{self.config.get('timeout', 60)}秒）", file=sys.stderr)
            sys.stderr.flush()
            raise
        except requests.exceptions.ConnectionError:
            print("\n错误：网络连接失败", file=sys.stderr)
            sys.stderr.flush()
            raise
        except requests.exceptions.RequestException as e:
            print(f"\n错误：请求失败 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise
        except ValueError as e:
            print(f"\n错误：响应解析失败 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise
        except Exception as e:
            print(f"\n错误：未知错误 - {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            raise
