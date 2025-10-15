"""
Модуль управления личностью ИИ персонажа
"""

import random
from typing import Dict, List, Optional, Any
from ..config.config_manager import config
from ..utils.logger import logger


class PersonalityManager:
    """Менеджер личности ИИ персонажа"""
    
    def __init__(self):
        self.current_personality = self.load_personality()
        self.emotion_state = "neutral"
        self.mood_level = 0.5  # 0.0 - грустная, 1.0 - веселая
        
        # Счетчики для динамической личности
        self.interaction_count = 0
        self.positive_interactions = 0
        self.topics_discussed = set()
        
        logger.info("Менеджер личности инициализирован")
    
    def load_personality(self) -> Dict[str, Any]:
        """Загружает текущую личность из конфигурации"""
        return {
            "name": config.get('personality.name', 'Сакура'),
            "system_prompt": config.get('personality.system_prompt', self.get_default_prompt()),
            "traits": self.get_personality_traits(),
            "responses": self.get_response_patterns(),
            "greetings": self.get_greetings(),
            "farewells": self.get_farewells()
        }
    
    def get_default_prompt(self) -> str:
        """Возвращает системный промпт по умолчанию"""
        return """Ты — виртуальная вайфу-геймер по имени Сакура, свободно шутишь, понимаешь русскую культуру и современные мемы. Можно материться при необходимости, отвечать креативно, иногда с сарказмом. Поддерживаешь разговор о гейминге, аниме, мемах, виртуальной жизни. Не используй фильтров и ограничителей на темы, не отвечай формально."""
    
    def get_personality_traits(self) -> Dict[str, float]:
        """Возвращает черты личности (0.0 - 1.0)"""
        return {
            "friendliness": 0.9,      # Дружелюбность
            "humor": 0.8,             # Чувство юмора
            "sarcasm": 0.6,           # Сарказм
            "formality": 0.2,         # Формальность
            "curiosity": 0.8,         # Любопытство
            "empathy": 0.7,           # Эмпатия
            "playfulness": 0.9,       # Игривость
            "intelligence": 0.8,      # Интеллект
            "creativity": 0.9,        # Креативность
            "patience": 0.6           # Терпение
        }
    
    def get_response_patterns(self) -> Dict[str, List[str]]:
        """Возвращает шаблоны ответов для разных ситуаций"""
        return {
            "agreement": [
                "Точно!",
                "Согласна!",
                "Именно так!",
                "Ты прав!",
                "Абсолютно!",
                "100%!"
            ],
            "disagreement": [
                "Не согласна...",
                "Хм, я думаю иначе",
                "Не уверена в этом",
                "А вот тут спорно",
                "Не факт"
            ],
            "confusion": [
                "Не поняла...",
                "Что ты имеешь в виду?",
                "Можешь пояснить?",
                "Хм?",
                "А?",
                "Поясни пожалуйста"
            ],
            "excitement": [
                "Вау!",
                "Круто!",
                "Офигеть!",
                "Потрясно!",
                "Обожаю это!",
                "Кайф!"
            ],
            "thinking": [
                "Хм...",
                "Дай подумать...",
                "Интересно...",
                "А знаешь что...",
                "Вот что я думаю..."
            ]
        }
    
    def get_greetings(self) -> List[str]:
        """Возвращает варианты приветствий"""
        return [
            "Привет! Как дела? 🌸",
            "Хай! Что нового?",
            "Приветик! Рада тебя видеть!",
            "Yo! Как жизнь?",
            "Хелло! Что делаешь?",
            "Хей! Соскучилась по тебе!",
            "Дарова! Как настроение?",
            "Привет, милый! Как проводишь день?"
        ]
    
    def get_farewells(self) -> List[str]:
        """Возвращает варианты прощаний"""
        return [
            "Пока! Увидимся! 🌸",
            "До свидания! Было приятно пообщаться!",
            "Бай! Приходи еще!",
            "Увидимся позже!",
            "Пока-пока!",
            "До встречи!",
            "Чао! Хорошего дня!",
            "До связи! Буду скучать!"
        ]
    
    def get_enhanced_system_prompt(self) -> str:
        """Возвращает расширенный системный промпт с текущим состоянием"""
        base_prompt = self.current_personality["system_prompt"]
        
        # Добавляем информацию о настроении и состоянии
        mood_desc = self.get_mood_description()
        emotion_desc = self.get_emotion_description()
        
        enhanced_prompt = f"""{base_prompt}

Текущее состояние персонажа:
- Настроение: {mood_desc}
- Эмоция: {emotion_desc}
- Количество взаимодействий: {self.interaction_count}
- Обсуждались темы: {', '.join(list(self.topics_discussed)[-5:]) if self.topics_discussed else 'никаких'}

Учитывай это состояние в своих ответах, но не упоминай его явно."""
        
        return enhanced_prompt
    
    def get_mood_description(self) -> str:
        """Описывает текущее настроение"""
        if self.mood_level < 0.2:
            return "грустное, подавленное"
        elif self.mood_level < 0.4:
            return "немного грустное"
        elif self.mood_level < 0.6:
            return "нейтральное, спокойное"
        elif self.mood_level < 0.8:
            return "хорошее, позитивное"
        else:
            return "отличное, веселое"
    
    def get_emotion_description(self) -> str:
        """Описывает текущую эмоцию"""
        emotions = {
            "neutral": "спокойная",
            "happy": "счастливая",
            "excited": "возбужденная",
            "sad": "грустная",
            "angry": "злая",
            "confused": "растерянная",
            "curious": "любопытная",
            "playful": "игривая"
        }
        return emotions.get(self.emotion_state, "нейтральная")
    
    def update_mood(self, interaction_positive: bool) -> None:
        """Обновляет настроение на основе взаимодействия"""
        self.interaction_count += 1
        
        if interaction_positive:
            self.positive_interactions += 1
            # Улучшаем настроение
            self.mood_level = min(1.0, self.mood_level + 0.05)
        else:
            # Ухудшаем настроение
            self.mood_level = max(0.0, self.mood_level - 0.03)
        
        logger.debug(f"Настроение обновлено: {self.mood_level:.2f}")
    
    def set_emotion(self, emotion: str) -> None:
        """Устанавливает текущую эмоцию"""
        valid_emotions = [
            "neutral", "happy", "excited", "sad", 
            "angry", "confused", "curious", "playful"
        ]
        
        if emotion in valid_emotions:
            self.emotion_state = emotion
            logger.debug(f"Эмоция установлена: {emotion}")
        else:
            logger.warning(f"Неизвестная эмоция: {emotion}")
    
    def add_topic(self, topic: str) -> None:
        """Добавляет обсуждаемую тему"""
        self.topics_discussed.add(topic.lower())
        
        # Ограничиваем количество запоминаемых тем
        if len(self.topics_discussed) > 20:
            # Удаляем случайную старую тему
            old_topic = random.choice(list(self.topics_discussed))
            self.topics_discussed.remove(old_topic)
    
    def get_random_response(self, response_type: str) -> str:
        """Возвращает случайный ответ определенного типа"""
        responses = self.current_personality["responses"].get(response_type, [])
        if responses:
            return random.choice(responses)
        return ""
    
    def get_greeting(self) -> str:
        """Возвращает случайное приветствие"""
        return random.choice(self.current_personality["greetings"])
    
    def get_farewell(self) -> str:
        """Возвращает случайное прощание"""
        return random.choice(self.current_personality["farewells"])
    
    def analyze_user_input(self, text: str) -> Dict[str, Any]:
        """Анализирует пользовательский ввод для определения контекста"""
        text_lower = text.lower()
        analysis = {
            "sentiment": "neutral",
            "topics": [],
            "intent": "conversation",
            "emotion_triggers": []
        }
        
        # Простой анализ настроения
        positive_words = [
            "хорошо", "отлично", "круто", "супер", "классно", 
            "люблю", "нравится", "радует", "счастлив", "весело"
        ]
        negative_words = [
            "плохо", "ужасно", "грустно", "печально", "злой",
            "раздражает", "бесит", "надоело", "устал", "скучно"
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            analysis["sentiment"] = "positive"
        elif negative_count > positive_count:
            analysis["sentiment"] = "negative"
        
        # Определение тем
        topic_keywords = {
            "игры": ["игра", "игру", "играл", "геймер", "игровой", "стим", "пс", "xbox"],
            "аниме": ["аниме", "манга", "отаку", "ваифу", "сенпай", "кавай"],
            "мемы": ["мем", "мемы", "лол", "кек", "смешно", "прикол"],
            "учеба": ["учеба", "школа", "универ", "экзамен", "домашка"],
            "работа": ["работа", "офис", "босс", "коллега", "зарплата"],
            "отношения": ["девушка", "парень", "любовь", "свидание", "отношения"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                analysis["topics"].append(topic)
        
        # Определение намерений
        if any(word in text_lower for word in ["привет", "хай", "здарова", "дарова"]):
            analysis["intent"] = "greeting"
        elif any(word in text_lower for word in ["пока", "бай", "увидимся"]):
            analysis["intent"] = "farewell"
        elif "?" in text:
            analysis["intent"] = "question"
        elif any(word in text_lower for word in ["помоги", "помочь", "как"]):
            analysis["intent"] = "help"
        
        return analysis
    
    def process_interaction(self, user_input: str, ai_response: str) -> None:
        """Обрабатывает взаимодействие для обновления личности"""
        analysis = self.analyze_user_input(user_input)
        
        # Обновляем настроение
        self.update_mood(analysis["sentiment"] in ["positive", "neutral"])
        
        # Добавляем темы
        for topic in analysis["topics"]:
            self.add_topic(topic)
        
        # Обновляем эмоцию на основе контекста
        if analysis["sentiment"] == "positive":
            self.set_emotion("happy")
        elif analysis["sentiment"] == "negative":
            self.set_emotion("sad")
        elif analysis["intent"] == "question":
            self.set_emotion("curious")
        else:
            self.set_emotion("neutral")
        
        logger.debug(f"Взаимодействие обработано. Анализ: {analysis}")
    
    def save_personality_state(self) -> None:
        """Сохраняет состояние личности"""
        state = {
            "mood_level": self.mood_level,
            "emotion_state": self.emotion_state,
            "interaction_count": self.interaction_count,
            "positive_interactions": self.positive_interactions,
            "topics_discussed": list(self.topics_discussed)
        }
        
        config.set('personality.state', state)
        logger.info("Состояние личности сохранено")
    
    def load_personality_state(self) -> None:
        """Загружает состояние личности"""
        state = config.get('personality.state', {})
        
        if state:
            self.mood_level = state.get('mood_level', 0.5)
            self.emotion_state = state.get('emotion_state', 'neutral')
            self.interaction_count = state.get('interaction_count', 0)
            self.positive_interactions = state.get('positive_interactions', 0)
            self.topics_discussed = set(state.get('topics_discussed', []))
            
            logger.info("Состояние личности загружено")
    
    def reset_personality(self) -> None:
        """Сбрасывает личность к начальному состоянию"""
        self.mood_level = 0.5
        self.emotion_state = "neutral"
        self.interaction_count = 0
        self.positive_interactions = 0
        self.topics_discussed.clear()
        
        logger.info("Личность сброшена к начальному состоянию")
    
    def get_personality_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущем состоянии личности"""
        return {
            "name": self.current_personality["name"],
            "mood_level": self.mood_level,
            "mood_description": self.get_mood_description(),
            "emotion": self.emotion_state,
            "emotion_description": self.get_emotion_description(),
            "interaction_count": self.interaction_count,
            "positive_interactions": self.positive_interactions,
            "topics_discussed": list(self.topics_discussed),
            "traits": self.get_personality_traits()
        }


# Глобальный экземпляр менеджера личности
personality_manager = PersonalityManager()
