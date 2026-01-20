from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from deep_translator import GoogleTranslator
import time
import os
import json
import requests
import base64
import sys
from pathlib import Path

# Initialize FastAPI
app = FastAPI(title="NineToFive API", version="1.0.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
DB_FILE = 'uploads_db.json'
UPLOAD_URL = "https://script.google.com/macros/s/AKfycbyV_2016LPBRF4jBzxVLi0LLCYAW6Hh1ET37KeEeF-JtyDe0oh9p0JOO26-g4TlpiSCzQ/exec"

# ------------------------------------------------------------------
# RAG Service Initialization
# ------------------------------------------------------------------
rag_service = None

try:
    # Ensure backend/ is in path to import rag_service.py if it's in the same folder
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from rag_service import RAGService
    rag_service = RAGService()
    print("[FastAPI] RAG Service connected successfully.")
except Exception as e:
    print(f"[FastAPI Warning] Could not load RAG Service: {e}")

# ------------------------------------------------------------------
# Data Models
# ------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str
    collections: Optional[List[str]] = None  # e.g., ["ipc"], ["bns"], ["mapping"], or ["ipc", "bns"]
    language: Optional[str] = "en"  # "en", "hi", or "all"

# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/data")
def get_data():
    """Returns content of README.md"""
    readme_content = ""
    try:
        readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'README.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
        else:
            readme_content = "README.md not found in parent directory."
    except Exception as e:
        readme_content = f"Error reading README.md: {str(e)}"

    return {
        "status": "success",
        "timestamp": time.time(),
        "readme": readme_content
    }

@app.get("/api/guide")
def get_guide(lang: str = Query("en")):
    """Returns HOW_TO_USE.md content, optionally translated"""
    try:
        guide_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'HOW_TO_USE.md')
        if os.path.exists(guide_path):
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_content = f.read()
        else:
            return {"content": "HOW_TO_USE.md not found."}

        if lang != 'en':
            translator = GoogleTranslator(source='auto', target=lang)
            guide_content = translator.translate(guide_content)
            
        return {"content": guide_content}
            
    except Exception as e:
        return {"content": f"Error processing guide: {str(e)}"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file sent")

    try:
        # Read file content
        file_content = await file.read()
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        payload = {
            "file": encoded_content,
            "filename": file.filename,
            "mimetype": file.content_type or "application/octet-stream"
        }
        
        # Requests is sync, but strictly it blocks the event loop.
        # For high perf, use httpx. For now, this logic is preserved from Flask.
        response = requests.post(UPLOAD_URL, json=payload)
        
        if response.status_code == 200:
            res_json = response.json()
            
            new_record = {
                "filename": file.filename,
                "driveUrl": res_json.get('driveUrl'),
                "thumbnail": res_json.get('lh3Thumbnail'),
                "timestamp": time.time(),
                "status": "uploaded",
                "summary": "AI Summary Placeholder: This legal document contains clauses..."
            }
            
            # Simple JSON DB (Not async safe for high load, but fine for prototype)
            db_data = []
            if os.path.exists(DB_FILE):
                try:
                    with open(DB_FILE, 'r') as f:
                        db_data = json.load(f)
                except:
                    pass
            
            db_data.append(new_record)
            
            with open(DB_FILE, 'w') as f:
                json.dump(db_data, f, indent=4)
                
            return {"status": "success", "data": new_record}
        else:
            raise HTTPException(status_code=500, detail=f"External upload failed: {response.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    RAG Chat Endpoint with full response caching.
    Defined as synchronous `def` so FastAPI runs it in a threadpool, 
    preventing the sync ChromaDB client from blocking the main loop.
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG Service not initialized")
        
    start_time = time.time()
    
    # Generate cache key from query + collections + language
    cache_key = f"answer:{request.query}:{sorted(request.collections) if request.collections else 'all'}:{request.language}"
    
    # Check if full answer is cached
    if rag_service.cache.enabled:
        cached_answer = rag_service.cache.client.get(cache_key)
        if cached_answer:
            print(f"[Cache] FULL ANSWER HIT for: {request.query[:30]}...")
            cached_data = json.loads(cached_answer)
            duration = time.time() - start_time
            return {
                "status": "success",
                "query": request.query,
                "answer": cached_data["answer"],
                "context": cached_data["context"],
                "duration_seconds": round(duration, 3),
                "cached": True
            }
    
    # 1. Retrieve (with optional collection and language filtering)
    context = rag_service.query_statutes(request.query, collections=request.collections, language=request.language)
    
    # 2. Answer
    answer = rag_service.generate_answer(request.query, context)
    
    duration = time.time() - start_time
    
    # Cache the full response (answer + context) for 1 hour
    if rag_service.cache.enabled:
        try:
            cache_data = json.dumps({"answer": answer, "context": context})
            rag_service.cache.client.setex(cache_key, 3600, cache_data)
        except Exception as e:
            print(f"[Cache Warning] Failed to cache answer: {e}")
    
    return {
        "status": "success",
        "query": request.query,
        "answer": answer,
        "context": context,
        "duration_seconds": round(duration, 3),
        "cached": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
