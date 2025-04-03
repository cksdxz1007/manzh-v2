"""
ManZH - Man手册中文翻译工具

一个用于将Linux/Unix man手册翻译成中文的自动化工具，支持多种翻译服务。
"""

__version__ = "2.1.0"
__author__ = "cynning"
__license__ = "MIT"

from .translate import TranslationQueue, create_translation_service
from .config_manager import load_config, ConfigCache
from .man_utils import get_man_page, get_help_output, save_man_page, list_translated_manuals
from .list_manuals import list_manuals
from .clean import clean_manual, clean_section, clean_all, interactive_clean
from .config_cli import (
    interactive_config,
    interactive_add_service,
    interactive_update_service,
    interactive_delete_service,
    interactive_set_default
)
from .optimize import optimize_man_page, optimize_man_directory, interactive_optimize

# 设置环境变量确保输出不缓冲
import os
os.environ["PYTHONUNBUFFERED"] = "1"

__all__ = [
    'TranslationQueue',
    'create_translation_service',
    'load_config',
    'ConfigCache',
    'get_man_page',
    'get_help_output',
    'save_man_page',
    'list_translated_manuals',
    'list_manuals',
    'clean_manual',
    'clean_section',
    'clean_all',
    'interactive_clean',
    'interactive_config',
    'interactive_add_service',
    'interactive_update_service',
    'interactive_delete_service',
    'interactive_set_default',
    'optimize_man_page',
    'optimize_man_directory',
    'interactive_optimize'
]
