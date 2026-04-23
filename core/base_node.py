from abc import ABC, abstractmethod
from typing import Tuple
from models.state import ConversationState


class BaseNode(ABC):
    @abstractmethod
    def execute(self, state: ConversationState, user_input: str) -> Tuple[ConversationState, str]:
        pass

    def _update_turn(self, state: ConversationState, user_input: str) -> ConversationState:
        from models.schemas import Message, Role
        from datetime import datetime
        state.messages.append(Message(role=Role.USER, content=user_input))
        state.turn_count += 1
        state.last_updated = datetime.utcnow()
        return state

    def _append_response(self, state: ConversationState, response: str) -> ConversationState:
        from models.schemas import Message, Role
        state.messages.append(Message(role=Role.ASSISTANT, content=response))
        return state
