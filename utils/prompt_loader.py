import os
from typing import Dict

from utils.logger import AppLogger

logger = AppLogger(__name__)

_DEFAULT_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


class PromptLoader:
    def __init__(self, prompts_dir: str = _DEFAULT_PROMPTS_DIR):
        self._dir = os.path.abspath(prompts_dir)
        self._cache: Dict[str, str] = {}

    def load(self, name: str) -> str:
        if name in self._cache:
            return self._cache[name]

        path = os.path.join(self._dir, f"{name}.txt")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Prompt file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            raise ValueError(f"Prompt file is empty: {path}")

        self._cache[name] = content
        logger.info({"event": "prompt_loaded", "name": name, "path": path})
        return content

    def reload(self, name: str) -> str:
        self._cache.pop(name, None)
        return self.load(name)

    def preload_all(self) -> None:
        if not os.path.isdir(self._dir):
            logger.warning({"event": "prompts_dir_missing", "path": self._dir})
            return
        for fname in os.listdir(self._dir):
            if fname.endswith(".txt"):
                name = fname[:-4]
                try:
                    self.load(name)
                except (FileNotFoundError, ValueError) as exc:
                    logger.error({"event": "prompt_preload_failed", "name": name, "error": str(exc)})

    def list_loaded(self) -> list[str]:
        return list(self._cache.keys())