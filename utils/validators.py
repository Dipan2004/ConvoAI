from typing import Tuple
from models.schemas import ChatRequest
from config.settings import settings
from config.constants import ErrorCode


class RequestValidator:
    def validate(self, request: ChatRequest) -> Tuple[bool, str]:
        if not request.session_id or not request.session_id.strip():
            return False, "session_id is required."
        if not request.message or not request.message.strip():
            return False, "message cannot be empty."
        if len(request.message) > settings.max_message_length:
            return False, f"message exceeds {settings.max_message_length} character limit."
        if self._contains_injection(request.message):
            return False, "Invalid input detected."
        return True, ""

    def _contains_injection(self, text: str) -> bool:
        patterns = ["<script", "javascript:", "SELECT ", "DROP TABLE"]
        lowered = text.lower()
        return any(p.lower() in lowered for p in patterns)
