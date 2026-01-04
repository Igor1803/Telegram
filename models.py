from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime

@dataclass
class ConversationContext:
    user_id: int
    messages: List[Message]
    is_finished: bool
    report: Optional[Dict[str, str]] = None

@dataclass
class ClientProfile:
    request: str
    timeline: str
    scale: str
    budget_readiness: str
    next_step: str
    priority: str

