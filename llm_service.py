from openai import OpenAI
from typing import Dict, Optional, Tuple
import re
from config import OPENAI_API_KEY
from prompts import SYSTEM_PROMPT
from models import Message

class AIService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4o"
    
    def _messages_to_openai_format(self, messages: list[Message]) -> list[Dict]:
        """Преобразует сообщения в формат OpenAI API"""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        return formatted
    
    def _extract_report(self, response_text: str) -> Optional[Dict[str, str]]:
        """Извлекает отчёт из ответа AI"""
        report_pattern = r'\[REPORT\](.*?)\[/REPORT\]'
        match = re.search(report_pattern, response_text, re.DOTALL)
        
        if not match:
            return None
        
        report_text = match.group(1).strip()
        report_dict = {}
        
        for line in report_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                report_dict[key] = value
        
        return report_dict
    
    def _check_conversation_finished(self, response_text: str) -> bool:
        """Проверяет, завершён ли разговор"""
        return '[CONVERSATION_END]' in response_text
    
    def _clean_response(self, response_text: str) -> str:
        """Очищает ответ от служебных маркеров"""
        response_text = re.sub(r'\[CONVERSATION_END\].*?\[/REPORT\].*', '', response_text, flags=re.DOTALL)
        return response_text.strip()
    
    def create_reply(
        self, 
        messages: list[Message]
    ) -> Tuple[str, bool, Optional[Dict[str, str]]]:
        """
        Генерирует ответ AI на основе истории разговора
        
        Returns:
            Tuple[ответ_для_клиента, разговор_завершён, отчёт]
        """
        conversation = self._messages_to_openai_format(messages)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *conversation
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            is_finished = self._check_conversation_finished(response_text)
            report = None
            
            if is_finished:
                report = self._extract_report(response_text)
            
            clean_response = self._clean_response(response_text)
            
            return clean_response, is_finished, report
            
        except Exception as e:
            error_msg = f"Извините, произошла техническая ошибка. Попробуйте позже."
            return error_msg, False, None

