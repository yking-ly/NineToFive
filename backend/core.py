import os
import json
import threading
import hashlib
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import LlamaCpp
import chromadb
from chromadb.config import Settings

try:
    from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
except ImportError:
    from langchain.callbacks.manager import CallbackManager
    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
EMBEDDING_MODEL_PATH = os.path.join(MODEL_DIR, "nomic-embed-text-v1.5")
LLM_MODEL_PATH = os.path.join(MODEL_DIR, "Qwen2.5-7B-Instruct-Q4_K_S.gguf")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
TEMP_DIR = os.path.join(BASE_DIR, "temp_uploads")
CACHE_FILE = os.path.join(BASE_DIR, "answer_cache.json")
EMBEDDING_CACHE_FILE = os.path.join(BASE_DIR, "embedding_cache.json")

os.makedirs(TEMP_DIR, exist_ok=True)
NUM_SHARDS = 3

# Global instances
_embedding_function = None
_llm = None
_db_shards = []
_response_cache = {}
_embedding_cache = {}

# Locks
cache_lock = threading.Lock()
llm_lock = threading.Lock()
embedding_lock = threading.Lock()

def load_persistent_caches():
    global _response_cache, _embedding_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                _response_cache = json.load(f)
        except: _response_cache = {}
    
    if os.path.exists(EMBEDDING_CACHE_FILE):
        try:
            with open(EMBEDDING_CACHE_FILE, 'r') as f:
                _embedding_cache = json.load(f)
        except: _embedding_cache = {}

def save_persistent_caches():
    try:
        with cache_lock:
            # Create copies to safely iterate/dump
            cache_copy = _response_cache.copy()
            emb_cache_copy = _embedding_cache.copy()
            
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_copy, f)
        with open(EMBEDDING_CACHE_FILE, 'w') as f:
            json.dump(emb_cache_copy, f)
    except Exception as e:
        print(f"Error saving caches: {e}")

# Load caches on startup
load_persistent_caches()

class CachedEmbeddings(HuggingFaceEmbeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # 1. Check Cache
        with cache_lock:
            for i, text in enumerate(texts):
                text_hash = hashlib.md5(text.encode()).hexdigest()
                if text_hash in _embedding_cache:
                    embeddings.append(_embedding_cache[text_hash])
                else:
                    embeddings.append(None)
                    texts_to_embed.append(text)
                    indices_to_embed.append(i)
        
        # 2. Compute missing embeddings
        if texts_to_embed:
            # Lock the GPU/Model access to prevent tensor mismatches
            with embedding_lock:
                new_embeddings = super().embed_documents(texts_to_embed)
            
            # 3. Update Cache
            with cache_lock:
                for i, emb in zip(indices_to_embed, new_embeddings):
                    embeddings[i] = emb
                    text_hash = hashlib.md5(texts[i].encode()).hexdigest()
                    _embedding_cache[text_hash] = emb
            
            # Async save
            threading.Thread(target=save_persistent_caches).start()
            
        return embeddings

def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        print("Loading embedding model...")
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")
        _embedding_function = CachedEmbeddings(
            model_name=EMBEDDING_MODEL_PATH,
            model_kwargs={'device': device, 'trust_remote_code': True}
        )
    return _embedding_function

def get_llm():
    global _llm
    if _llm is None:
        print("Loading LLM...")
        _llm = LlamaCpp(
            model_path=LLM_MODEL_PATH,
            n_gpu_layers=-1, 
            n_batch=512,
            n_ctx=16384, # Increased to 16k to handle larger legal chunks + history
            max_tokens=1024, # Maximum tokens to generate for complete responses
            f16_kv=True,
            verbose=False,
            temperature=0.1,
        )
    return _llm

def safe_llm_invoke(prompt: str, **kwargs):
    """
    Thread-safe wrapper for LLM generation.
    """
    llm = get_llm()
    with llm_lock:
        return llm.invoke(prompt, **kwargs)

def safe_llm_stream(prompt: str, **kwargs):
    """
    Thread-safe wrapper for LLM streaming.
    Yields chunks while holding the lock to ensure single-stream integrity.
    """
    llm = get_llm()
    with llm_lock:
        # We must consume the stream inside the lock or yield while locked.
        # Since stream is a generator, if we just return it, the lock exits immediately.
        # we need to iterate here.
        stream = llm.stream(prompt, **kwargs)
        for chunk in stream:
            yield chunk

def get_dbs():
    global _db_shards
    if not _db_shards:
        print(f"Initializing {NUM_SHARDS} Vector DB Shards...")
        embedding_fn = get_embedding_function()
        for i in range(NUM_SHARDS):
            shard_dir = os.path.join(BASE_DIR, f"chroma_db_shard_{i}")
            os.makedirs(shard_dir, exist_ok=True)
            
            # Create explicit ChromaDB client with proper settings
            try:
                client = chromadb.PersistentClient(
                    path=shard_dir,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                # Create or get collection
                collection_name = f"shard_{i}"
                
                # Try to get existing collection, or create new one
                try:
                    collection = client.get_collection(name=collection_name)
                    print(f"  Loaded existing collection for shard {i}")
                except:
                    collection = client.create_collection(name=collection_name)
                    print(f"  Created new collection for shard {i}")
                
                # Create Chroma instance with the client
                db = Chroma(
                    client=client,
                    collection_name=collection_name,
                    embedding_function=embedding_fn
                )
                _db_shards.append(db)
                
            except Exception as e:
                print(f"Error initializing shard {i}: {e}")
                # Fallback to simple initialization
                db = Chroma(
                    persist_directory=shard_dir, 
                    embedding_function=embedding_fn
                )
                _db_shards.append(db)
                
    return _db_shards

def clear_cache():
    with cache_lock:
        _response_cache.clear()
    save_persistent_caches()

def get_cache_entry(query):
    with cache_lock:
        return _response_cache.get(query)

def update_cache(query, answer, sources):
    with cache_lock:
        _response_cache[query] = (answer, sources)
    save_persistent_caches()

def get_similar_cache_entries(query: str, threshold: float = 0.85, max_results: int = 3):
    """
    Find semantically similar cached queries using embedding similarity.
    Returns a list of dicts with 'query', 'answer', 'sources', and 'similarity' score.
    """
    if not _response_cache:
        print("Cache is empty, no similar entries to find")
        return []
    
    try:
        import numpy as np
        import traceback
        
        print(f"Searching cache for similar queries (threshold: {threshold})...")
        
        # Get embedding for the current query
        embedding_fn = get_embedding_function()
        query_embedding = embedding_fn.embed_query(query)
        
        similar_entries = []
        
        with cache_lock:
            cache_size = len(_response_cache)
            print(f"Comparing against {cache_size} cached queries")
            
            for cached_query, (cached_answer, cached_sources) in _response_cache.items():
                try:
                    # Get embedding for cached query
                    cached_embedding = embedding_fn.embed_query(cached_query)
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, cached_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(cached_embedding)
                    )
                    
                    # Only include if above threshold
                    if similarity >= threshold:
                        similar_entries.append({
                            'query': cached_query,
                            'answer': cached_answer,
                            'sources': cached_sources if cached_sources else [],
                            'similarity': float(similarity)
                        })
                        print(f"  Found similar query (similarity: {similarity:.3f}): {cached_query[:50]}...")
                except Exception as inner_e:
                    print(f"Error processing cached query: {inner_e}")
                    continue
        
        # Sort by similarity (highest first)
        similar_entries.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top N results
        result = similar_entries[:max_results]
        print(f"Returning {len(result)} similar cache entries")
        return result
        
    except Exception as e:
        import traceback
        print(f"Error finding similar cache entries: {e}")
        traceback.print_exc()
        return []


