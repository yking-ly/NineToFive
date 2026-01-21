# Firebase Integration Setup Guide

This guide will help you set up Firebase Authentication and Firestore for the NineToFive Legal application.

## Prerequisites

- Google account
- Node.js and npm installed
- Python 3.8+ installed

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or "Create a project"
3. Enter project name: `NineToFive-Legal` (or your preferred name)
4. Enable/disable Google Analytics (optional)
5. Click "Create project"

## Step 2: Enable Authentication

1. In Firebase Console, go to **Build > Authentication**
2. Click "Get started"
3. Go to **Sign-in method** tab
4. Click on **Google**
5. Toggle "Enable"
6. Set support email (your email)
7. Click "Save"

## Step 3: Create Firestore Database

1. In Firebase Console, go to **Build > Firestore Database**
2. Click "Create database"
3. Select **Start in production mode** (we'll add rules later)
4. Choose your preferred location (e.g., `us-central1`)
5. Click "Enable"

## Step 4: Get Web App Configuration

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Scroll down to "Your apps"
3. Click the **Web** icon (`</>`)
4. Register app with nickname: `NineToFive-Web`
5. **Don't** check "Also set up Firebase Hosting"
6. Click "Register app"
7. Copy the configuration object - you'll need these values:
   ```javascript
   const firebaseConfig = {
     apiKey: "...",
     authDomain: "...",
     projectId: "...",
     storageBucket: "...",
     messagingSenderId: "...",
     appId: "..."
   };
   ```

## Step 5: Configure Frontend

1. Navigate to `frontend` directory
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and fill in your Firebase configuration:
   ```
   VITE_FIREBASE_API_KEY=your_api_key
   VITE_FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your_project_id
   VITE_FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
   VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   VITE_FIREBASE_APP_ID=your_app_id
   ```

## Step 6: Get Service Account Key (Backend)

1. In Firebase Console, go to **Project Settings > Service Accounts**
2. Click "Generate new private key"
3. Click "Generate key" in the confirmation dialog
4. A JSON file will be downloaded - **keep this secure!**
5. Create a `config` folder in `backend`:
   ```bash
   mkdir backend/config
   ```
6. Move the downloaded JSON file to `backend/config/serviceAccountKey.json`

## Step 7: Configure Backend

1. Navigate to `backend` directory
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and set the path to your service account key:
   ```
   FIREBASE_SERVICE_ACCOUNT_PATH=config/serviceAccountKey.json
   ```

## Step 8: Install Dependencies

### Frontend
```bash
cd frontend
npm install
```

### Backend
```bash
cd backend
pip install -r requirements.txt
```

## Step 9: Set Up Firestore Security Rules

1. In Firebase Console, go to **Firestore Database > Rules**
2. Replace the default rules with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users collection
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Sessions collection
    match /sessions/{sessionId} {
      allow read, create: if request.auth != null;
      allow update, delete: if request.auth != null && 
        resource.data.userId == request.auth.uid;
    }
    
    // Chats collection
    match /chats/{chatId} {
      allow read, create: if request.auth != null;
      allow update, delete: if request.auth != null && 
        resource.data.userId == request.auth.uid;
    }
    
    // Documents collection
    match /documents/{documentId} {
      allow read, create: if request.auth != null;
      allow update, delete: if request.auth != null && 
        resource.data.userId == request.auth.uid;
    }
  }
}
```

3. Click "Publish"

## Step 10: Create Firestore Indexes

Some queries require composite indexes. Create them as needed:

1. Go to **Firestore Database > Indexes**
2. Click "Add index"
3. Create the following indexes:

### Sessions Index
- Collection ID: `sessions`
- Fields:
  - `userId` (Ascending)
  - `updatedAt` (Descending)

### Chats Index
- Collection ID: `chats`
- Fields:
  - `sessionId` (Ascending)
  - `timestamp` (Ascending)

### Documents Index
- Collection ID: `documents`
- Fields:
  - `userId` (Ascending)
  - `uploadedAt` (Descending)

## Step 11: Update .gitignore

Make sure your `.gitignore` includes:

```
# Environment variables
.env
.env.local

# Firebase service account
**/serviceAccountKey.json
**/config/*.json
```

## Step 12: Test the Setup

1. Start the backend:
   ```bash
   cd backend
   python app.py
   ```

2. Start the frontend (in a new terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. Open your browser to `http://localhost:5173`
4. You should see the login page
5. Click "Continue with Google"
6. Sign in with your Google account
7. You should be redirected to the home page

## Troubleshooting

### "Firebase: Error (auth/unauthorized-domain)"
- Go to Firebase Console > Authentication > Settings > Authorized domains
- Add `localhost` and your deployment domain

### "Missing or insufficient permissions"
- Check Firestore security rules
- Ensure you're signed in
- Check browser console for detailed errors

### Backend can't initialize Firebase
- Verify service account key path in `.env`
- Ensure the JSON file exists and is valid
- Check file permissions

### Frontend can't connect to Firebase
- Verify all environment variables in `.env`
- Restart the Vite dev server after changing `.env`
- Check browser console for configuration errors

## Security Best Practices

1. **Never commit** `.env` files or service account keys
2. **Rotate** service account keys periodically
3. **Use** environment-specific Firebase projects (dev/staging/prod)
4. **Enable** App Check for production (optional but recommended)
5. **Monitor** Firebase usage and set up billing alerts

## Next Steps

- Customize session management in `SessionContext.jsx`
- Add more Firestore collections as needed
- Implement data migration from `uploads_db.json` to Firestore
- Set up Firebase Cloud Functions for advanced features
- Configure Firebase Storage for file uploads (optional)

## Support

For issues or questions:
- Check Firebase documentation: https://firebase.google.com/docs
- Review the implementation plan: `.agent/workflows/firebase-integration.md`
- Check application logs for detailed error messages
