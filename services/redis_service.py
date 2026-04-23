import json
from typing import Any, Dict, Optional

import msgpack
import redis

from config.settings import settings
from utils.logger import AppLogger

logger = AppLogger(__name__)


class RedisService:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: Optional[int] = None,
        use_msgpack: bool = True,
    ):
        self._host = host or settings.redis_host
        self._port = port or settings.redis_port
        self._db = db
        self._password = password or settings.redis_password
        self._default_ttl = default_ttl or settings.redis_ttl_seconds
        self._use_msgpack = use_msgpack
        self._client = redis.Redis(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        self._verify_connection()

    def _verify_connection(self) -> None:
        try:
            self._client.ping()
            logger.info({"event": "redis_connected", "host": self._host, "port": self._port})
        except redis.ConnectionError as exc:
            logger.error({"event": "redis_connection_failed", "error": str(exc)})
            raise

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            raw = self._client.get(key)
            if raw is None:
                return None
            return self._deserialize(raw)
        except redis.RedisError as exc:
            logger.error({"event": "redis_get_error", "key": key, "error": str(exc)})
            return None

    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        try:
            serialized = self._serialize(value)
            expire = ttl if ttl is not None else self._default_ttl
            self._client.setex(key, expire, serialized)
            return True
        except redis.RedisError as exc:
            logger.error({"event": "redis_set_error", "key": key, "error": str(exc)})
            return False

    def delete(self, key: str) -> bool:
        try:
            self._client.delete(key)
            return True
        except redis.RedisError as exc:
            logger.error({"event": "redis_delete_error", "key": key, "error": str(exc)})
            return False

    def exists(self, key: str) -> bool:
        try:
            return bool(self._client.exists(key))
        except redis.RedisError:
            return False

    def refresh_ttl(self, key: str, ttl: Optional[int] = None) -> bool:
        try:
            expire = ttl if ttl is not None else self._default_ttl
            return bool(self._client.expire(key, expire))
        except redis.RedisError:
            return False

    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except redis.RedisError:
            return False

    def _serialize(self, value: Dict[str, Any]) -> bytes:
        if self._use_msgpack:
            return msgpack.packb(value, use_bin_type=True)
        return json.dumps(value).encode("utf-8")

    def _deserialize(self, raw: bytes) -> Dict[str, Any]:
        if self._use_msgpack:
            return msgpack.unpackb(raw, raw=False)
        return json.loads(raw.decode("utf-8"))