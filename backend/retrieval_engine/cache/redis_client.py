"""
Redis client for caching and KV storage.
"""
import redis
import json
import hashlib
from typing import Optional, Any, Dict, List
from ..config import settings


class RedisClient:
    """Client for Redis caching and key-value storage."""
    
    # Key prefixes
    PREFIX_QUERY = "query:"
    PREFIX_EMBEDDING = "emb:"
    PREFIX_SECTION = "section:"
    PREFIX_MAPPING = "mapping:"
    PREFIX_SESSION = "session:"
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self) -> redis.Redis:
        """Lazy initialize Redis connection."""
        if self._client is None:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True
            )
        return self._client
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            self.client.ping()
            return True
        except redis.ConnectionError:
            return False
    
    @staticmethod
    def _hash_key(text: str) -> str:
        """Generate a hash for cache keys."""
        return hashlib.md5(text.encode()).hexdigest()
    
    # ==================== Query Cache ====================
    
    def cache_query_response(self, query: str, response: Dict[str, Any]) -> bool:
        """Cache a query response."""
        key = f"{self.PREFIX_QUERY}{self._hash_key(query)}"
        try:
            self.client.setex(
                key,
                settings.QUERY_CACHE_TTL,
                json.dumps(response)
            )
            return True
        except Exception as e:
            print(f"Error caching query: {e}")
            return False
    
    def get_cached_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Get a cached query response."""
        key = f"{self.PREFIX_QUERY}{self._hash_key(query)}"
        try:
            result = self.client.get(key)
            return json.loads(result) if result else None
        except Exception as e:
            print(f"Error getting cached query: {e}")
            return None
    
    # ==================== Section Lookup ====================
    
    def store_section(
        self,
        source: str,  # 'ipc' or 'bns'
        section_number: str,
        language: str,
        data: Dict[str, Any]
    ) -> bool:
        """Store a section for direct lookup."""
        key = f"{self.PREFIX_SECTION}{source}:{section_number}:{language}"
        try:
            self.client.set(key, json.dumps(data))
            return True
        except Exception as e:
            print(f"Error storing section: {e}")
            return False
    
    def get_section(
        self,
        source: str,
        section_number: str,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Get a section by direct lookup."""
        key = f"{self.PREFIX_SECTION}{source}:{section_number}:{language}"
        try:
            result = self.client.get(key)
            return json.loads(result) if result else None
        except Exception as e:
            print(f"Error getting section: {e}")
            return None
    
    # ==================== Mapping Lookup ====================
    
    def store_mapping(
        self,
        ipc_section: str,
        bns_section: str,
        data: Dict[str, Any]
    ) -> bool:
        """Store IPC-BNS mapping for direct lookup."""
        try:
            # Store both directions
            ipc_key = f"{self.PREFIX_MAPPING}ipc:{ipc_section}"
            bns_key = f"{self.PREFIX_MAPPING}bns:{bns_section}"
            
            self.client.set(ipc_key, json.dumps({**data, "direction": "ipc_to_bns"}))
            self.client.set(bns_key, json.dumps({**data, "direction": "bns_to_ipc"}))
            return True
        except Exception as e:
            print(f"Error storing mapping: {e}")
            return False
    
    def get_mapping_by_ipc(self, ipc_section: str) -> Optional[Dict[str, Any]]:
        """Get BNS equivalent for an IPC section."""
        key = f"{self.PREFIX_MAPPING}ipc:{ipc_section}"
        try:
            result = self.client.get(key)
            return json.loads(result) if result else None
        except Exception as e:
            print(f"Error getting mapping: {e}")
            return None
    
    def get_mapping_by_bns(self, bns_section: str) -> Optional[Dict[str, Any]]:
        """Get IPC equivalent for a BNS section."""
        key = f"{self.PREFIX_MAPPING}bns:{bns_section}"
        try:
            result = self.client.get(key)
            return json.loads(result) if result else None
        except Exception as e:
            print(f"Error getting mapping: {e}")
            return None
    
    # ==================== Embedding Cache ====================
    
    def cache_embedding(self, text: str, embedding: List[float]) -> bool:
        """Cache an embedding vector."""
        key = f"{self.PREFIX_EMBEDDING}{self._hash_key(text)}"
        try:
            self.client.setex(
                key,
                settings.EMBEDDING_CACHE_TTL,
                json.dumps(embedding)
            )
            return True
        except Exception as e:
            print(f"Error caching embedding: {e}")
            return False
    
    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get a cached embedding vector."""
        key = f"{self.PREFIX_EMBEDDING}{self._hash_key(text)}"
        try:
            result = self.client.get(key)
            return json.loads(result) if result else None
        except Exception as e:
            print(f"Error getting cached embedding: {e}")
            return None
    
    # ==================== Session Cache ====================
    
    def store_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Store session data."""
        key = f"{self.PREFIX_SESSION}{session_id}"
        try:
            self.client.setex(
                key,
                settings.SESSION_CACHE_TTL,
                json.dumps(data)
            )
            return True
        except Exception as e:
            print(f"Error storing session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        key = f"{self.PREFIX_SESSION}{session_id}"
        try:
            result = self.client.get(key)
            return json.loads(result) if result else None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data (refreshes TTL)."""
        return self.store_session(session_id, data)
    
    # ==================== Utility Methods ====================
    
    def flush_cache(self, prefix: str = None) -> int:
        """Flush cache entries. If prefix provided, only flush matching keys."""
        try:
            if prefix:
                keys = self.client.keys(f"{prefix}*")
                if keys:
                    return self.client.delete(*keys)
                return 0
            else:
                self.client.flushdb()
                return -1  # Indicates full flush
        except Exception as e:
            print(f"Error flushing cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        try:
            return {
                "query_cache": len(self.client.keys(f"{self.PREFIX_QUERY}*")),
                "section_cache": len(self.client.keys(f"{self.PREFIX_SECTION}*")),
                "mapping_cache": len(self.client.keys(f"{self.PREFIX_MAPPING}*")),
                "embedding_cache": len(self.client.keys(f"{self.PREFIX_EMBEDDING}*")),
                "session_cache": len(self.client.keys(f"{self.PREFIX_SESSION}*"))
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}
