"""
Модуль для синтеза речи с помощью Silero TTS
"""

import os
import torch
import sounddevice as sd
import numpy as np
import threading
from typing import Optional
from config.config_manager import config
from utils.logger import logger


class SileroTTS:
    """Класс для работы с Silero TTS"""
    
    def __init__(self):
        self.model = None
        self.device = torch.device(config.get('tts.device', 'cpu'))
        self.model_name = config.get('tts.model', 'v4_ru')
        self.speaker = config.get('tts.speaker', 'baya')
        self.sample_rate = config.get('tts.sample_rate', 48000)
        self.volume = config.get('tts.volume', 0.8)
        self.speed = config.get('tts.speed', 1.0)
        
        self.is_playing = False
        self.current_audio = None
        
        logger.info(f"Silero TTS инициализирован. Модель: {self.model_name}, Спикер: {self.speaker}")
        
        # Загружаем модель в отдельном потоке
        threading.Thread(target=self._load_model, daemon=True).start()
    
    def _load_model(self) -> None:
        """Загружает модель Silero TTS"""
        try:
            logger.info("Загрузка модели Silero TTS...")
            
            # Загружаем модель из torch.hub
            self.model, example_text = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='ru',
                speaker=self.model_name
            )
            
            self.model.to(self.device)
            
            logger.info("Модель Silero TTS успешно загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели Silero TTS: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Проверяет доступность TTS"""
        return self.model is not None
    
    def synthesize_audio(self, text: str) -> Optional[np.ndarray]:
        """Синтезирует аудио из текста"""
        if not self.is_available():
            logger.error("Модель TTS не загружена")
            return None
        
        try:
            logger.info(f"Синтез речи: {text[:50]}...")
            
            # Генерируем аудио
            audio = self.model.apply_tts(
                text=text,
                speaker=self.speaker,
                sample_rate=self.sample_rate
            )
            
            # Применяем громкость
            if self.volume != 1.0:
                audio = audio * self.volume
            
            # Конвертируем в numpy array
            if isinstance(audio, torch.Tensor):
                audio = audio.detach().cpu().numpy()
            
            logger.info("Синтез речи завершен")
            return audio
            
        except Exception as e:
            logger.error(f"Ошибка синтеза речи: {e}")
            return None
    
    def speak(self, text: str, blocking: bool = False) -> None:
        """Озвучивает текст"""
        if not text.strip():
            return
        
        def _speak():
            # Останавливаем текущее воспроизведение
            self.stop()
            
            # Синтезируем аудио
            audio = self.synthesize_audio(text)
            if audio is None:
                return
            
            try:
                self.is_playing = True
                self.current_audio = audio
                
                logger.info("Начало воспроизведения речи")
                
                # Воспроизводим аудио
                sd.play(audio, samplerate=self.sample_rate)
                sd.wait()  # Ждем завершения воспроизведения
                
                self.is_playing = False
                self.current_audio = None
                
                logger.info("Воспроизведение речи завершено")
                
            except Exception as e:
                logger.error(f"Ошибка воспроизведения: {e}")
                self.is_playing = False
                self.current_audio = None
        
        if blocking:
            _speak()
        else:
            # Запускаем в отдельном потоке
            threading.Thread(target=_speak, daemon=True).start()
    
    def stop(self) -> None:
        """Останавливает воспроизведение"""
        if self.is_playing:
            try:
                sd.stop()
                self.is_playing = False
                self.current_audio = None
                logger.info("Воспроизведение остановлено")
            except Exception as e:
                logger.error(f"Ошибка остановки воспроизведения: {e}")
    
    def save_audio(self, text: str, filename: str) -> bool:
        """Сохраняет синтезированную речь в файл"""
        audio = self.synthesize_audio(text)
        if audio is None:
            return False
        
        try:
            import soundfile as sf
            sf.write(filename, audio, self.sample_rate)
            logger.info(f"Аудио сохранено в файл: {filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения аудио: {e}")
            return False
    
    def set_speaker(self, speaker: str) -> bool:
        """Изменяет спикера"""
        try:
            # Список доступных спикеров для v4_ru
            available_speakers = ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']
            
            if speaker not in available_speakers:
                logger.error(f"Спикер {speaker} недоступен. Доступные: {available_speakers}")
                return False
            
            self.speaker = speaker
            config.set('tts.speaker', speaker)
            logger.info(f"Спикер изменен на: {speaker}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка смены спикера: {e}")
            return False
    
    def set_volume(self, volume: float) -> None:
        """Устанавливает громкость (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        config.set('tts.volume', self.volume)
        logger.info(f"Громкость установлена: {self.volume}")
    
    def set_speed(self, speed: float) -> None:
        """Устанавливает скорость речи"""
        self.speed = max(0.5, min(2.0, speed))
        config.set('tts.speed', self.speed)
        logger.info(f"Скорость речи установлена: {self.speed}")
    
    def get_available_speakers(self) -> list:
        """Возвращает список доступных спикеров"""
        if self.model_name == 'v4_ru':
            return ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']
        else:
            return ['default']
    
    def test_speech(self) -> None:
        """Тестирует синтез речи"""
        test_text = "Привет! Меня зовут Сакура. Проверка синтеза речи."
        self.speak(test_text)
