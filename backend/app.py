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

# Track active generation requests for interruption
active_requests = {}

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

@app.route('/api/translations/<lang>')
def get_translations(lang):
    try:
        # Load the translations file
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'translations.json')
        # Check if file exists
        if not os.path.exists(data_path):
             return jsonify({"error": "Translations file not found"}), 404

        with open(data_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        target_lang = lang
        # Map romanized to English UI strings for now, or handle specifically if added
        if lang == 'hi-romanized':
             target_lang = 'en' 
        
        # Return the specific language dictionary, default to English if not found
        result = translations.get(target_lang, translations.get('en'))
        
        # Add artificial delay to show off skeleton loading if requested? 
        # User asked for "skeleton type loading style", implying it should be visible.
        # I'll add a tiny delay (e.g. 500ms) to ensure the visual effect is perceptible.
        time.sleep(0.5)
        
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
# Force 'polling' to prevent WebSocket upgrade crashes on Windows/Werkzeug
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', transports=['polling'])

@socketio.on('stop_generation')
def handle_stop(data=None):
    """
    Stops the current generation for the requesting user.
    """
    if request.sid in active_requests:
        active_requests[request.sid] = False
        print(f"🛑 Generation stopped for session {request.sid}")

@socketio.on('send_message')
def handle_message(data):
    """
    Handles real-time chat messages via WebSocket.
    """
    query = data.get('message')
    history = data.get('history', [])
    language = data.get('language', 'en')
    tag = data.get('tag', None)
    persona = data.get('persona', 'default') # Support for Kira
    
    # Mark this session as active
    active_requests[request.sid] = True
    
    if not query:
        emit('error', {'error': 'No query provided'})
        return

    try:
        # Get stream and sources from retrieval module
        answer_stream, source_filenames = retrieval.query_docs(
            query, 
            chat_history=history, 
            language=language,
            category_tag=tag,
            persona=persona
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
        
        # Helper function to strip markdown (for Kira plaintext responses)
        def strip_markdown(text):
            """Aggressively remove ALL markdown syntax for pure plaintext TTS output"""
            import re
            # Remove code blocks
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            # Remove bold (multiple passes for nested)
            for _ in range(3):
                text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
                text = re.sub(r'__(.+?)__', r'\1', text)
            # Remove italic
            for _ in range(3):
                text = re.sub(r'\*(.+?)\*', r'\1', text)
                text = re.sub(r'_(.+?)_', r'\1', text)
            # Remove headers
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
            # Remove inline code
            text = re.sub(r'`(.+?)`', r'\1', text)
            # Remove list markers
            text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
            # Remove links [text](url)
            text = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', text)
            # Clean up spaces BUT preserve newlines for natural TTS pauses
            # Collapse only horizontal whitespace (spaces, tabs)
            text = re.sub(r'[ \t]+', ' ', text)
            return text
    
        import re

        # Stream the answer chunks
        full_response = ""
        buffer = ""
        for chunk in answer_stream:
            # Check for interruption signal
            if not active_requests.get(request.sid, True):
                print(f"⚠️ Generation interrupted by user {request.sid}")
                break
            
            full_response += chunk
            
            if persona == 'kira':
                buffer += chunk
                # Split by sentence delimiters (English and Hindi danda)
                parts = re.split(r'([.!?\n।]+)', buffer)
                if len(parts) > 1:
                    for i in range(0, len(parts) - 1, 2):
                        sentence = parts[i] + parts[i+1]
                        emit('response_chunk', strip_markdown(sentence))
                    buffer = parts[-1]
            else:
                emit('response_chunk', chunk)
            
            # Yield control to allow other threads to run
            socketio.sleep(0) 

        if persona == 'kira' and buffer:
            emit('response_chunk', strip_markdown(buffer))

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
    # allow_unsafe_werkzeug=True fixes "write() before start_response" in some envs
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
