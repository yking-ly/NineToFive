import { createContext, useContext, useState, useEffect } from 'react';
import {
    signInWithPopup,
    signOut as firebaseSignOut,
    onAuthStateChanged
} from 'firebase/auth';
import { doc, setDoc, getDoc, serverTimestamp } from 'firebase/firestore';
import { auth, googleProvider, db } from '../config/firebase';
import toast from 'react-hot-toast';

const AuthContext = createContext({});

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [authToken, setAuthToken] = useState(null);

    // Initialize auth state listener
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                // Get ID token
                const token = await firebaseUser.getIdToken();
                setAuthToken(token);

                // Create/update user document in Firestore
                await createOrUpdateUserDocument(firebaseUser);

                setUser({
                    uid: firebaseUser.uid,
                    email: firebaseUser.email,
                    displayName: firebaseUser.displayName,
                    photoURL: firebaseUser.photoURL,
                });
            } else {
                setUser(null);
                setAuthToken(null);
            }
            setLoading(false);
        });

        return unsubscribe;
    }, []);

    // Create or update user document in Firestore
    const createOrUpdateUserDocument = async (firebaseUser) => {
        try {
            const userRef = doc(db, 'users', firebaseUser.uid);
            const userSnap = await getDoc(userRef);

            const userData = {
                email: firebaseUser.email,
                displayName: firebaseUser.displayName,
                photoURL: firebaseUser.photoURL,
                lastLogin: serverTimestamp(),
            };

            if (!userSnap.exists()) {
                // New user
                await setDoc(userRef, {
                    ...userData,
                    createdAt: serverTimestamp(),
                });
            } else {
                // Existing user - update last login
                await setDoc(userRef, userData, { merge: true });
            }
        } catch (error) {
            console.error('Error creating/updating user document:', error);
        }
    };

    // Sign in with Google
    const signInWithGoogle = async () => {
        try {
            setLoading(true);
            const result = await signInWithPopup(auth, googleProvider);

            toast.success(`Welcome, ${result.user.displayName}!`, {
                icon: '👋',
                duration: 3000,
            });

            return result.user;
        } catch (error) {
            console.error('Error signing in with Google:', error);

            let errorMessage = 'Failed to sign in';
            if (error.code === 'auth/popup-closed-by-user') {
                errorMessage = 'Sign-in cancelled';
            } else if (error.code === 'auth/network-request-failed') {
                errorMessage = 'Network error. Please check your connection';
            }

            toast.error(errorMessage, {
                duration: 4000,
            });

            throw error;
        } finally {
            setLoading(false);
        }
    };

    // Sign out
    const signOut = async () => {
        try {
            await firebaseSignOut(auth);
            setUser(null);
            setAuthToken(null);
            toast.success('Signed out successfully', {
                icon: '👋',
            });
        } catch (error) {
            console.error('Error signing out:', error);
            toast.error('Failed to sign out');
            throw error;
        }
    };

    // Refresh token
    const refreshToken = async () => {
        if (auth.currentUser) {
            const token = await auth.currentUser.getIdToken(true);
            setAuthToken(token);
            return token;
        }
        return null;
    };

    const value = {
        user,
        loading,
        authToken,
        signInWithGoogle,
        signOut,
        refreshToken,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
