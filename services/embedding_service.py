from typing import List, Optional
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from config.settings import settings
from utils.logger import AppLogger

logger = AppLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self._model_name = model_name or settings.embedding_model
        self._device = device or settings.embedding_device
        self._model: Optional[SentenceTransformer] = None

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info({"event": "embedding_model_loading", "model": self._model_name})
            self._model = SentenceTransformer(self._model_name, device=self._device)
            logger.info({"event": "embedding_model_loaded", "model": self._model_name})
        return self._model

    def embed(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")
        model = self._load_model()
        vector = model.encode(text.strip(), normalize_embeddings=True, show_progress_bar=False)
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        cleaned = [t.strip() for t in texts if t and t.strip()]
        if not cleaned:
            raise ValueError("No valid texts to embed.")
        model = self._load_model()
        vectors = model.encode(
            cleaned,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return [v.tolist() for v in vectors]

    def dimension(self) -> int:
        model = self._load_model()
        return model.get_sentence_embedding_dimension()