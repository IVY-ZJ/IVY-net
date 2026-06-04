"""
配置加载模块 —— 从 .env 文件和环境变量中读取 LLM 配置

支持的 LLM 提供商:
  - deepseek: DeepSeek API (默认)
  - openai:   OpenAI API
  - qwen:     通义千问 (DashScope)
  - custom:   自定义 API 地址
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件（命令行运行时从项目根目录加载）
load_dotenv()

# 提供商默认配置
PROVIDER_CONFIG = {
    "deepseek": {
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "openai": {
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4o",
    },
    "qwen": {
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
}


def load_config() -> dict:
    """
    加载 LLM 配置

    优先级: 环境变量 > .env 文件 > 默认值

    Returns:
        dict: {
            "api_key": str,
            "api_base": str,
            "model": str,
            "temperature": float,
        }
    """
    provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()

    # API Key（必填）
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "未找到 LLM_API_KEY。请在 .env 文件中设置，或设置环境变量。\n"
            "示例: LLM_API_KEY=sk-your-api-key-here"
        )

    # 获取提供商默认配置
    defaults = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["deepseek"])

    config = {
        "api_key": api_key,
        "api_base": os.getenv("LLM_API_BASE", "").strip() or defaults["api_base"],
        "model": os.getenv("LLM_MODEL", "").strip() or defaults["model"],
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
    }

    return config