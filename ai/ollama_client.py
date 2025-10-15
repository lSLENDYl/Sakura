"""
Клиент для работы с Ollama API
"""

import asyncio
import ollama
from typing import List, Dict, Optional, AsyncGenerator
from config.config_manager import config
from utils.logger import logger


class OllamaClient:
    """Клиент для взаимодействия с локальной Ollama"""
    
    def __init__(self):
        self.host = config.get('ai.ollama_host', 'http://localhost:11434')
        self.model = config.get('ai.model', 'qwen3:30b')
        self.client = ollama.Client(host=self.host)
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = config.get('personality.conversation_memory', 50)
        
        # Системный промпт
        self.system_prompt = config.get('personality.system_prompt', '')
        
        logger.info(f"Ollama клиент инициализирован. Хост: {self.host}, Модель: {self.model}")
    
    def is_available(self) -> bool:
        """Проверяет доступность Ollama сервера"""
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            
            if self.model not in available_models:
                logger.warning(f"Модель {self.model} не найдена. Доступные модели: {available_models}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ollama сервер недоступен: {e}")
            return False
    
    def add_to_history(self, role: str, content: str) -> None:
        """Добавляет сообщение в историю разговора"""
        self.conversation_history.append({
            'role': role,
            'content': content
        })
        
        # Ограничиваем размер истории
        if len(self.conversation_history) > self.max_history:
            # Сохраняем системный промпт, удаляем старые сообщения
            system_messages = [msg for msg in self.conversation_history if msg['role'] == 'system']
            user_assistant_messages = [msg for msg in self.conversation_history if msg['role'] != 'system']
            
            # Оставляем только последние сообщения
            keep_count = self.max_history - len(system_messages)
            user_assistant_messages = user_assistant_messages[-keep_count:]
            
            self.conversation_history = system_messages + user_assistant_messages
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Формирует список сообщений для отправки в Ollama"""
        messages = []
        
        # Добавляем системный промпт, если он не в истории
        if self.system_prompt and not any(msg['role'] == 'system' for msg in self.conversation_history):
            messages.append({
                'role': 'system', 
                'content': self.system_prompt
            })
        
        # Добавляем историю разговора
        messages.extend(self.conversation_history)
        
        return messages
    
    def generate_response(self, user_input: str) -> str:
        """Генерирует ответ на пользователский ввод"""
        try:
            # Добавляем сообщение пользователя в историю
            self.add_to_history('user', user_input)
            
            # Формируем сообщения для Ollama
            messages = self.get_messages()
            
            logger.info(f"Отправка запроса в Ollama: {user_input[:50]}...")
            
            # Отправляем запрос
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': config.get('ai.temperature', 0.7),
                    'num_ctx': config.get('ai.max_tokens', 1024)
                }
            )
            
            assistant_response = response['message']['content']
            
            # Добавляем ответ в историю
            self.add_to_history('assistant', assistant_response)
            
            logger.info(f"Получен ответ от Ollama: {assistant_response[:50]}...")
            
            return assistant_response
            
        except Exception as e:
            error_msg = f"Ошибка при генерации ответа: {e}"
            logger.error(error_msg)
            return f"Извини, произошла ошибка: {str(e)}"
    
    async def generate_response_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        """Генерирует ответ потоком (для анимации печати)"""
        try:
            # Добавляем сообщение пользователя в историю
            self.add_to_history('user', user_input)
            
            # Формируем сообщения для Ollama
            messages = self.get_messages()
            
            logger.info(f"Отправка потокового запроса в Ollama: {user_input[:50]}...")
            
            response_text = ""
            
            # Отправляем запрос с потоковой передачей
            for chunk in self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    'temperature': config.get('ai.temperature', 0.7),
                    'num_ctx': config.get('ai.max_tokens', 1024)
                }
            ):
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    response_text += content
                    yield content
            
            # Добавляем полный ответ в историю
            self.add_to_history('assistant', response_text)
            
            logger.info(f"Потоковый ответ завершен: {response_text[:50]}...")
            
        except Exception as e:
            error_msg = f"Ошибка при потоковой генерации: {e}"
            logger.error(error_msg)
            yield f"Извини, произошла ошибка: {str(e)}"
    
    def clear_history(self) -> None:
        """Очищает историю разговора"""
        self.conversation_history.clear()
        logger.info("История разговора очищена")
    
    def set_model(self, model_name: str) -> bool:
        """Изменяет используемую модель"""
        try:
            # Проверяем доступность модели
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            
            if model_name not in available_models:
                logger.error(f"Модель {model_name} не найдена. Доступные: {available_models}")
                return False
            
            self.model = model_name
            config.set('ai.model', model_name)
            logger.info(f"Модель изменена на: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при смене модели: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Получает список доступных моделей"""
        try:
            models = self.client.list()
            return [model['name'] for model in models['models']]
        except Exception as e:
            logger.error(f"Ошибка получения списка моделей: {e}")
            return []
