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
    
    print(f"\n{'='*70}")
    print(f"[{threading.current_thread().name}] Processing: {filename}")
    print(f"{'='*70}")
    
    try:
        # 1. Upload to Google Drive
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
                encoded_content = base64.b64encode(file_content).decode('utf-8')
        except Exception as e:
            print(f"❌ Error reading file {filename}: {e}")
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
        print(f"📤 [{filename}] Uploading to Drive...")
        response = requests.post(UPLOAD_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ [{filename}] FAILED to upload to Drive: {response.text}")
            return
        
        res_json = response.json()
        drive_url = res_json.get('driveUrl')
        thumbnail = res_json.get('lh3Thumbnail')
        print(f"✅ [{filename}] Drive upload successful")
        
        # 2. USE MASTER INGESTION PIPELINE
        print(f"🚀 [{filename}] Starting Master Ingestion...")
        print(f"-" * 70)
        
        def status_callback(msg):
            print(f"   [{filename}] {msg}")
        
        # Call the smart ingestion
        result = ingest.smart_ingest_document(
            file_path=file_path,
            original_filename=filename,
            status_callback=status_callback
        )
        
        print(f"-" * 70)
        
        if not result.get('success'):
            print(f"❌ [{filename}] Ingestion FAILED: {result.get('message', 'Unknown error')}")
            return
        
        # Display results
        doc_type = result.get('doc_type', 'Unknown')
        chunks_created = result.get('chunks_created', 0)
        processing_method = result.get('processing_method', 'Unknown')
        
        print(f"✅ [{filename}] Ingestion successful!")
        print(f"   📌 Type: {doc_type}")
        print(f"   📦 Chunks: {chunks_created}")
        print(f"   ⚙️  Method: {processing_method}")
        
        # Show zones if judgment
        if doc_type == 'JUDGMENT' and 'zones' in result:
            print(f"   ⚖️  Zones: {', '.join(result['zones'])}")

        # 3. Update Database - Critical Section
        # Note: Master ingestion already updates uploads_db.json with structured data
        # But we also need to add Drive URL and thumbnail
        
        with db_lock:
            # Load the JSON DB updated by master ingestion
            if os.path.exists(DB_FILE):
                try:
                    with open(DB_FILE, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        db = json.loads(content) if content else {"documents": {}}
                except json.JSONDecodeError:
                    db = {"documents": {}}
            else:
                db = {"documents": {}}
            
            # Find the document by file_id
            file_id = result.get('file_id')
            
            if file_id and file_id in db.get('documents', {}):
                # Update existing entry with Drive metadata
                db['documents'][file_id]['driveUrl'] = drive_url
                db['documents'][file_id]['thumbnail'] = thumbnail
                db['documents'][file_id]['lh3Thumbnail'] = thumbnail
                db['documents'][file_id]['status'] = 'uploaded'
                
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(db, f, indent=2, ensure_ascii=False)
                
                print(f"✅ [{filename}] Database updated with Drive metadata")
            else:
                print(f"⚠️  [{filename}] Could not find file_id in database to update Drive URL")
                
        print(f"✅✅ [{filename}] Successfully processed and saved")
        print(f"{'='*70}\n")

    except Exception as e:
        import traceback
        print(f"❌❌ [{filename}] ERROR: {str(e)}")
        traceback.print_exc()
        print(f"{'='*70}\n")


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

