# Fix for Windows: Disable colorama before any Flask imports to prevent OSError 6
import os
import sys
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['TERM'] = 'dumb'
    # Disable colorama's auto-initialization
    os.environ['COLORAMA_AUTORESET'] = '0'
    os.environ['COLORAMA_STRIP'] = '1'

from flask import Flask, jsonify, request
from flask_cors import CORS
from deep_translator import GoogleTranslator
import time
import json
import requests
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "expose_headers": ["X-Sources"]}})

DB_FILE = 'uploads_db.json'
UPLOAD_URL = "https://script.google.com/macros/s/AKfycbyV_2016LPBRF4jBzxVLi0LLCYAW6Hh1ET37KeEeF-JtyDe0oh9p0JOO26-g4TlpiSCzQ/exec"

@app.route('/')
def hello_world():
    return jsonify({"message": "Hello from Flask Backend!"})

@app.route('/api/data')
def get_data():
    # Read README.md from the parent directory
    try:
        readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        readme_content = f"Error reading README.md: {str(e)}"

    data = {
        "status": "success",
        "timestamp": time.time(),
        "readme": readme_content
    }
    return jsonify(data)

@app.route('/api/guide')
def get_guide():
    lang = request.args.get('lang', 'en')
    
    try:
        # Read HOW_TO_USE.md from the backend directory (current directory)
        guide_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'HOW_TO_USE.md')
        with open(guide_path, 'r', encoding='utf-8') as f:
            guide_content = f.read()
            
        if lang != 'en':
            # Translate content
            translator = GoogleTranslator(source='auto', target=lang)
            # We translate paragraph by paragraph to avoid length limits better (though deep-translator handles limits well usually)
            # Simple approach: Translate the whole thing if it's not too huge.
            # For markdown, let's just translate the whole blob.
            guide_content = translator.translate(guide_content)
            
    except Exception as e:
        guide_content = f"Error processing guide: {str(e)}"
    
    return jsonify({"content": guide_content})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            # Save to temp file for ingestion and processing
            # Ensure ingest module is imported
            import ingest
            import core
            temp_path = os.path.join(core.TEMP_DIR, file.filename)
            file.save(temp_path)

            # Read content for Drive Upload from the saved file
            with open(temp_path, "rb") as f:
                file_content = f.read()
                encoded_content = base64.b64encode(file_content).decode('utf-8')
            
            payload = {
                "file": encoded_content,
                "filename": file.filename,
                "mimetype": file.mimetype or "application/octet-stream"
            }
            
            # Send to external service (Google Apps Script)
            response = requests.post(UPLOAD_URL, json=payload)
            
            if response.status_code == 200:
                res_json = response.json()
                
                # Ingest to ChromaDB
                print(f"Ingesting {file.filename}...")
                chunk_ids = ingest.ingest_document(temp_path, file.filename)
                
                # Prepare record for local DB
                new_record = {
                    "filename": file.filename,
                    "driveUrl": res_json.get('driveUrl'),
                    "thumbnail": res_json.get('lh3Thumbnail'),
                    "lh3Thumbnail": res_json.get('lh3Thumbnail'),
                    "timestamp": time.time(),
                    "status": "uploaded",
                    "chunk_ids": chunk_ids,
                    "summary": "Document successfully ingested and indexed. Ready for chat."
                }

                # Save to local JSON DB
                db_data = []
                if os.path.exists(DB_FILE):
                    try:
                        with open(DB_FILE, 'r') as f:
                            db_data = json.load(f)
                    except json.JSONDecodeError:
                        db_data = []
                
                db_data.append(new_record)
                
                with open(DB_FILE, 'w') as f:
                    json.dump(db_data, f, indent=4)
                
                # Optional: Clean up temp file
                # os.remove(temp_path)
                
                return jsonify({"status": "success", "data": new_record})
            else:
                return jsonify({"error": "Failed to upload to external service", "details": response.text}), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('message')
    history = data.get('history', [])
    language = data.get('language', 'en')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
        
    try:
        # Import ingest here to ensure it uses the same cached models if running in same process
        # (Though Flask dev server reloader might mess with globals, but for production/testing this is fine)
        import retrieval
        from flask import Response, stream_with_context
        
        answer_stream, source_filenames = retrieval.query_docs(query, chat_history=history, language=language)
        
        # Map filenames to details from DB
        sources = []
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    db_data = json.load(f)
                    
                for filename in source_filenames:
                    # Find matching record
                    record = next((item for item in db_data if item["filename"] == filename), None)
                    if record:
                        sources.append({
                            "filename": filename,
                            "driveUrl": record.get("driveUrl"),
                            "thumbnail": record.get("thumbnail")
                        })
                    else:
                        sources.append({"filename": filename})
            except Exception as e:
                print(f"Error reading DB mapping: {e}")
                sources = [{"filename": f} for f in source_filenames]
        
        def generate():
            for chunk in answer_stream:
                yield chunk

        # Return streaming response with sources in header
        response = Response(stream_with_context(generate()), mimetype='text/plain')
        response.headers['X-Sources'] = json.dumps(sources)
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# WebSocket Handler
from flask_socketio import SocketIO, emit
import retrieval

# Use threading mode to avoid compatibility issues with PyTorch/Gevent
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@socketio.on('send_message')
def handle_message(data):
    """
    Handles real-time chat messages via WebSocket.
    """
    query = data.get('message')
    history = data.get('history', [])
    language = data.get('language', 'en')
    tag = data.get('tag', None)  # Get the selected category tag
    
    if not query:
        emit('error', {'error': 'No query provided'})
        return

    try:
        # Get stream and sources from retrieval module
        answer_stream, source_filenames = retrieval.query_docs(
            query, 
            chat_history=history, 
            language=language,
            category_tag=tag  # Pass the tag to retrieval
        )
        
        # Map filenames to details from DB
        sources = []
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    db_data = json.load(f)
                
                for filename in source_filenames:
                    record = next((item for item in db_data if item["filename"] == filename), None)
                    if record:
                        sources.append({
                            "filename": filename,
                            "driveUrl": record.get("driveUrl"),
                            "thumbnail": record.get("thumbnail")
                        })
                    else:
                        sources.append({"filename": filename})
            except Exception as e:
                print(f"Error reading DB mapping: {e}")
                sources = [{"filename": f} for f in source_filenames]
        else:
             sources = [{"filename": f} for f in source_filenames]

        # Emit sources first
        emit('sources', sources)
        
        # Stream the answer chunks
        full_response = ""
        for chunk in answer_stream:
            full_response += chunk
            emit('response_chunk', chunk)
            
            # Yield control to allow other threads to run
            socketio.sleep(0) 

        emit('response_complete')
        
    except Exception as e:
        emit('error', {'error': str(e)})

if __name__ == '__main__':
    # Preload models to ensure fast first response
    print("--- PRELOADING MODELS ---")
    try:
        import core
        print("Loading Embedding Model...")
        core.get_embedding_function()
        print("Loading LLM...")
        core.get_llm()
        print("Models loaded successfully.")
    except Exception as e:
        print(f"Error preloading models: {e}")
    
    # Use socketio.run instead of app.run
    print("Starting Server with SocketIO...")
    socketio.run(app, debug=True, port=5000)
