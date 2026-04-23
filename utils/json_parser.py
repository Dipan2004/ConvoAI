import json
import re
from typing import Any, Dict, Optional

from utils.logger import AppLogger

logger = AppLogger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
_INLINE_RE = re.compile(r"(\{[\s\S]*?\}|\[[\s\S]*?\])")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class JSONParser:
    def parse(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {}

        result = self._try(text.strip())
        if result is not None:
            return result

        fence = _FENCE_RE.search(text)
        if fence:
            result = self._try(fence.group(1).strip())
            if result is not None:
                return result

        inline = _INLINE_RE.search(text)
        if inline:
            result = self._try(inline.group(1).strip())
            if result is not None:
                return result

        cleaned = self._clean(text)
        result = self._try(cleaned)
        if result is not None:
            return result

        logger.warning({"event": "json_parse_failed", "preview": text[:200]})
        return {}

    def parse_strict(self, text: str) -> Dict[str, Any]:
        result = self.parse(text)
        if not result:
            raise ValueError(f"Could not parse JSON from: {text[:200]}")
        return result

    def _try(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"data": parsed}
            return {"value": parsed}
        except (json.JSONDecodeError, ValueError):
            return None

    def _clean(self, text: str) -> str:
        text = _CONTROL_RE.sub("", text)
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return text.strip()