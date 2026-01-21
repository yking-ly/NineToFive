import { createContext, useContext, useState, useEffect } from 'react';
import {
    collection,
    doc,
    addDoc,
    getDoc,
    getDocs,
    updateDoc,
    deleteDoc,
    query,
    where,
    orderBy,
    serverTimestamp,
    onSnapshot
} from 'firebase/firestore';
import { db } from '../config/firebase';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

const SessionContext = createContext({});

export const useSession = () => {
    const context = useContext(SessionContext);
    if (!context) {
        throw new Error('useSession must be used within SessionProvider');
    }
    return context;
};

export const SessionProvider = ({ children }) => {
    const { user } = useAuth();
    const [sessions, setSessions] = useState([]);
    const [currentSession, setCurrentSession] = useState(null);
    const [loading, setLoading] = useState(true);

    // Load user sessions
    useEffect(() => {
        if (!user) {
            // Guest mode - start fresh or load from local storage if we wanted persistence
            // For now, transient sessions.
            setSessions([]);
            setCurrentSession(null);
            setLoading(false);
            return;
        }

        setLoading(true);

        // Real-time listener for sessions
        const sessionsQuery = query(
            collection(db, 'sessions'),
            where('userId', '==', user.uid),
            orderBy('updatedAt', 'desc')
        );

        const unsubscribe = onSnapshot(sessionsQuery, (snapshot) => {
            const sessionsData = snapshot.docs.map(doc => ({
                id: doc.id,
                ...doc.data(),
            }));

            setSessions(sessionsData);

            // Auto-select first session if none selected
            if (!currentSession && sessionsData.length > 0) {
                setCurrentSession(sessionsData[0]);
            }

            setLoading(false);
        }, (error) => {
            console.error('Error loading sessions:', error);
            toast.error('Failed to load sessions');
            setLoading(false);
        });

        return unsubscribe;
    }, [user]);

    // Create new session
    const createSession = async (title = 'New Conversation', persona = 'default') => {
        const newSessionData = {
            title: title || `Conversation ${sessions.length + 1}`,
            persona,
            createdAt: user ? serverTimestamp() : new Date(),
            updatedAt: user ? serverTimestamp() : new Date(),
            userId: user ? user.uid : 'guest',
        };

        try {
            if (user) {
                // Firestore logic
                const docRef = await addDoc(collection(db, 'sessions'), newSessionData);
                const newSession = { id: docRef.id, ...newSessionData };
                return newSession;
            } else {
                // Guest logic
                const newSession = {
                    id: `guest_${Date.now()}`,
                    ...newSessionData
                };
                setSessions(prev => [newSession, ...prev]);
                setCurrentSession(newSession);
                toast.success('Guest session created', { icon: '👻' });
                return newSession;
            }
        } catch (error) {
            console.error('Error creating session:', error);
            toast.error('Failed to create session');
            return null;
        }
    };

    // Update session
    const updateSession = async (sessionId, updates) => {
        if (user) {
            try {
                const sessionRef = doc(db, 'sessions', sessionId);
                await updateDoc(sessionRef, {
                    ...updates,
                    updatedAt: serverTimestamp(),
                });
            } catch (error) {
                console.error('Error updating session:', error);
            }
        } else {
            // Guest mode
            setSessions(prev => prev.map(s =>
                s.id === sessionId
                    ? { ...s, ...updates, updatedAt: new Date() }
                    : s
            ));
        }
    };

    // Delete session
    const deleteSession = async (sessionId) => {
        try {
            if (user) {
                // Delete chats
                const chatsQuery = query(
                    collection(db, 'chats'),
                    where('sessionId', '==', sessionId),
                    where('userId', '==', user.uid)
                );
                const chatsSnapshot = await getDocs(chatsQuery);
                await Promise.all(chatsSnapshot.docs.map(doc => deleteDoc(doc.ref)));
                // Delete session
                await deleteDoc(doc(db, 'sessions', sessionId));
            } else {
                // Guest mode
                setSessions(prev => prev.filter(s => s.id !== sessionId));
            }

            // Update current session
            if (currentSession?.id === sessionId) {
                const remaining = sessions.filter(s => s.id !== sessionId);
                setCurrentSession(remaining[0] || null);
            }
            toast.success('Session deleted', { icon: '🗑️' });
        } catch (error) {
            console.error('Error deleting session:', error);
            toast.error('Failed to delete session');
        }
    };

    // Switch to a different session
    const switchSession = (session) => {
        setCurrentSession(session);
    };

    // Save chat message
    const saveChatMessage = async (sessionId, role, content, sources = [], language = 'en') => {
        if (!sessionId) return;

        // Create payload
        const chatData = {
            sessionId,
            userId: user ? user.uid : 'guest',
            role,
            content,
            sources,
            language,
            timestamp: user ? serverTimestamp() : new Date(),
        };

        if (user) {
            try {
                await addDoc(collection(db, 'chats'), chatData);
                await updateSession(sessionId, {}); // Update timestamp
            } catch (error) {
                console.error('Error saving chat message:', error);
            }
        } else {
            // Guest mode
            // Store in memory for history retrieval
            if (!window.guestChats) window.guestChats = {};
            if (!window.guestChats[sessionId]) window.guestChats[sessionId] = [];
            window.guestChats[sessionId].push(chatData);

            await updateSession(sessionId, {}); // Update timestamp
        }
    };

    // Load chat history for a session
    const loadChatHistory = async (sessionId) => {
        if (!sessionId) return [];

        if (user) {
            try {
                const chatsQuery = query(
                    collection(db, 'chats'),
                    where('sessionId', '==', sessionId),
                    where('userId', '==', user.uid),
                    orderBy('timestamp', 'asc')
                );

                const snapshot = await getDocs(chatsQuery);
                return snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data(),
                }));
            } catch (error) {
                console.error('Error loading chat history:', error);
                return [];
            }
        } else {
            // Guest mode
            if (window.guestChats && window.guestChats[sessionId]) {
                return [...window.guestChats[sessionId]];
            }
            return [];
        }
    };

    const value = {
        sessions,
        currentSession,
        loading,
        createSession,
        updateSession,
        deleteSession,
        switchSession,
        saveChatMessage,
        loadChatHistory,
    };

    return (
        <SessionContext.Provider value={value}>
            {children}
        </SessionContext.Provider>
    );
};
