import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Get service account path from environment
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
            
            if service_account_path and os.path.exists(service_account_path):
                # Initialize with service account
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                print(f"✅ Firebase Admin SDK initialized with service account: {service_account_path}")
            else:
                # If path is set but not found, print warning but try default
                if service_account_path:
                    print(f"⚠️ Warning: Service account file not found at {service_account_path}")
                
                # Initialize with default credentials (for Cloud environments)
                firebase_admin.initialize_app()
                print("✅ Firebase Admin SDK initialized with default credentials")
        
        return True
    except Exception as e:
        print(f"❌ Error initializing Firebase Admin SDK: {e}")
        return False

# Initialize on module load
initialize_firebase()

# Get Firestore client
def get_firestore_client():
    """Get Firestore database client"""
    try:
        return firestore.client()
    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        return None

# Verify Firebase ID token
def verify_token(id_token):
    """Verify Firebase ID token and return decoded token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

# Decorator for protected routes
def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            # Extract token (format: "Bearer <token>")
            token = auth_header.split('Bearer ')[1]
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        # Verify token
        decoded_token = verify_token(token)
        
        if not decoded_token:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request
        request.user_id = decoded_token['uid']
        request.user_email = decoded_token.get('email')
        
        return f(*args, **kwargs)
    
    return decorated_function

# Helper functions for Firestore operations
def get_user_document(user_id):
    """Get user document from Firestore"""
    try:
        db = get_firestore_client()
        if not db:
            return None
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except Exception as e:
        print(f"Error getting user document: {e}")
        return None

def create_or_update_user(user_id, user_data):
    """Create or update user document in Firestore"""
    try:
        db = get_firestore_client()
        if not db:
            return False
        
        user_ref = db.collection('users').document(user_id)
        user_ref.set(user_data, merge=True)
        return True
    except Exception as e:
        print(f"Error creating/updating user: {e}")
        return False

def get_user_sessions(user_id, persona=None):
    """Get all sessions for a user"""
    try:
        db = get_firestore_client()
        if not db:
            return []
        
        query = db.collection('sessions').where('userId', '==', user_id)
        
        if persona:
            query = query.where('persona', '==', persona)
        
        query = query.order_by('updatedAt', direction=firestore.Query.DESCENDING)
        
        sessions = []
        for doc in query.stream():
            session_data = doc.to_dict()
            session_data['id'] = doc.id
            sessions.append(session_data)
        
        return sessions
    except Exception as e:
        print(f"Error getting user sessions: {e}")
        return []

def get_session_chats(session_id):
    """Get all chats for a session"""
    try:
        db = get_firestore_client()
        if not db:
            return []
        
        query = db.collection('chats') \
            .where('sessionId', '==', session_id) \
            .order_by('timestamp')
        
        chats = []
        for doc in query.stream():
            chat_data = doc.to_dict()
            chat_data['id'] = doc.id
            chats.append(chat_data)
        
        return chats
    except Exception as e:
        print(f"Error getting session chats: {e}")
        return []

def save_chat_message(session_id, user_id, role, content, sources=None, language='en'):
    """Save a chat message to Firestore"""
    try:
        db = get_firestore_client()
        if not db:
            return None
        
        chat_data = {
            'sessionId': session_id,
            'userId': user_id,
            'role': role,
            'content': content,
            'sources': sources or [],
            'language': language,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = db.collection('chats').add(chat_data)
        return doc_ref[1].id
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return None

def get_user_documents(user_id):
    """Get all documents uploaded by a user"""
    try:
        db = get_firestore_client()
        if not db:
            return []
        
        query = db.collection('documents') \
            .where('userId', '==', user_id) \
            .order_by('uploadedAt', direction=firestore.Query.DESCENDING)
        
        documents = []
        for doc in query.stream():
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            documents.append(doc_data)
        
        return documents
    except Exception as e:
        print(f"Error getting user documents: {e}")
        return []

def save_document(user_id, filename, drive_url, thumbnail, summary='', chunk_ids=None):
    """Save document metadata to Firestore"""
    try:
        db = get_firestore_client()
        if not db:
            return None
        
        doc_data = {
            'userId': user_id,
            'filename': filename,
            'driveUrl': drive_url,
            'thumbnail': thumbnail,
            'summary': summary,
            'chunk_ids': chunk_ids or [],
            'status': 'uploaded',
            'uploadedAt': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = db.collection('documents').add(doc_data)
        return doc_ref[1].id
    except Exception as e:
        print(f"Error saving document: {e}")
        return None
