"""
Redis Cache Service for fast key-value lookups.

Features:
- Mapping Cache: IPC Section → BNS Section (and vice versa)
- Response Cache: Cache full query responses
- Section Cache: Direct section lookups
"""

import redis
import json
import hashlib
from typing import Optional, Any

class CacheService:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize Redis connection.
        Falls back gracefully if Redis is not available.
        """
        self.enabled = False
        self.client = None
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=2  # Fail fast if Redis not running
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            print("[Cache] Redis connected successfully.")
        except redis.ConnectionError:
            print("[Cache Warning] Redis not available. Caching disabled.")
            self.enabled = False
        except Exception as e:
            print(f"[Cache Warning] Redis error: {e}. Caching disabled.")
            self.enabled = False
    
    def _generate_key(self, prefix: str, value: str) -> str:
        """Generate a cache key with prefix."""
        return f"{prefix}:{value.lower().strip()}"
    
    def _hash_query(self, query: str, collections: list = None) -> str:
        """Generate a hash for query + collections to use as cache key."""
        cache_input = f"{query}:{sorted(collections) if collections else 'all'}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    # =========================================================================
    # MAPPING CACHE: IPC ↔ BNS
    # =========================================================================
    
    def get_mapping_by_ipc(self, ipc_section: str) -> Optional[dict]:
        """Get BNS equivalent for an IPC section."""
        if not self.enabled:
            return None
        try:
            key = self._generate_key("map:ipc", ipc_section)
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    def get_mapping_by_bns(self, bns_section: str) -> Optional[dict]:
        """Get IPC equivalent for a BNS section."""
        if not self.enabled:
            return None
        try:
            key = self._generate_key("map:bns", bns_section)
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    def set_mapping(self, ipc_section: str, bns_section: str, metadata: dict):
        """Store a mapping in both directions."""
        if not self.enabled:
            return
        try:
            data = json.dumps({
                "ipc_section": ipc_section,
                "bns_section": bns_section,
                **metadata
            })
            # Store in both directions for O(1) lookup
            self.client.set(self._generate_key("map:ipc", ipc_section), data)
            self.client.set(self._generate_key("map:bns", bns_section), data)
        except Exception as e:
            print(f"[Cache Error] Failed to set mapping: {e}")
    
    # =========================================================================
    # RESPONSE CACHE: Full query responses
    # =========================================================================
    
    def get_response(self, query: str, collections: list = None) -> Optional[dict]:
        """Get cached response for a query."""
        if not self.enabled:
            return None
        try:
            key = f"resp:{self._hash_query(query, collections)}"
            data = self.client.get(key)
            if data:
                print(f"[Cache] HIT for query: {query[:30]}...")
                return json.loads(data)
            return None
        except Exception:
            return None
    
    def set_response(self, query: str, collections: list, response: dict, ttl: int = 3600):
        """
        Cache a query response.
        
        Args:
            ttl: Time-to-live in seconds (default 1 hour)
        """
        if not self.enabled:
            return
        try:
            key = f"resp:{self._hash_query(query, collections)}"
            self.client.setex(key, ttl, json.dumps(response))
        except Exception as e:
            print(f"[Cache Error] Failed to cache response: {e}")
    
    # =========================================================================
    # SECTION CACHE: Direct section lookups
    # =========================================================================
    
    def get_section(self, collection: str, section_number: str) -> Optional[dict]:
        """Get cached section by number."""
        if not self.enabled:
            return None
        try:
            key = self._generate_key(f"sec:{collection}", section_number)
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    def set_section(self, collection: str, section_number: str, section_data: dict):
        """Cache a section."""
        if not self.enabled:
            return
        try:
            key = self._generate_key(f"sec:{collection}", section_number)
            self.client.set(key, json.dumps(section_data))
        except Exception as e:
            print(f"[Cache Error] Failed to cache section: {e}")
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def clear_all(self):
        """Clear all cached data. Use with caution!"""
        if self.enabled:
            self.client.flushdb()
            print("[Cache] All data cleared.")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}
        try:
            info = self.client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "total_keys": self.client.dbsize()
            }
        except Exception:
            return {"enabled": False}
    
    # =========================================================================
    # CHAT HISTORY: Multiple conversations with memory
    # =========================================================================
    
    def create_chat(self, chat_id: str, name: str = "New Chat") -> dict:
        """Create a new chat session."""
        if not self.enabled:
            return None
        try:
            import time
            chat_data = {
                "id": chat_id,
                "name": name,
                "created_at": time.time(),
                "updated_at": time.time(),
                "messages": []
            }
            self.client.set(f"chat:{chat_id}", json.dumps(chat_data))
            # Add to chat index
            self.client.sadd("chat:index", chat_id)
            return chat_data
        except Exception as e:
            print(f"[Cache Error] Failed to create chat: {e}")
            return None
    
    def get_chat(self, chat_id: str) -> Optional[dict]:
        """Get a chat by ID."""
        if not self.enabled:
            return None
        try:
            data = self.client.get(f"chat:{chat_id}")
            return json.loads(data) if data else None
        except Exception:
            return None
    
    def list_chats(self) -> list:
        """List all chats, sorted by last updated."""
        if not self.enabled:
            return []
        try:
            chat_ids = self.client.smembers("chat:index")
            chats = []
            for chat_id in chat_ids:
                chat = self.get_chat(chat_id)
                if chat:
                    chats.append({
                        "id": chat["id"],
                        "name": chat["name"],
                        "created_at": chat["created_at"],
                        "updated_at": chat["updated_at"],
                        "message_count": len(chat.get("messages", []))
                    })
            # Sort by updated_at (newest first)
            chats.sort(key=lambda x: x["updated_at"], reverse=True)
            return chats
        except Exception as e:
            print(f"[Cache Error] Failed to list chats: {e}")
            return []
    
    def add_message(self, chat_id: str, role: str, content: str) -> bool:
        """Add a message to a chat."""
        if not self.enabled:
            return False
        try:
            import time
            chat = self.get_chat(chat_id)
            if not chat:
                return False
            chat["messages"].append({
                "role": role,
                "content": content,
                "timestamp": time.time()
            })
            chat["updated_at"] = time.time()
            self.client.set(f"chat:{chat_id}", json.dumps(chat))
            return True
        except Exception as e:
            print(f"[Cache Error] Failed to add message: {e}")
            return False
    
    def rename_chat(self, chat_id: str, new_name: str) -> bool:
        """Rename a chat."""
        if not self.enabled:
            return False
        try:
            chat = self.get_chat(chat_id)
            if not chat:
                return False
            chat["name"] = new_name
            self.client.set(f"chat:{chat_id}", json.dumps(chat))
            return True
        except Exception as e:
            print(f"[Cache Error] Failed to rename chat: {e}")
            return False
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat."""
        if not self.enabled:
            return False
        try:
            self.client.delete(f"chat:{chat_id}")
            self.client.srem("chat:index", chat_id)
            return True
        except Exception as e:
            print(f"[Cache Error] Failed to delete chat: {e}")
            return False
    
    def get_chat_messages(self, chat_id: str, limit: int = 10) -> list:
        """Get recent messages from a chat for context."""
        chat = self.get_chat(chat_id)
        if not chat:
            return []
        messages = chat.get("messages", [])
        # Return last N messages
        return messages[-limit:] if limit else messages
    
    # =========================================================================
    # QUICK MAPPING: Instant IPC ↔ BNS lookups
    # =========================================================================
    
    def quick_lookup_ipc(self, ipc_section: str) -> Optional[dict]:
        """
        Instant IPC → BNS lookup from pre-loaded mapping.
        Returns: {"ipc": "302", "bns": "103(1)", "category": "Grave Offences..."}
        """
        if not self.enabled:
            return None
        try:
            # Normalize: remove spaces, parentheses, lowercase
            key = ipc_section.lower().replace(" ", "").replace("(", "").replace(")", "")
            data = self.client.get(f"quick:ipc:{key}")
            if data:
                print(f"[Cache] QUICK HIT: IPC {ipc_section}")
                return json.loads(data)
            return None
        except Exception:
            return None
    
    def quick_lookup_bns(self, bns_section: str) -> Optional[dict]:
        """
        Instant BNS → IPC lookup from pre-loaded mapping.
        Returns: {"bns": "103(1)", "ipc": "302", "category": "Grave Offences..."}
        """
        if not self.enabled:
            return None
        try:
            key = bns_section.lower().replace(" ", "").replace("(", "").replace(")", "")
            data = self.client.get(f"quick:bns:{key}")
            if data:
                print(f"[Cache] QUICK HIT: BNS {bns_section}")
                return json.loads(data)
            return None
        except Exception:
            return None
    
    def quick_lookup_category(self, category: str) -> Optional[list]:
        """
        Get all sections in a crime category.
        Returns: [{"ipc": "379", "bns": "303(2)"}, ...]
        """
        if not self.enabled:
            return None
        try:
            # Try exact match first
            key = category.lower().replace(" ", "_")
            data = self.client.get(f"quick:category:{key}")
            if data:
                return json.loads(data)
            
            # Try partial match
            all_keys = self.client.keys("quick:category:*")
            for cat_key in all_keys:
                if category.lower() in cat_key.lower():
                    data = self.client.get(cat_key)
                    if data:
                        return json.loads(data)
            return None
        except Exception:
            return None

