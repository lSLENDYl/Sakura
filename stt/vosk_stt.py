"""
Модуль для распознавания речи с помощью Vosk
"""

import os
import json
import queue
import threading
import pyaudio
import vosk
import urllib.request
import zipfile
from typing import Optional, Callable
from config.config_manager import config
from utils.logger import logger


class VoskSTT:
    """Класс для работы с Vosk STT"""
    
    def __init__(self):
        self.model = None
        self.recognizer = None
        self.microphone = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_recording = False
        
        # Настройки из конфигурации
        self.model_path = config.get('stt.model_path', 'models/vosk-model-ru-0.42')
        self.sample_rate = config.get('stt.sample_rate', 16000)
        self.channels = config.get('stt.channels', 1)
        self.chunk_size = config.get('stt.chunk_size', 4096)
        self.auto_download = config.get('stt.auto_download', True)
        
        # Callbacks
        self.on_partial_result: Optional[Callable[[str], None]] = None
        self.on_final_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        logger.info(f"Vosk STT инициализирован. Модель: {self.model_path}")
        
        # Инициализируем в отдельном потоке
        threading.Thread(target=self._initialize, daemon=True).start()
    
    def _initialize(self) -> None:
        """Инициализация модели и микрофона"""
        try:
            # Проверяем и скачиваем модель при необходимости
            if not self._ensure_model():
                return
            
            # Загружаем модель
            self._load_model()
            
            # Инициализируем микрофон
            self._init_microphone()
            
            logger.info("Vosk STT успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Vosk STT: {e}")
    
    def _ensure_model(self) -> bool:
        """Проверяет наличие модели и скачивает при необходимости"""
        if os.path.exists(self.model_path):
            logger.info(f"Модель найдена: {self.model_path}")
            return True
        
        if not self.auto_download:
            logger.error(f"Модель не найдена: {self.model_path}")
            return False
        
        logger.info("Модель не найдена. Начинаем загрузку...")
        return self._download_model()
    
    def _download_model(self) -> bool:
        """Скачивает модель Vosk"""
        try:
            model_url = "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip"
            models_dir = os.path.dirname(self.model_path)
            zip_path = os.path.join(models_dir, "vosk-model-ru-0.42.zip")
            
            # Создаем директорию
            os.makedirs(models_dir, exist_ok=True)
            
            logger.info(f"Скачиваем модель с {model_url}")
            
            # Скачиваем файл
            urllib.request.urlretrieve(model_url, zip_path)
            
            logger.info("Распаковываем модель...")
            
            # Распаковываем
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(models_dir)
            
            # Удаляем архив
            os.remove(zip_path)
            
            logger.info("Модель успешно загружена и распакована")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            return False
    
    def _load_model(self) -> None:
        """Загружает модель Vosk"""
        try:
            # Отключаем логи Vosk
            vosk.SetLogLevel(-1)
            
            logger.info("Загрузка модели Vosk...")
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)  # Включаем распознавание отдельных слов
            
            logger.info("Модель Vosk загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели Vosk: {e}")
            raise
    
    def _init_microphone(self) -> None:
        """Инициализирует микрофон"""
        try:
            self.microphone = pyaudio.PyAudio()
            
            # Проверяем наличие устройств ввода
            device_count = self.microphone.get_device_count()
            input_devices = []
            
            for i in range(device_count):
                device_info = self.microphone.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append((i, device_info['name']))
            
            if not input_devices:
                raise Exception("Не найдено устройств ввода аудио")
            
            logger.info(f"Найдено устройств ввода: {len(input_devices)}")
            for device_id, device_name in input_devices:
                logger.info(f"  {device_id}: {device_name}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации микрофона: {e}")
            raise
    
    def is_available(self) -> bool:
        """Проверяет готовность STT к работе"""
        return self.model is not None and self.recognizer is not None and self.microphone is not None
    
    def start_listening(self) -> bool:
        """Начинает непрерывное прослушивание"""
        if not self.is_available():
            logger.error("STT не готов к работе")
            return False
        
        if self.is_listening:
            logger.warning("Прослушивание уже активно")
            return True
        
        try:
            logger.info("Начинаем прослушивание...")
            
            # Открываем поток аудио
            self.audio_stream = self.microphone.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_listening = True
            self.audio_stream.start_stream()
            
            # Запускаем обработку аудио в отдельном потоке
            threading.Thread(target=self._process_audio, daemon=True).start()
            
            logger.info("Прослушивание активировано")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка начала прослушивания: {e}")
            return False
    
    def stop_listening(self) -> None:
        """Останавливает прослушивание"""
        if not self.is_listening:
            return
        
        try:
            logger.info("Останавливаем прослушивание...")
            
            self.is_listening = False
            
            if hasattr(self, 'audio_stream'):
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            
            logger.info("Прослушивание остановлено")
            
        except Exception as e:
            logger.error(f"Ошибка остановки прослушивания: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback для получения аудио данных"""
        if self.is_listening:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def _process_audio(self) -> None:
        """Обрабатывает аудио данные из очереди"""
        while self.is_listening:
            try:
                # Получаем аудио данные
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get(timeout=0.1)
                    
                    # Отправляем в распознаватель
                    if self.recognizer.AcceptWaveform(audio_data):
                        # Финальный результат
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        
                        if text and self.on_final_result:
                            self.on_final_result(text)
                    else:
                        # Частичный результат
                        partial = json.loads(self.recognizer.PartialResult())
                        text = partial.get('partial', '').strip()
                        
                        if text and self.on_partial_result:
                            self.on_partial_result(text)
                            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка обработки аудио: {e}")
                if self.on_error:
                    self.on_error(str(e))
    
    def recognize_file(self, audio_file: str) -> Optional[str]:
        """Распознает речь из аудио файла"""
        if not self.is_available():
            logger.error("STT не готов к работе")
            return None
        
        try:
            import wave
            
            logger.info(f"Распознавание файла: {audio_file}")
            
            wf = wave.open(audio_file, 'rb')
            
            # Проверяем параметры файла
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != self.sample_rate:
                logger.warning(f"Параметры файла не оптимальны. Нужно: 1 канал, 16 бит, {self.sample_rate} Hz")
            
            results = []
            
            # Читаем и обрабатываем файл по частям
            while True:
                data = wf.readframes(self.chunk_size)
                if len(data) == 0:
                    break
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        results.append(text)
            
            # Получаем финальный результат
            final_result = json.loads(self.recognizer.FinalResult())
            text = final_result.get('text', '').strip()
            if text:
                results.append(text)
            
            wf.close()
            
            full_text = ' '.join(results)
            logger.info(f"Распознавание завершено: {full_text[:100]}...")
            
            return full_text if full_text else None
            
        except Exception as e:
            logger.error(f"Ошибка распознавания файла: {e}")
            return None
    
    def set_callbacks(self, 
                     on_partial: Optional[Callable[[str], None]] = None,
                     on_final: Optional[Callable[[str], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None) -> None:
        """Устанавливает callback функции"""
        self.on_partial_result = on_partial
        self.on_final_result = on_final
        self.on_error = on_error
    
    def test_microphone(self) -> bool:
        """Тестирует микрофон"""
        if not self.is_available():
            return False
        
        try:
            logger.info("Тестирование микрофона...")
            
            # Записываем 3 секунды аудио
            stream = self.microphone.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            for _ in range(int(self.sample_rate / self.chunk_size * 3)):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            logger.info("Тест микрофона пройден")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка тестирования микрофона: {e}")
            return False
    
    def __del__(self):
        """Деструктор"""
        self.stop_listening()
        if self.microphone:
            self.microphone.terminate()
