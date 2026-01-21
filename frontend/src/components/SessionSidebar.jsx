import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
    HiPlus,
    HiTrash,
    HiChatBubbleLeft,
    HiMagnifyingGlass,
    HiXMark,
    HiChevronLeft,
    HiChevronRight
} from 'react-icons/hi2';
import { useSession } from '../context/SessionContext';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

const SessionSidebar = ({ isOpen, onToggle, persona = 'default' }) => {
    const {
        sessions,
        currentSession,
        createSession,
        deleteSession,
        switchSession,
        loading
    } = useSession();

    const { user } = useAuth();
    const navigate = useNavigate();

    // If user is not logged in, do not render sidebar
    if (!user) return null;

    const [searchQuery, setSearchQuery] = useState('');
    const [deletingId, setDeletingId] = useState(null);

    // Filter sessions by persona and search query
    const filteredSessions = sessions
        .filter(s => s.persona === persona)
        .filter(s =>
            s.title.toLowerCase().includes(searchQuery.toLowerCase())
        );

    const handleCreateSession = async () => {
        const title = `${persona === 'kira' ? 'Kira' : 'Legal'} Chat ${sessions.filter(s => s.persona === persona).length + 1}`;
        const newSession = await createSession(title, persona);
        if (newSession) {
            switchSession(newSession);
        }
    };

    const handleDeleteSession = async (sessionId, e) => {
        e.stopPropagation();

        if (deletingId === sessionId) {
            // Confirm delete
            await deleteSession(sessionId);
            setDeletingId(null);
        } else {
            // First click - show confirmation
            setDeletingId(sessionId);
            toast('Click again to confirm deletion', {
                icon: '⚠️',
                duration: 2000,
            });

            // Reset after 2 seconds
            setTimeout(() => setDeletingId(null), 2000);
        }
    };

    const formatDate = (timestamp) => {
        if (!timestamp) return '';

        const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    return (
        <>
            {/* Toggle Button */}
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onToggle}
                className={`fixed top-24 left-4 z-50 glass p-2 rounded-lg shadow-lg ${isOpen ? 'hidden' : 'block'}`}
            >
                <HiChevronRight className="text-xl text-white" />
            </motion.button>

            {/* Sidebar */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Overlay (Mobile Only) */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onToggle}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 md:hidden"
                        />

                        {/* Sidebar Content */}
                        <motion.div
                            initial={{ x: -300 }}
                            animate={{ x: 0 }}
                            exit={{ x: -300 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed left-0 top-0 h-full w-80 glass-card border-r border-white/10 z-40 flex flex-col"
                        >
                            {/* Header */}
                            <div className="p-4 border-b border-white/10">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                        <HiChatBubbleLeft className="text-purple-400" />
                                        Sessions
                                    </h2>
                                    <button
                                        onClick={onToggle}
                                        className="glass p-2 rounded-lg hover:bg-white/10 transition-colors"
                                    >
                                        <HiChevronLeft className="text-white" />
                                    </button>
                                </div>

                                {/* Search */}
                                <div className="relative">
                                    <HiMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="Search sessions..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    />
                                </div>

                                {/* New Session Button */}
                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={handleCreateSession}
                                    className="w-full mt-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-medium py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 hover:shadow-lg transition-all"
                                >
                                    <HiPlus className="text-lg" />
                                    New Session
                                </motion.button>
                            </div>

                            {/* Sessions List */}
                            <div className="flex-1 overflow-y-auto p-2">
                                {loading ? (
                                    <div className="flex items-center justify-center h-32">
                                        <motion.div
                                            animate={{ rotate: 360 }}
                                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                            className="w-8 h-8 border-3 border-purple-500 border-t-transparent rounded-full"
                                        />
                                    </div>
                                ) : filteredSessions.length === 0 ? (
                                    <div className="text-center py-8 text-gray-400">
                                        <HiChatBubbleLeft className="text-4xl mx-auto mb-2 opacity-50" />
                                        <p className="text-sm">
                                            {searchQuery ? 'No sessions found' : 'No sessions yet'}
                                        </p>
                                        <p className="text-xs mt-1">
                                            {!searchQuery && 'Create a new session to get started'}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        {filteredSessions.map((session) => (
                                            <motion.div
                                                key={session.id}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -10 }}
                                                whileHover={{ scale: 1.02 }}
                                                onClick={() => {
                                                    switchSession(session);
                                                    if (window.innerWidth < 768) onToggle();
                                                }}
                                                className={`group relative p-3 rounded-lg cursor-pointer transition-all ${currentSession?.id === session.id
                                                    ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/50'
                                                    : 'bg-white/5 hover:bg-white/10 border border-transparent'
                                                    }`}
                                            >
                                                <div className="flex items-start justify-between gap-2">
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium text-white truncate">
                                                            {session.title}
                                                        </p>
                                                        <p className="text-xs text-gray-400 mt-1">
                                                            {formatDate(session.updatedAt)}
                                                        </p>
                                                    </div>

                                                    <motion.button
                                                        whileHover={{ scale: 1.1 }}
                                                        whileTap={{ scale: 0.9 }}
                                                        onClick={(e) => handleDeleteSession(session.id, e)}
                                                        className={`opacity-0 group-hover:opacity-100 p-1.5 rounded-lg transition-all ${deletingId === session.id
                                                            ? 'bg-red-500 text-white'
                                                            : 'bg-white/10 text-gray-400 hover:text-red-400'
                                                            }`}
                                                    >
                                                        <HiTrash className="text-sm" />
                                                    </motion.button>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Footer */}
                            <div className="p-4 border-t border-white/10">
                                <p className="text-xs text-gray-400 text-center mb-2">
                                    {filteredSessions.length} {filteredSessions.length === 1 ? 'session' : 'sessions'}
                                </p>
                                {!user && (
                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => {
                                            navigate('/login');
                                            onToggle();
                                        }}
                                        className="w-full text-xs bg-white/10 hover:bg-white/20 text-blue-300 py-2 rounded-lg transition-colors border border-dashed border-blue-400/30"
                                    >
                                        Sign in to save history
                                    </motion.button>
                                )}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    );
};

export default SessionSidebar;
