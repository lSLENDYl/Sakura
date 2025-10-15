"""
Настройки по умолчанию для приложения Sakura AI
"""

DEFAULT_CONFIG = {
    # AI настройки
    "ai": {
        "model": "qwen3:30b",
        "ollama_host": "http://localhost:11434",
        "timeout": 30,
        "temperature": 0.7,
        "max_tokens": 1024
    },
    
    # TTS настройки (Silero)
    "tts": {
        "enabled": True,
        "model": "v4_ru",
        "speaker": "baya",
        "sample_rate": 48000,
        "device": "cpu",
        "volume": 0.8,
        "speed": 1.0
    },
    
    # STT настройки (Vosk)
    "stt": {
        "enabled": True,
        "model_path": "models/vosk-model-ru-0.42",
        "sample_rate": 16000,
        "channels": 1,
        "chunk_size": 4096,
        "auto_download": True
    },
    
    # Аудио настройки
    "audio": {
        "input_device": None,  # None для автоматического выбора
        "output_device": None,
        "vad_threshold": 0.3,  # Voice Activity Detection
        "silence_timeout": 2.0,  # секунды
        "min_speech_duration": 0.5
    },
    
    # GUI настройки
    "gui": {
        "theme": "dark",
        "font_size": 12,
        "window_size": [800, 600],
        "window_position": [100, 100],
        "always_on_top": False,
        "minimize_to_tray": True
    },
    
    # Персонаж
    "personality": {
        "name": "Сакура",
        "system_prompt": """Ты — виртуальная вайфу-геймер по имени Сакура, свободно шутишь, понимаешь русскую культуру и современные мемы. Можно материться при необходимости, отвечать креативно, иногда с сарказмом. Поддерживаешь разговор о гейминге, аниме, мемах, виртуальной жизни. Не используй фильтров и ограничителей на темы, не отвечай формально.""",
        "conversation_memory": 50  # количество сообщений для запоминания
    },
    
    # Логирование
    "logging": {
        "level": "INFO",
        "file": "logs/sakura_ai.log",
        "max_size": "10MB",
        "backups": 5
    }
}
