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

@app.route('/api/uploads')
def get_uploads():
    if not os.path.exists(DB_FILE):
        return jsonify([])
    try:
        with open(DB_FILE, 'r') as f:
            content = f.read()
            if not content.strip():
                return jsonify([])
            data = json.loads(content)
        # Sort by timestamp descending if available, else usage
        # Assuming simple list for now
        return jsonify(data)
    except json.JSONDecodeError:
        print("[WARNING] DB_FILE corrupted or empty, returning empty list")
        return jsonify([])
    except Exception as e:
        print(f"[ERROR] Failed to read uploads db: {e}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/api/kyc')
def get_kyc_content():
    """Know Your Constitution - Educational content about Indian Constitution"""
    try:
        lang = request.args.get('lang', 'en')
        article = request.args.get('article', None)
        
        # Constitution articles database
        constitution_data = {
            "fundamental_rights": [
                {
                    "id": "art14",
                    "article": "Article 14",
                    "title": "Equality before law" if lang == 'en' else "कानून के समक्ष समानता",
                    "description": "The State shall not deny to any person equality before the law or the equal protection of the laws within the territory of India.",
                    "category": "Right to Equality",
                    "simplified": "Everyone is equal before the law. No one can be discriminated against."
                },
                {
                    "id": "art19",
                    "article": "Article 19",
                    "title": "Freedom of speech and expression" if lang == 'en' else "अभिव्यक्ति की स्वतंत्रता",
                    "description": "All citizens shall have the right to freedom of speech and expression.",
                    "category": "Right to Freedom",
                    "simplified": "You have the right to express your opinions freely."
                },
                {
                    "id": "art21",
                    "article": "Article 21",
                    "title": "Right to life and personal liberty" if lang == 'en' else "जीवन और व्यक्तिगत स्वतंत्रता का अधिकार",
                    "description": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
                    "category": "Right to Life",
                    "simplified": "Your life and freedom are protected by law."
                },
                {
                    "id": "art32",
                    "article": "Article 32",
                    "title": "Right to Constitutional Remedies" if lang == 'en' else "संवैधानिक उपचारों का अधिकार",
                    "description": "The right to move the Supreme Court for the enforcement of fundamental rights.",
                    "category": "Right to Constitutional Remedies",
                    "simplified": "You can approach courts if your rights are violated."
                }
            ],
            "directive_principles": [
                {
                    "id": "art39",
                    "article": "Article 39",
                    "title": "Equal justice and free legal aid" if lang == 'en' else "समान न्याय और निःशुल्क कानूनी सहायता",
                    "description": "The State shall secure equal justice and free legal aid.",
                    "category": "Directive Principles",
                    "simplified": "Everyone deserves fair justice, regardless of economic status."
                }
            ],
            "overview": {
                "total_articles": 395,
                "parts": 22,
                "schedules": 12,
                "adoption_date": "26th January 1950"
            }
        }
        
        if article:
            # Search for specific article
            for category in constitution_data.values():
                if isinstance(category, list):
                    for item in category:
                        if item.get('id') == article:
                            return jsonify(item)
            return jsonify({"error": "Article not found"}), 404
        
        return jsonify(constitution_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kyl')
def get_kyl_content():
    """Know Your Law - Educational content about Indian legal provisions"""
    try:
        lang = request.args.get('lang', 'en')
        category = request.args.get('category', 'all')
        
        # Legal provisions database
        legal_data = {
            "criminal_law": [
                {
                    "id": "bns304",
                    "section": "BNS 304",
                    "title": "Murder" if lang == 'en' else "हत्या",
                    "description": "Punishment for murder: Life imprisonment or death penalty",
                    "example": "Intentional killing with premeditation",
                    "severity": "Cognizable, Non-bailable",
                    "simplified": "Taking someone's life intentionally is the gravest crime."
                },
                {
                    "id": "bns103",
                    "section": "BNS 103",
                    "title": "Snatching" if lang == 'en' else "छीनाझपटी",
                    "description": "Theft with sudden force from a person",
                    "example": "Grabbing a mobile phone or chain from someone",
                    "severity": "Cognizable, Bailable",
                    "simplified": "Forcefully taking someone's belongings is a crime."
                }
            ],
            "civil_rights": [
                {
                    "id": "consumer",
                    "title": "Consumer Rights" if lang == 'en' else "उपभोक्ता अधिकार",
                    "rights": [
                        "Right to Safety",
                        "Right to Information",
                        "Right to Choose",
                        "Right to be Heard",
                        "Right to Redressal"
                    ],
                    "simplified": "As a consumer, you have protection against unfair practices."
                },
                {
                    "id": "labor",
                    "title": "Labor Rights" if lang == 'en' else "श्रमिक अधिकार",
                    "rights": [
                        "Minimum Wage",
                        "Safe Working Conditions",
                        "Right to Form Unions",
                        "Protection from Exploitation"
                    ],
                    "simplified": "Workers have legal protection and guaranteed rights."
                }
            ],
            "everyday_law": [
                {
                    "topic": "Traffic Rules",
                    "key_points": [
                        "Helmet mandatory for two-wheelers",
                        "Seatbelt mandatory in cars",
                        "No mobile phone while driving",
                        "Valid license and documents required"
                    ]
                },
                {
                    "topic": "Tenant Rights",
                    "key_points": [
                        "Cannot be evicted without notice",
                        "Rent agreement should be in writing",
                        "Landlord must maintain property",
                        "Security deposit should be returned"
                    ]
                }
            ]
        }
        
        if category != 'all':
            return jsonify(legal_data.get(category, {}))
        
        return jsonify(legal_data)
        
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
                
                # Prepare record for local DB (without summary initially)
                # Note: Ingestion is deferred to the WebSocket handler (handle_generate_summary) 
                # to include the generated summary in the chunk metadata/content.
                chunk_ids = []
                new_record = {
                    "filename": file.filename,
                    "driveUrl": res_json.get('driveUrl'),
                    "thumbnail": res_json.get('lh3Thumbnail'),
                    "lh3Thumbnail": res_json.get('lh3Thumbnail'),
                    "timestamp": time.time(),
                    "status": "processing",  # Mark as processing
                    "chunk_ids": chunk_ids,
                    "summary": ""  # Empty, will be filled by streaming endpoint
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
                
                # Return immediately - summary will be generated via WebSocket
                return jsonify({"status": "success", "data": new_record, "temp_path": temp_path})
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
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', transports=['polling'], ping_timeout=60, ping_interval=25)

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
        # Custom Status Callback
        def status_update(msg):
             emit('search_status', {'message': msg})
             socketio.sleep(0) # Yield for smoothness

        if persona == 'kira':
            # --- FAST KIRA LOGIC ---
            try:
                import kira_processor
                import core
                
                # 1. IMMEDIATE ACKNOWLEDGMENT (The "Mouth")
                # Generate opener based on raw query
                opener = kira_processor.generate_opener(query)
                if opener:
                    print(f"🗣️ Kira Opener: {opener}")
                    # Emit opener immediately for TTS
                    # Use existing loop logic downstream to clean it, OR clean it here?
                    # The downstream loop handles 'response_chunk' cleaning.
                    # We just need to make sure it doesn't get mixed up.
                    # We'll emit it here, and the client will queue it.
                    emit('response_chunk', kira_processor.clean_for_tts(opener) + " ")
                    socketio.sleep(0) 
                
                # 2. HEAVY LIFTING (The "Brain") - Retrieval
                # Rewrite query
                effective_query = kira_processor.build_kira_context(history, query)
                
                # Retrieve (using shared pipeline)
                # status_update("🧠 Recalling legal provisions...") 
                results = retrieval.retrieve_context(
                    effective_query, 
                    n_results=3, 
                    persona='kira', 
                    status_callback=status_update
                )
                
                # 3. FACT GENERATION
                # Prepare Context
                context_texts = [doc.page_content for doc, _ in results] if results else []
                context = "\n\n---\n\n".join(context_texts)
                source_filenames = [doc.metadata['filename'] for doc, _ in results if 'filename' in doc.metadata]
                
                # Prepare System Prompt (Keep strictly aligned with retrieval.py)
                system_instruction = """You are Kira, a senior legal consultant on a live phone call. 
Your goal is to guide the user through their legal issue conversationally.

CRITICAL VOICE CONSTRAINTS:
1. NO MARKDOWN: Do not use **, ##, -, or list formats.
2. SHORT SENTENCES: Keep sentences under 15 words where possible. Long sentences confuse TTS.
3. CONVERSATIONAL FILLERS: Use phrases like "Let's see," "That's a good point," or "Bear with me."
4. ASK ONE THING: Never ask two questions in a row.
5. NO legal jargon without immediate explanation.

STRICT BEHAVIOR:
- If the retrieved text is insufficient, say: "I'm checking the files, but I don't see that specific detail here. Could you clarify...?"
- Do not cite Section numbers like a robot. Instead of "According to Section 103...", say "Under Section 103, the law states..."
- Use the context provided to answer accurately.
"""
                prompt = f"<|im_start|>system\n{system_instruction}\nContext:\n{context}<|im_end|>\n"
                
                # Add History
                for msg in history[-6:]: # Keep it tight for speed
                     role = msg.get('role', 'user')
                     content = msg.get('content', '')
                     if role == 'user': prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
                     else: prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
                
                prompt += f"<|im_start|>user\n{effective_query}<|im_end|>\n<|im_start|>assistant\n"
                
                # Stream Answer
                print("Generate Kira Answer...")
                answer_stream = core.safe_llm_stream(prompt, stop=["<|im_end|>"])
                
            except Exception as e:
                print(f"Kira Fast Track Failed: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to standard
                answer_stream, source_filenames = retrieval.query_docs(query, chat_history=history, persona=persona, status_callback=status_update)

        else:
            # --- STANDARD LOGIC ---
            # Get stream and sources from retrieval module
            answer_stream, source_filenames = retrieval.query_docs(
                query, 
                chat_history=history, 
                language=language,
                category_tag=tag,
                persona=persona,
                status_callback=status_update 
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
        try:
            import kira_processor
        except ImportError:
            kira_processor = None

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
                        # Use optimized TTS cleaner
                        clean_text = kira_processor.clean_for_tts(sentence) if kira_processor else strip_markdown(sentence)
                        emit('response_chunk', clean_text)
                    buffer = parts[-1]
            else:
                emit('response_chunk', chunk)
            
            # Yield control to allow other threads to run
            socketio.sleep(0) 

        if persona == 'kira' and buffer:
            clean_text = kira_processor.clean_for_tts(buffer) if kira_processor else strip_markdown(buffer)
            emit('response_chunk', clean_text)

        emit('response_complete')
        
        # Save chat history to Firestore if session info is provided
        session_id = data.get('sessionId')
        user_id = data.get('userId')
        
        if session_id and user_id and user_id != 'guest':
            try:
                import firebase_config
                # Only save Assistant Response (User message saved by frontend for immediate UI)
                firebase_config.save_chat_message(
                    session_id=session_id,
                    user_id=user_id,
                    role='assistant',
                    content=full_response,
                    sources=[s.get('filename') for s in sources] if sources else [],
                    language=language
                )
                print(f"✅ Saved assistant response to Firebase session {session_id}")
            except Exception as e:
                print(f"❌ Error saving chat to Firebase: {e}")

    
    except Exception as e:
        emit('error', {'error': str(e)})

@socketio.on('generate_summary')
def handle_generate_summary(data):
    """
    Streams AI summary generation for uploaded documents
    Supports Hindi translation and structured format
    Includes cross-document referencing for comprehensive legal context
    """
    import ingest
    import document_processor
    from deep_translator import GoogleTranslator
    import re
    
    filename = data.get('filename')
    temp_path = data.get('temp_path')
    language = data.get('language', 'en')  # 'en' or 'hi'
    
    if not filename or not temp_path:
        emit('summary_error', {'error': 'Missing filename or path'})
        return
    
    try:
        # Extract text first
        emit('search_status', {'message': f"📄 Extracting text from {filename}..."})
        print(f"📄 Extracting text from {filename}...")
        text, extraction_method = document_processor.extract_text_smart(temp_path)
        
        if not text:
            emit('summary_error', {'error': f'Text extraction failed: {extraction_method}'})
            return
        
        # Emit extraction method info
        emit('extraction_method', {'method': extraction_method})
        
        # STEP 1: Extract legal entities from the document for cross-referencing
        emit('search_status', {'message': "🔍 Identifying legal entities..."})
        print(f"🔍 Extracting legal entities for cross-referencing...")
        legal_entities = []
        
        # Extract sections, articles, chapters
        sections = re.findall(r'(?:section|sec\.|§)\s*(\d+[A-Z]?(?:\(\d+\))?)', text, re.IGNORECASE)
        articles = re.findall(r'(?:article|art\.)\s*(\d+[A-Z]?)', text, re.IGNORECASE)
        
        # Extract act names (IPC, BNS, CrPC, etc.)
        acts = re.findall(r'\b((?:Indian Penal Code|IPC|Bharatiya Nyaya Sanhita|BNS|Criminal Procedure Code|CrPC|Bharatiya Nagarik Suraksha Sanhita|BNSS|Indian Evidence Act|IEA|Bharatiya Sakshya Adhiniyam|BSA|IT Act))\b', text, re.IGNORECASE)
        
        # Extract crime types and charges
        crime_types = re.findall(r'\b(murder|rape|theft|robbery|assault|cheating|fraud|forgery|kidnapping|abduction|extortion|criminal breach of trust|dowry death|sexual harassment|culpable homicide|attempt to murder|voluntarily causing hurt|grievous hurt|defamation|bribery|corruption|money laundering|terrorism|sedition|criminal conspiracy|rioting|unlawful assembly)\b', text, re.IGNORECASE)
        
        # Extract legal concepts and procedures
        legal_concepts = re.findall(r'\b(bail|anticipatory bail|acquittal|conviction|appeal|revision|writ petition|habeas corpus|mandamus|certiorari|quo warranto|prohibition|injunction|stay order|interim order|life imprisonment|death sentence|rigorous imprisonment|fine|compensation|damages|sentence|punishment|penalty|probation|parole|remission|commutation)\b', text, re.IGNORECASE)
        
        # Extract legal terms specific to evidence and trial
        procedural_terms = re.findall(r'\b(evidence|witness|testimony|cross-examination|examination-in-chief|prosecution|defense|accused|complainant|victim|appellant|respondent|petitioner|defendant|plaintiff|judgment|decree|order|direction|charge|framing of charges|trial|hearing|investigation|FIR|charge sheet|cognizance|summons|warrant|arrest)\b', text, re.IGNORECASE)
        
        # PRIORITIZED entity lists - specific terms first
        # Tier 1: Most specific and most likely to find good matches
        tier1_entities = []
        tier1_entities.extend([f"Section {s}" for s in set(sections[:10])])
        tier1_entities.extend([f"Article {a}" for a in set(articles[:5])])
        tier1_entities.extend(list(set(acts[:5])))
        
        # Tier 2: Crime types (specific but may vary in terminology)
        tier2_entities = list(set([c.lower() for c in crime_types]))[:8]
        
        # Tier 3: Legal concepts (moderately specific)
        tier3_entities = list(set([c.lower() for c in legal_concepts]))[:5]
        
        # Tier 4: Procedural terms (very generic, use sparingly)
        tier4_entities = list(set([p.lower() for p in procedural_terms]))[:3]
        
        # Combine with priority
        legal_entities = tier1_entities + tier2_entities + tier3_entities + tier4_entities
        
        print(f"Found {len(legal_entities)} legal entities:")
        print(f"  - Tier 1 (Sections/Acts): {tier1_entities[:5]}")
        print(f"  - Tier 2 (Crime types): {tier2_entities[:5]}")
        print(f"  - Tier 3 (Legal concepts): {tier3_entities[:3]}")
        
        # STEP 2: Cross-reference with other documents using ADVANCED RETRIEVAL
        referenced_docs = set([filename]) # Always include current
        context_from_other_docs = []
        
        if legal_entities:
            import retrieval
            
            # Prioritize entities: Tier 1 (Section/Acts) + Top Tier 2 (Crimes)
            # Limit to top 5 to avoid excessive processing time (5 * ~2-4 seconds = ~15s)
            priority_entities = legal_entities[:5]
            
            print(f"🔍 Starting Deep Cross-Reference Search for {len(priority_entities)} priority entities...")
            emit('search_status', {'message': f"📚 Starting deep search for {len(priority_entities)} key legal points..."})
            
            for idx, entity in enumerate(priority_entities, 1):
                # Custom status callback for this entity search
                def entity_status(msg):
                    # We only emit interesting statuses to avoid spam
                    if "Reranking" in msg or "Deepening" in msg or "Adaptive" in msg:
                        short_entity = entity[:20] + "..." if len(entity) > 20 else entity
                        emit('search_status', {'message': f"[{short_entity}] {msg}"})
                        socketio.sleep(0) # Yield

                emit('search_status', {'message': f"📚 Analyzing references for '{entity}' ({idx}/{len(priority_entities)})..."})
                
                # USE THE POWERFUL SHARED PIPELINE
                # We ask for n_results=10 initially, standard complexity analysis
                # This automatically handles: Translation, Index Priority, Deepening, Reranking
                try:
                    results = retrieval.retrieve_context(
                        query_text=entity,
                        n_results=10, 
                        language=language,
                        status_callback=entity_status,
                        persona='default' # Use default (strict) mode
                    )
                    
                    # Process results
                    for doc, score in results:
                         if 'filename' in doc.metadata:
                            source_file = doc.metadata['filename']
                            if source_file != filename: # Exclude self
                                referenced_docs.add(source_file)
                                
                                # Add to context list
                                context_from_other_docs.append({
                                    'entity': entity,
                                    'source': source_file,
                                    'content': doc.page_content, 
                                    'score': score # 0.0 to 1.0 (higher is better from reranker)
                                })
                except Exception as e:
                     print(f"Error searching for entity '{entity}': {e}")

        print(f"\n📚 Cross-referencing complete: Found {len(referenced_docs)} total documents")
        print(f"   Documents: {sorted(list(referenced_docs))}")
        print(f"   Context snippets collected: {len(context_from_other_docs)}")
        
        # STEP 3: Generate enhanced summary with cross-references
        emit('search_status', {'message': "🤖 Generating comprehensive summary..."})
        print(f"🤖 Generating comprehensive summary for {filename}...")
        context = text[:4000] if len(text) > 4000 else text
        
        # Add context from other documents if available
        additional_context = ""
        if context_from_other_docs:
            # Sort by relevance score (HIGHER is better for FlashRank) and take top 10
            sorted_contexts = sorted(context_from_other_docs, key=lambda x: x.get('score', 0), reverse=True)[:10]
            
            additional_context = "\n\n=== RELEVANT CONTEXT FROM OTHER LEGAL DOCUMENTS ===\n"
            additional_context += f"(Found {len(context_from_other_docs)} related references across {len(referenced_docs)-1} documents)\n\n"
            
            for ctx in sorted_contexts:
                additional_context += f"📄 {ctx['entity']} (from {ctx['source']}):\n"
                additional_context += f"   {ctx['content'][:200]}...\n\n"
        
        # Enhanced prompt with cross-referencing
        prompt = f"""<|im_start|>system
You are a legal document analysis assistant. Create clear, easy-to-understand summaries for non-lawyers.
Use simple language and bullet points for better readability.

IMPORTANT: When relevant information is available from other legal documents in the database, 
incorporate it to provide complete legal context, especially for:
- Definitions of sections, articles, and legal provisions
- Punishments and penalties for crimes
- Related case precedents and court decisions
- Legal procedures and requirements<|im_end|>
<|im_start|>user
Analyze this legal document and provide a structured summary with cross-references:

PRIMARY DOCUMENT:
{context}
{additional_context}

Format your response EXACTLY like this:

## Document Overview
[Write 2-3 sentences explaining what this document is about in simple terms]

## Key Legal Points
[List 5-8 bullet points. When mentioning sections/crimes/penalties, include specific details from cross-references:]
- **Point Title**: Brief explanation (mention Section X penalties: [details from other docs])
- **Point Title**: Brief explanation with relevant legal context
[Continue with 5-8 points total]

## Scope & Applicability
[1-2 sentences about who this applies to and when]

## Related Laws & References
[List any cross-references found in other documents:]
- Section/Article references with their purposes
- Related acts and provisions
- Relevant case laws or precedents mentioned

Use simple, clear language. When mentioning punishments or penalties, be specific.
Incorporate information from cross-referenced documents to provide complete legal context.<|im_end|>
<|im_start|>assistant
"""
        
        # Stream from LLM
        import core
        llm = core.get_llm()
        
        full_summary = ""
        for chunk in llm.stream(prompt, stop=["<|im_end|>"]):
            full_summary += chunk
            emit('summary_chunk', {'chunk': chunk})
            socketio.sleep(0)  # Yield control
        
        full_summary = full_summary.strip()
        
        # Translate to Hindi if requested
        translated_summary = ""
        if language == 'hi':
            try:
                print(f"🌐 Translating summary to Hindi...")
                emit('translation_status', {'status': 'translating'})
                emit('search_status', {'message': "🌐 Translating summary..."})
                
                translator = GoogleTranslator(source='en', target='hi')
                
                # Translate in chunks to avoid length limits
                lines = full_summary.split('\n')
                translated_lines = []
                
                for line in lines:
                    if line.strip():
                        if len(line) > 4500:  # Split very long lines
                            # Translate in smaller chunks
                            words = line.split()
                            chunk_size = 100
                            translated_chunks = []
                            for i in range(0, len(words), chunk_size):
                                chunk = ' '.join(words[i:i+chunk_size])
                                translated_chunks.append(translator.translate(chunk))
                            translated_lines.append(' '.join(translated_chunks))
                        else:
                            translated_lines.append(translator.translate(line))
                    else:
                        translated_lines.append('')
                
                translated_summary = '\n'.join(translated_lines)
                emit('translation_complete', {'translated': translated_summary})
            except Exception as e:
                print(f"Translation error: {e}")
                emit('translation_status', {'status': 'failed', 'error': str(e)})
                translated_summary = full_summary  # Fallback to English
        
        # Translated summary handling above...
        
        # INGESTION STEP: Now that we have the summary, ingest the document
        try:
            emit('search_status', {'message': "🔄 Finalizing ingestion..."})
            print(f"🔄 Ingesting {filename} into Vector DB with Context...")
            chunk_ids = ingest.ingest_document(temp_path, filename, summary=full_summary)
            print(f"✅ Ingestion complete: {len(chunk_ids)} chunks")
        except Exception as ingest_error:
            print(f"❌ Ingestion failed: {ingest_error}")
            chunk_ids = []

        # Update database with complete summary (both English and Hindi if available)
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    db_data = json.load(f)
                
                # Find and update the record
                for record in db_data:
                    if record['filename'] == filename:
                        record['summary'] = full_summary
                        if translated_summary:
                            record['summary_hi'] = translated_summary
                        record['status'] = 'uploaded'
                        if chunk_ids:
                             record['chunk_ids'] = chunk_ids
                        break
                
                # Save updated database
                with open(DB_FILE, 'w') as f:
                    json.dump(db_data, f, indent=4)
                
                print(f"✅ Summary generated and saved for {filename}")
            except Exception as e:
                print(f"Error updating database: {e}")
        
        # Cleanup: Delete temporary file after successful processing
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"🗑️  Cleaned up temporary file: {temp_path}")
        except Exception as e:
            print(f"Warning: Could not delete temp file {temp_path}: {e}")
        
        emit('summary_complete', {
            'summary': full_summary,
            'summary_hi': translated_summary if language == 'hi' else None,
            'references': sorted(list(referenced_docs))  # Include all referenced documents
        })
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup temp file even on error
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"🗑️  Cleaned up temporary file after error: {temp_path}")
        except:
            pass
        
        emit('summary_error', {'error': str(e)})

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
