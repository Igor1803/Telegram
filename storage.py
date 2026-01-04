from typing import Dict, Optional
from models import ConversationContext, Message
from datetime import datetime
import json

class ConversationRepository:
    """Простое хранилище разговоров в памяти (для MVP)"""
    
    def __init__(self):
        self.conversations: Dict[int, ConversationContext] = {}
    
    def get_conversation(self, user_id: int) -> Optional[ConversationContext]:
        """Получает контекст разговора для пользователя"""
        return self.conversations.get(user_id)
    
    def create_conversation(self, user_id: int) -> ConversationContext:
        """Создаёт новый разговор для пользователя"""
        conversation = ConversationContext(
            user_id=user_id,
            messages=[],
            is_finished=False
        )
        self.conversations[user_id] = conversation
        return conversation
    
    def add_message(self, user_id: int, role: str, content: str):
        """Добавляет сообщение в разговор"""
        if user_id not in self.conversations:
            self.create_conversation(user_id)
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        self.conversations[user_id].messages.append(message)
    
    def finalize_conversation(self, user_id: int, report: Dict[str, str]):
        """Отмечает разговор как завершённый и сохраняет отчёт"""
        if user_id in self.conversations:
            self.conversations[user_id].is_finished = True
            self.conversations[user_id].report = report
    
    def reset_conversation(self, user_id: int):
        """Сбрасывает разговор для пользователя"""
        if user_id in self.conversations:
            del self.conversations[user_id]

