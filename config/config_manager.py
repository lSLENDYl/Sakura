"""
Менеджер конфигурации для приложения Sakura AI
"""

import os
import json
import yaml
from typing import Any, Dict, Optional
from .default_config import DEFAULT_CONFIG


class ConfigManager:
    """Менеджер конфигурации с поддержкой JSON и YAML"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Загружает конфигурацию из файла"""
        if not os.path.exists(self.config_file):
            self.save_config()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)
            
            # Рекурсивно обновляем конфигурацию
            self._deep_update(self.config, user_config)
            
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            print("Используется конфигурация по умолчанию")
    
    def save_config(self) -> None:
        """Сохраняет конфигурацию в файл"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                    
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Получает значение по пути ключа (например, 'ai.model')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Устанавливает значение по пути ключа (например, 'ai.model')
        """
        keys = key_path.split('.')
        config = self.config
        
        # Переходим к предпоследнему уровню
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Устанавливаем значение
        config[keys[-1]] = value
        self.save_config()
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Рекурсивно обновляет словарь"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def reset_to_default(self) -> None:
        """Сбрасывает конфигурацию к значениям по умолчанию"""
        self.config = DEFAULT_CONFIG.copy()
        self.save_config()
    
    def get_section(self, section: str) -> Dict:
        """Получает целую секцию конфигурации"""
        return self.config.get(section, {})
    
    def update_section(self, section: str, updates: Dict) -> None:
        """Обновляет секцию конфигурации"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(updates)
        self.save_config()


# Глобальный экземпляр менеджера конфигурации
config = ConfigManager()
