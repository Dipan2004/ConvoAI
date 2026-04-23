import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")
_DEBUG = os.environ.get("DEBUG", "false").lower() == "true"


class AppLogger:
    def __init__(self, name: str, session_id: Optional[str] = None):
        self._name = name
        self._session_id = session_id

    def with_session(self, session_id: str) -> "AppLogger":
        l = AppLogger(self._name, session_id)
        return l

    def info(self, data: Dict[str, Any]) -> None:
        self._emit("INFO", data)

    def error(self, data: Dict[str, Any]) -> None:
        self._emit("ERROR", data)

    def warning(self, data: Dict[str, Any]) -> None:
        self._emit("WARNING", data)

    def debug(self, data: Dict[str, Any]) -> None:
        if _DEBUG:
            self._emit("DEBUG", data)

    def step(
        self,
        step: str,
        session_id: Optional[str] = None,
        latency_ms: Optional[float] = None,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None,
        **extra: Any,
    ) -> None:
        record: Dict[str, Any] = {"step": step}
        sid = session_id or self._session_id
        if sid:
            record["session_id"] = sid
        if latency_ms is not None:
            record["latency_ms"] = round(latency_ms, 2)
        if tokens:
            record["tokens"] = tokens
        if cost is not None:
            record["cost_usd"] = round(cost, 8)
        if error:
            record["error"] = error
        record.update(extra)
        level = "ERROR" if error else "INFO"
        self._emit(level, record)

    def _emit(self, level: str, data: Dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": level,
            "module": self._name,
        }
        if self._session_id and "session_id" not in data:
            record["session_id"] = self._session_id
        record.update(data)
        line = json.dumps(record, default=str, ensure_ascii=False)
        stream = sys.stderr if level == "ERROR" else sys.stdout
        print(line, file=stream, flush=True)
        self._write(line)

    def _write(self, line: str) -> None:
        try:
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass