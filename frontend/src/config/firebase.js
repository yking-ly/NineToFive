import { initializeApp } from 'firebase/app';
import { getAnalytics } from 'firebase/analytics';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBWcvjMiV_nfu2Dv1WgPuaRAWVjJ-6mIkY",
  authDomain: "ninetofive-ea427.firebaseapp.com",
  projectId: "ninetofive-ea427",
  storageBucket: "ninetofive-ea427.firebasestorage.app",
  messagingSenderId: "727490526238",
  appId: "1:727490526238:web:6c226b44168e2254e0020f",
  measurementId: "G-8MFKGXZVZ4"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// Initialize Firebase Authentication
export const auth = getAuth(app);

// Initialize Google Auth Provider
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account'
});

// Initialize Firestore
export const db = getFirestore(app);

export { analytics };
export default app;
