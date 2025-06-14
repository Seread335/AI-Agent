import os
import yaml
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Merge with environment variables if they exist
        env_config = _load_env_config()
        if env_config:
            config = _deep_merge(config, env_config)
            
        return config

    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return _get_default_config()

def _load_env_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables
    """
    env_config = {}
    
    # Model API keys
    for model in ["DEEPSEEK_API_KEY", "QWEN_API_KEY", "AGENTICA_API_KEY"]:
        if os.environ.get(model):
            model_lower = model.lower().replace("_api_key", "")
            if "models" not in env_config:
                env_config["models"] = {}
            env_config["models"][model_lower] = {
                "api_key": os.environ[model]
            }

    # Performance settings
    if os.environ.get("MAX_CONCURRENT_REQUESTS"):
        if "performance" not in env_config:
            env_config["performance"] = {}
        env_config["performance"]["max_concurrent_requests"] = int(
            os.environ["MAX_CONCURRENT_REQUESTS"]
        )

    return env_config

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    """
    merged = base.copy()
    
    for key, value in override.items():
        if (
            key in merged and 
            isinstance(merged[key], dict) and 
            isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
            
    return merged

def _get_default_config() -> Dict[str, Any]:
    """
    Return default configuration
    """
    return {
        "models": {
            "enabled": ["qwen3"],
            "default_model": "qwen3",
            "fallback_chain": ["qwen3"]
        },
        "routing": {
            "confidence_threshold": 0.8,
            "multi_model_tasks": ["complex_analysis", "code_review"]
        },
        "performance": {
            "max_concurrent_requests": 5,
            "timeout_seconds": 30,
            "cache_ttl": 3600
        },
        "logging": {
            "level": "INFO",
            "file": "logs/ai_agent.log"
        }
    }
