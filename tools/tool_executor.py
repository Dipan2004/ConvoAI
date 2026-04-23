import time
from typing import Any, Callable, Dict, Optional
from models.schemas import ToolCallRecord
from models.state import ConversationState
from config.constants import ErrorCode
from utils.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    def __init__(self):
        self._registry: Dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        self._registry[name] = fn

    def execute(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        state: ConversationState,
    ) -> tuple[Any, ConversationState]:
        if tool_name not in self._registry:
            raise ValueError(f"Tool not registered: {tool_name}")

        record = ToolCallRecord(tool_name=tool_name, inputs=inputs)
        start = time.monotonic()

        try:
            output = self._registry[tool_name](**inputs)
            record.output = output
            record.success = True
        except Exception as exc:
            record.success = False
            record.error = str(exc)
            logger.error({
                "event": "tool_failed",
                "tool": tool_name,
                "error": str(exc),
                "session_id": state.session_id,
            })
            output = None
        finally:
            record.latency_ms = (time.monotonic() - start) * 1000
            state.tool_calls.append(record)

        logger.info({
            "event": "tool_executed",
            "tool": tool_name,
            "success": record.success,
            "latency_ms": record.latency_ms,
            "session_id": state.session_id,
        })
        return output, state