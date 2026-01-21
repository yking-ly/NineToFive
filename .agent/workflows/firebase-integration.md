---
description: Firebase Integration with Google Sign-In and Session Management
---

# Firebase Integration Implementation Plan

## Overview
Integrate Firebase Authentication with Google Sign-In, implement user sessions, chat history persistence, and document management with cached summaries.

## Phase 1: Firebase Setup & Configuration

### 1.1 Install Firebase Dependencies
```bash
cd frontend
npm install firebase
```

### 1.2 Backend Dependencies
```bash
cd backend
pip install firebase-admin
```

### 1.3 Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project: "NineToFive-Legal"
3. Enable Google Authentication in Authentication > Sign-in method
4. Enable Firestore Database
5. Download configuration files:
   - Web app config (for frontend)
   - Service account key (for backend)

### 1.4 Environment Configuration
Create `.env` files:

**frontend/.env**:
```
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_auth_domain
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_storage_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

**backend/.env**:
```
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/serviceAccountKey.json
```

## Phase 2: Frontend Implementation

### 2.1 Firebase Configuration
Create `frontend/src/config/firebase.js`:
- Initialize Firebase app
- Export auth instance
- Export Firestore instance

### 2.2 Authentication Context
Create `frontend/src/context/AuthContext.jsx`:
- Google Sign-In functionality
- Sign-Out functionality
- User state management
- Protected route wrapper

### 2.3 Login Page
Create `frontend/src/pages/Login.jsx`:
- Beautiful glassmorphic design
- Google Sign-In button
- Loading states
- Error handling

### 2.4 Session Management
Create `frontend/src/context/SessionContext.jsx`:
- Create new session
- Load existing sessions
- Switch between sessions
- Delete sessions
- Auto-save chat history

### 2.5 Update Existing Pages
- Add authentication checks to all pages
- Add session selector to Chat and Kira pages
- Add user profile dropdown in navigation
- Implement sign-out functionality

## Phase 3: Backend Implementation

### 3.1 Firebase Admin Setup
Update `backend/app.py`:
- Initialize Firebase Admin SDK
- Add middleware for token verification
- Create user verification decorator

### 3.2 User Management Endpoints
Create `backend/user_service.py`:
- `/api/user/profile` - Get user profile
- `/api/user/sessions` - List user sessions
- `/api/user/sessions/create` - Create new session
- `/api/user/sessions/<id>` - Get session details
- `/api/user/sessions/<id>/delete` - Delete session

### 3.3 Document Management
Create `backend/document_service.py`:
- `/api/user/documents` - List user's uploaded documents
- `/api/user/documents/<id>` - Get document with cached summary
- Link documents to user ID
- Store summaries in Firestore

### 3.4 Chat History
Update `backend/app.py` WebSocket handlers:
- Save chat messages to Firestore
- Load chat history from Firestore
- Associate chats with sessions and users

## Phase 4: Firestore Schema

### Collections Structure

```
users/
  {userId}/
    email: string
    displayName: string
    photoURL: string
    createdAt: timestamp
    lastLogin: timestamp

sessions/
  {sessionId}/
    userId: string
    title: string
    createdAt: timestamp
    updatedAt: timestamp
    persona: string (default|kira)
    
chats/
  {chatId}/
    sessionId: string
    userId: string
    role: string (user|assistant)
    content: string
    timestamp: timestamp
    sources: array
    language: string

documents/
  {documentId}/
    userId: string
    filename: string
    driveUrl: string
    thumbnail: string
    uploadedAt: timestamp
    summary: string
    summary_hi: string (optional)
    chunk_ids: array
    status: string
```

## Phase 5: UI/UX Enhancements

### 5.1 Session Sidebar
Create `frontend/src/components/SessionSidebar.jsx`:
- List all sessions
- Create new session button
- Delete session with confirmation
- Session search/filter
- Glassmorphic design

### 5.2 Document Library
Create `frontend/src/pages/Documents.jsx`:
- Grid view of uploaded documents
- Cached summaries display
- Filter by date/name
- Quick view modal
- Delete functionality

### 5.3 User Profile
Create `frontend/src/components/UserProfile.jsx`:
- User avatar dropdown
- Profile information
- Sign out button
- Settings link

## Phase 6: Testing & Optimization

### 6.1 Test Authentication Flow
- Google Sign-In
- Token refresh
- Session persistence
- Sign-Out

### 6.2 Test Session Management
- Create sessions
- Switch sessions
- Load chat history
- Delete sessions

### 6.3 Test Document Management
- Upload documents
- View cached summaries
- Filter documents
- Delete documents

### 6.4 Performance Optimization
- Implement pagination for sessions
- Lazy load chat history
- Cache document summaries
- Optimize Firestore queries

## Phase 7: Security

### 7.1 Firestore Security Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    match /sessions/{sessionId} {
      allow read, write: if request.auth != null && 
        resource.data.userId == request.auth.uid;
    }
    
    match /chats/{chatId} {
      allow read, write: if request.auth != null && 
        resource.data.userId == request.auth.uid;
    }
    
    match /documents/{documentId} {
      allow read, write: if request.auth != null && 
        resource.data.userId == request.auth.uid;
    }
  }
}
```

### 7.2 Backend Security
- Verify Firebase tokens on all protected endpoints
- Validate user ownership of resources
- Rate limiting
- Input sanitization

## Implementation Order

1. **Setup** (Phase 1)
2. **Frontend Auth** (Phase 2.1-2.3)
3. **Backend Auth** (Phase 3.1)
4. **Session Management** (Phase 2.4, 3.2, 4)
5. **Document Management** (Phase 3.3, 5.2)
6. **UI Polish** (Phase 5)
7. **Security & Testing** (Phase 6-7)

## Notes
- Keep existing functionality intact
- Ensure backward compatibility
- Add migration script for existing data
- Implement proper error handling
- Add loading states everywhere
- Follow existing design patterns
