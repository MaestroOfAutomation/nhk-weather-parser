"""
Configuration module for loading and accessing application settings.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, cast


class Config:
    """
    Configuration manager for the application.
    
    Loads settings from a JSON file and provides access to configuration values.
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the configuration manager.
        
        :param config_path: Path to the configuration file. If None, uses default path.
        """
        self._config_path: str = config_path or os.environ.get(
            "CONFIG_PATH", 
            str(Path(__file__).parent.parent.parent / "config.json")
        )
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """
        Load configuration from the JSON file.
        
        :raises FileNotFoundError: If the configuration file doesn't exist.
        :raises json.JSONDecodeError: If the configuration file contains invalid JSON.
        """
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self._config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file: {self._config_path}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        :param section: Configuration section name.
        :param key: Configuration key within the section.
        :param default: Default value if the key doesn't exist.
        :return: Configuration value or default.
        """
        if section not in self._config:
            return default
        return self._config[section].get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        :param section: Configuration section name.
        :return: Dictionary containing the section configuration.
        """
        return self._config.get(section, {})
    
    @property
    def deepseek_api_key(self) -> str:
        """Get the DeepSeek API key."""
        return cast(str, self.get('deepseek', 'api_key') or os.environ.get('DEEPSEEK_API_KEY', ''))
    
    @property
    def deepseek_api_url(self) -> str:
        """Get the DeepSeek API URL."""
        return cast(str, self.get('deepseek', 'api_url', 'https://api.deepseek.com/chat/completions'))
    
    @property
    def deepseek_model(self) -> str:
        """Get the DeepSeek model name."""
        return cast(str, self.get('deepseek', 'model', 'deepseek-chat'))
    
    @property
    def telegram_bot_token(self) -> str:
        """Get the Telegram bot token."""
        return cast(str, self.get('telegram', 'bot_token') or os.environ.get('TELEGRAM_BOT_TOKEN', ''))
    
    @property
    def telegram_chat_id(self) -> str:
        """Get the Telegram chat ID."""
        return cast(str, self.get('telegram', 'chat_id') or os.environ.get('TELEGRAM_CHAT_ID', ''))
    
    @property
    def nhk_url(self) -> str:
        """Get the NHK website URL."""
        return cast(str, self.get('nhk', 'url', 'https://www.nhk.or.jp/kishou-saigai/'))
    
    @property
    def nhk_map_selector(self) -> str:
        """Get the CSS selector for the NHK weather map."""
        return cast(str, self.get('nhk', 'map_selector', '.theWeatherForecastWeeklyMap'))
    
    @property
    def schedule_hours(self) -> int:
        """Get the scheduled execution hours (UTC)."""
        return cast(int, self.get('schedule', 'hours', 16))
    
    @property
    def schedule_minutes(self) -> int:
        """Get the scheduled execution minutes (UTC)."""
        return cast(int, self.get('schedule', 'minutes', 0))


config = Config()