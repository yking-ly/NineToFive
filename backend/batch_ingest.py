import os
import json
import requests
import base64
import time
import ingest
import core  # Import core to initialize DBs
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INFO_DIR = os.path.join(BASE_DIR, "info")
DB_FILE = os.path.join(BASE_DIR, 'uploads_db.json')
UPLOAD_URL = "https://script.google.com/macros/s/AKfycbyV_2016LPBRF4jBzxVLi0LLCYAW6Hh1ET37KeEeF-JtyDe0oh9p0JOO26-g4TlpiSCzQ/exec"

db_lock = threading.Lock()

def process_file(filename):
    file_path = os.path.join(INFO_DIR, filename)
    
    print(f"[{threading.current_thread().name}] Processing: {filename}")
    
    try:
        # 1. Upload to Google Drive
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
                encoded_content = base64.b64encode(file_content).decode('utf-8')
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return

        # Simple mimetype detection
        ext = os.path.splitext(filename)[1].lower()
        mimetype = "application/octet-stream"
        if ext == ".pdf": mimetype = "application/pdf"
        elif ext == ".txt": mimetype = "text/plain"
        elif ext == ".docx": mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        payload = {
            "file": encoded_content,
            "filename": filename,
            "mimetype": mimetype
        }
        
        # Drive upload - network bound, good for threads
        print(f"  [{filename}] Uploading to Drive...")
        response = requests.post(UPLOAD_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"  [{filename}] FAILED to upload to Drive: {response.text}")
            return
        
        res_json = response.json()
        drive_url = res_json.get('driveUrl')
        thumbnail = res_json.get('lh3Thumbnail')
        print(f"  [{filename}] Drive upload successful")
        
        # 2. Ingest to ChromaDB
        print(f"  [{filename}] Ingesting to ChromaDB...")
        chunk_ids = ingest.ingest_document(file_path, filename)
        
        if not chunk_ids:
            print(f"  [{filename}] WARNING: No chunks were ingested")
        else:
            print(f"  [{filename}] Ingested {len(chunk_ids)} chunks")
        
        # 3. Generate Summary
        print(f"  [{filename}] Generating summary...")
        summary = ingest.generate_summary(file_path)

        # 4. Update Database - Critical Section
        new_record = {
            "filename": filename,
            "driveUrl": drive_url,
            "thumbnail": thumbnail,
            "timestamp": time.time(),
            "status": "uploaded",
            "chunk_ids": chunk_ids,
            "summary": summary
        }

        with db_lock:
            db_data = []
            if os.path.exists(DB_FILE):
                try:
                    with open(DB_FILE, 'r') as f:
                        db_data = json.load(f)
                except json.JSONDecodeError:
                    db_data = []
            
            # Check if file already exists in DB, if so, remove old entry
            db_data = [d for d in db_data if d['filename'] != filename]
            
            db_data.append(new_record)
            
            with open(DB_FILE, 'w') as f:
                json.dump(db_data, f, indent=4)
                
        print(f"  ✅ [{filename}] Successfully processed and saved")

    except Exception as e:
        import traceback
        print(f"  ❌ [{filename}] ERROR: {str(e)}")
        traceback.print_exc()

def main():
    if not os.path.exists(INFO_DIR):
        print(f"Directory not found: {INFO_DIR}")
        return

    files = [f for f in os.listdir(INFO_DIR) if os.path.isfile(os.path.join(INFO_DIR, f))]
    
    if not files:
        print("No files found in info directory.")
        return

    print(f"Found {len(files)} files to process.")
    print("=" * 60)
    
    # IMPORTANT: Initialize ChromaDB shards BEFORE parallel processing
    print("Initializing ChromaDB shards...")
    try:
        dbs = core.get_dbs()
        print(f"✅ Successfully initialized {len(dbs)} database shards")
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("=" * 60)
    print("Starting parallel ingestion...")
    print("=" * 60)
    
    # Use 3 workers to match shard count
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_file, f) for f in files]
        for future in as_completed(futures):
            try:
                future.result()  # This will raise any exceptions that occurred
            except Exception as e:
                print(f"Thread execution error: {e}")
    
    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"✅ Batch ingestion complete in {elapsed:.2f} seconds")
    print("=" * 60)

if __name__ == "__main__":
    main()

