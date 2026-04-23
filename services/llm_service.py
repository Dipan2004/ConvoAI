import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings
from utils.json_parser import JSONParser
from utils.logger import AppLogger

logger = AppLogger(__name__)

_COST_PER_1K_INPUT: Dict[str, float] = {
    "qwen/qwen-2.5-72b-instruct": 0.0009,
    "minimax/minimax-01": 0.0003,
    "default": 0.001,
}
_COST_PER_1K_OUTPUT: Dict[str, float] = {
    "qwen/qwen-2.5-72b-instruct": 0.0009,
    "minimax/minimax-01": 0.0003,
    "default": 0.001,
}

_FALLBACK_RESPONSE = "Something went wrong. Please try again."


class LLMService:
    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._model = model or settings.model_name
        self._fallback_model = fallback_model or settings.model_fallback
        self._api_key = api_key or settings.openrouter_api_key
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._timeout = settings.llm_timeout_seconds
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature
        self._parser = JSONParser()
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.headers.update({
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-agent-system.internal",
            "X-Title": settings.app_name,
        })
        return session

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        model_override: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        model = model_override or self._model
        messages = self._build_messages(prompt, system, history)
        payload = self._build_payload(messages, temperature, max_tokens, json_mode, model)

        t_start = time.monotonic()
        raw = self._call(payload, session_id=session_id)

        if raw is None:
            payload["model"] = self._fallback_model
            raw = self._call(payload, session_id=session_id)

        latency_ms = (time.monotonic() - t_start) * 1000

        if raw is None:
            logger.step(
                "llm_fallback_triggered",
                session_id=session_id,
                latency_ms=latency_ms,
                error="both primary and fallback models failed",
            )
            return {
                "content": _FALLBACK_RESPONSE,
                "parsed": None,
                "model": None,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "cost_usd": 0.0,
                "latency_ms": round(latency_ms, 2),
            }

        content = self._extract_content(raw)
        usage = raw.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = self._estimate_cost(model, input_tokens, output_tokens)

        logger.step(
            "llm_call",
            session_id=session_id,
            latency_ms=latency_ms,
            tokens={"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens},
            cost=cost,
            model=raw.get("model", model),
        )

        parsed = None
        if json_mode:
            parsed = self._parser.parse(content)

        return {
            "content": content,
            "parsed": parsed,
            "model": raw.get("model", model),
            "tokens": {"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens},
            "cost_usd": cost,
            "latency_ms": round(latency_ms, 2),
        }

    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.generate(
            prompt=prompt,
            system=system,
            history=history,
            json_mode=True,
            session_id=session_id,
        )

    def _call(self, payload: Dict[str, Any], session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        url = f"{self._base_url}/chat/completions"
        try:
            response = self._session.post(url, json=payload, timeout=self._timeout)
            if response.status_code != 200:
                logger.error({
                    "event": "llm_http_error",
                    "status": response.status_code,
                    "body": response.text[:300],
                    "model": payload.get("model"),
                    "session_id": session_id,
                })
                return None
            return response.json()
        except requests.exceptions.Timeout:
            logger.error({
                "event": "llm_timeout",
                "model": payload.get("model"),
                "session_id": session_id,
            })
            return None
        except requests.exceptions.RequestException as exc:
            logger.error({
                "event": "llm_request_error",
                "error": str(exc),
                "session_id": session_id,
            })
            return None
        except Exception as exc:
            logger.error({
                "event": "llm_unexpected_error",
                "error": str(exc),
                "session_id": session_id,
            })
            return None

    def _build_messages(
        self,
        prompt: str,
        system: Optional[str],
        history: Optional[List[Dict[str, str]]],
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages

    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
        json_mode: bool,
        model: str,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self._temperature,
            "max_tokens": min(
                max_tokens if max_tokens is not None else self._max_tokens,
                self._max_tokens,
            ),
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _extract_content(self, response: Dict[str, Any]) -> str:
        try:
            return response["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError):
            return ""

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        in_rate = _COST_PER_1K_INPUT.get(model, _COST_PER_1K_INPUT["default"])
        out_rate = _COST_PER_1K_OUTPUT.get(model, _COST_PER_1K_OUTPUT["default"])
        return (input_tokens / 1000 * in_rate) + (output_tokens / 1000 * out_rate)