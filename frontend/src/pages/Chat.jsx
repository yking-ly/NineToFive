import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaUserAstronaut, FaPaperPlane, FaArrowLeft, FaComments, FaRobot, FaUser, FaFilter, FaCopy, FaCheck, FaPlus, FaTrash, FaEdit, FaBars, FaTimes } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';

const API_BASE = 'http://127.0.0.1:5000';

export default function Chat() {
    // Chat list state
    const [chats, setChats] = useState([]);
    const [currentChatId, setCurrentChatId] = useState(null);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [editingChatId, setEditingChatId] = useState(null);
    const [editName, setEditName] = useState("");

    const location = useLocation();

    // Message state
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [selectedCollections, setSelectedCollections] = useState(["ipc", "bns", "mapping", "case_law"]);
    const [selectedLanguage, setSelectedLanguage] = useState("en");
    const [copiedId, setCopiedId] = useState(null);
    const messagesEndRef = useRef(null);

    // Load chats on mount
    useEffect(() => {
        loadChats();
    }, []);

    // Handle incoming query from Home page
    useEffect(() => {
        if (location.state?.query) {
            const constitutionMode = location.state?.constitutionMode || false;
            handleIncomingQuery(location.state.query, constitutionMode);
            // Clear state to prevent re-running on refresh
            window.history.replaceState({}, document.title);
        }
    }, [location.state]);

    const handleIncomingQuery = async (query, constitutionMode = false) => {
        // Create a new chat first
        const newChat = await createNewChat();
        if (newChat) {
            // If constitution mode, override collections
            if (constitutionMode) {
                setSelectedCollections(["constitution"]);
            }

            // Slight delay to ensure state updates
            setTimeout(() => {
                handleSend(query, newChat.id);
            }, 100);
        }
    };

    // Load messages when chat changes
    useEffect(() => {
        if (currentChatId) {
            loadChatMessages(currentChatId);
        }
    }, [currentChatId]);

    const loadChats = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/chats`);
            const data = await res.json();
            if (data.status === 'success') {
                setChats(data.chats || []);
                // Auto-select first chat or create new one
                if (data.chats && data.chats.length > 0 && !currentChatId) {
                    setCurrentChatId(data.chats[0].id);
                }
            }
        } catch (err) {
            console.error('Failed to load chats:', err);
        }
    };

    const loadChatMessages = async (chatId) => {
        try {
            const res = await fetch(`${API_BASE}/api/chats/${chatId}`);
            const data = await res.json();
            if (data.status === 'success' && data.chat) {
                const msgs = data.chat.messages.map((m, i) => ({
                    role: m.role === 'assistant' ? 'ai' : m.role,
                    content: m.content,
                    timestamp: m.timestamp
                }));
                setMessages(msgs);
            }
        } catch (err) {
            console.error('Failed to load messages:', err);
        }
    };

    const createNewChat = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/chats`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: "New Chat" })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setChats(prev => [data.chat, ...prev]);
                setCurrentChatId(data.chat.id);
                setMessages([]);
                return data.chat;
            }
        } catch (err) {
            console.error('Failed to create chat:', err);
            return null;
        }
    };

    const deleteChat = async (chatId) => {
        try {
            await fetch(`${API_BASE}/api/chats/${chatId}`, { method: 'DELETE' });
            setChats(prev => prev.filter(c => c.id !== chatId));
            if (currentChatId === chatId) {
                setCurrentChatId(chats.length > 1 ? chats.find(c => c.id !== chatId)?.id : null);
                setMessages([]);
            }
        } catch (err) {
            console.error('Failed to delete chat:', err);
        }
    };

    const renameChat = async (chatId, newName) => {
        try {
            await fetch(`${API_BASE}/api/chats/${chatId}/rename`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName })
            });
            setChats(prev => prev.map(c => c.id === chatId ? { ...c, name: newName } : c));
            setEditingChatId(null);
        } catch (err) {
            console.error('Failed to rename chat:', err);
        }
    };

    const copyToClipboard = async (text, id) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedId(id);
            setTimeout(() => setCopiedId(null), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const toggleCollection = (collection) => {
        setSelectedCollections(prev => {
            if (prev.includes(collection)) {
                if (prev.length === 1) return prev;
                return prev.filter(c => c !== collection);
            } else {
                return [...prev, collection];
            }
        });
    };

    const handleSend = async (text = null, chatIdOverride = null) => {
        const query = text || input;
        const activeChatId = chatIdOverride || currentChatId;

        if (!query.trim() || !activeChatId) return;

        const userMsg = { role: 'user', content: query };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE}/api/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    chat_id: activeChatId,
                    collections: selectedCollections,
                    language: selectedLanguage
                }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                const aiMsg = {
                    role: 'ai',
                    content: data.answer,
                    duration: data.duration_seconds,
                    collections: selectedCollections
                };
                setMessages(prev => [...prev, aiMsg]);

                // Update chat name from first message if it's "New Chat"
                const currentChat = chats.find(c => c.id === activeChatId);
                if (currentChat && currentChat.name === "New Chat") {
                    const shortName = query.slice(0, 30) + (query.length > 30 ? '...' : '');
                    renameChat(activeChatId, shortName);
                }

                loadChats(); // Refresh chat list to update timestamps
            } else {
                const errorMsg = { role: 'ai', content: "⚠️ Sorry, I encountered an error." };
                setMessages(prev => [...prev, errorMsg]);
            }
        } catch (error) {
            console.error('Error:', error);
            const errorMsg = { role: 'ai', content: "⚠️ Connection error. Check if the server is running." };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp * 1000);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="flex h-screen bg-neutral-950 text-white overflow-hidden">
            {/* Sidebar */}
            <aside className={`${sidebarOpen ? 'w-72' : 'w-0'} bg-neutral-900 border-r border-white/5 flex flex-col transition-all duration-300 overflow-hidden`}>
                {/* Sidebar Header */}
                <div className="p-4 border-b border-white/5">
                    <button
                        onClick={createNewChat}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all font-semibold"
                    >
                        <FaPlus /> New Chat
                    </button>
                </div>

                {/* Chat List */}
                <div className="flex-1 overflow-y-auto p-2">
                    {chats.length === 0 ? (
                        <p className="text-neutral-500 text-center text-sm mt-8">No chats yet</p>
                    ) : (
                        chats.map(chat => (
                            <div
                                key={chat.id}
                                className={`group flex items-center gap-2 px-3 py-3 rounded-lg cursor-pointer mb-1 transition-all ${currentChatId === chat.id
                                    ? 'bg-white/10 border border-white/10'
                                    : 'hover:bg-white/5'
                                    }`}
                                onClick={() => setCurrentChatId(chat.id)}
                            >
                                <FaComments className="text-neutral-500 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                    {editingChatId === chat.id ? (
                                        <input
                                            type="text"
                                            value={editName}
                                            onChange={(e) => setEditName(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') renameChat(chat.id, editName);
                                                if (e.key === 'Escape') setEditingChatId(null);
                                            }}
                                            onBlur={() => renameChat(chat.id, editName)}
                                            className="bg-neutral-800 border border-white/20 rounded px-2 py-1 text-sm w-full"
                                            autoFocus
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                    ) : (
                                        <>
                                            <p className="text-sm font-medium truncate">{chat.name}</p>
                                            <p className="text-xs text-neutral-500">{formatTime(chat.updated_at)}</p>
                                        </>
                                    )}
                                </div>
                                {/* Actions */}
                                <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setEditingChatId(chat.id);
                                            setEditName(chat.name);
                                        }}
                                        className="p-1.5 hover:bg-white/10 rounded"
                                        title="Rename"
                                    >
                                        <FaEdit className="w-3 h-3 text-neutral-400" />
                                    </button>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (confirm('Delete this chat?')) deleteChat(chat.id);
                                        }}
                                        className="p-1.5 hover:bg-red-500/20 rounded"
                                        title="Delete"
                                    >
                                        <FaTrash className="w-3 h-3 text-red-400" />
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Sidebar Footer */}
                <div className="p-4 border-t border-white/5">
                    <Link to="/" className="flex items-center gap-2 text-neutral-400 hover:text-white text-sm transition-colors">
                        <FaArrowLeft /> Back to Home
                    </Link>
                </div>
            </aside>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <header className="relative z-20 flex items-center gap-4 p-4 bg-neutral-950/80 backdrop-blur-xl border-b border-white/5">
                    <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                        {sidebarOpen ? <FaTimes /> : <FaBars />}
                    </button>
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                            <FaUserAstronaut className="text-white" />
                        </div>
                        <div>
                            <h1 className="font-bold text-lg">AI Legal Assistant</h1>
                            <p className="text-xs text-green-400 flex items-center gap-1">
                                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                                ONLINE • RAG ACTIVE
                            </p>
                        </div>
                    </div>
                </header>

                {/* Messages Area */}
                <main className="flex-1 overflow-y-auto p-4 md:p-6">
                    <div className="max-w-3xl mx-auto space-y-6">
                        {!currentChatId ? (
                            <div className="flex flex-col items-center justify-center h-full text-center">
                                <FaComments className="text-6xl text-neutral-700 mb-4" />
                                <h2 className="text-xl font-semibold text-neutral-400">No chat selected</h2>
                                <p className="text-neutral-500 mb-4">Create a new chat to start</p>
                                <button
                                    onClick={createNewChat}
                                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all font-semibold"
                                >
                                    <FaPlus className="inline mr-2" /> New Chat
                                </button>
                            </div>
                        ) : messages.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-64 text-center">
                                <FaRobot className="text-5xl text-neutral-700 mb-4" />
                                <h2 className="text-lg font-semibold text-neutral-400">Start a conversation</h2>
                                <p className="text-neutral-500 text-sm">Ask about IPC, BNS, or any legal query</p>
                            </div>
                        ) : (
                            messages.map((msg, idx) => (
                                <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    {msg.role !== 'user' && (
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center flex-shrink-0">
                                            <FaRobot className="text-white text-sm" />
                                        </div>
                                    )}
                                    <div className={`group relative max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                        ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white rounded-br-sm'
                                        : 'bg-neutral-800 text-neutral-100 rounded-bl-sm border border-white/5'
                                        }`}>
                                        {/* Copy button for all messages */}
                                        <button
                                            onClick={() => copyToClipboard(msg.content, idx)}
                                            className={`absolute top-2 right-2 p-1.5 rounded transition-all ${msg.role === 'user'
                                                ? 'opacity-0 group-hover:opacity-100 hover:bg-white/20'
                                                : 'hover:bg-white/10'
                                                }`}
                                            title="Copy message"
                                        >
                                            {copiedId === idx ? (
                                                <FaCheck className="w-3 h-3 text-green-400" />
                                            ) : (
                                                <FaCopy className={`w-3 h-3 ${msg.role === 'user' ? 'text-white/70' : 'text-neutral-400'}`} />
                                            )}
                                        </button>
                                        <div className={msg.role === 'ai' ? 'prose prose-invert prose-sm max-w-none pr-8' : 'pr-6'}>
                                            {msg.role === 'ai' ? (
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                            ) : (
                                                <p>{msg.content}</p>
                                            )}
                                        </div>
                                        {msg.duration && (
                                            <p className="text-xs text-neutral-500 mt-2">Generated in {msg.duration}s</p>
                                        )}
                                    </div>
                                    {msg.role === 'user' && (
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-pink-600 flex items-center justify-center flex-shrink-0">
                                            <FaUser className="text-white text-sm" />
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                        {isLoading && (
                            <div className="flex gap-3 justify-start">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                                    <FaRobot className="text-white text-sm" />
                                </div>
                                <div className="bg-neutral-800 rounded-2xl rounded-bl-sm px-4 py-3 border border-white/5">
                                    <div className="flex gap-1">
                                        <span className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce"></span>
                                        <span className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                                        <span className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </main>

                {/* Input Area */}
                {currentChatId && (
                    <footer className="relative z-20 p-4 md:p-6 bg-neutral-950/80 backdrop-blur-xl border-t border-white/5">
                        <div className="max-w-3xl mx-auto">
                            {/* Collection Filter Toggles */}
                            <div className="flex items-center justify-center gap-2 mb-4 flex-wrap">
                                <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-semibold flex items-center gap-1">
                                    <FaFilter className="w-2.5 h-2.5" /> Search in:
                                </span>
                                {[
                                    { id: 'ipc', label: 'IPC', color: 'from-orange-500 to-red-500' },
                                    { id: 'bns', label: 'BNS', color: 'from-blue-500 to-indigo-500' },
                                    { id: 'mapping', label: 'Mapping', color: 'from-green-500 to-emerald-500' },
                                    { id: 'case_law', label: 'Cases', color: 'from-purple-500 to-pink-500' }
                                ].map(col => (
                                    <button
                                        key={col.id}
                                        onClick={() => toggleCollection(col.id)}
                                        className={`px-3 py-1.5 rounded-full text-[11px] font-semibold uppercase tracking-wider transition-all duration-200 border ${selectedCollections.includes(col.id)
                                            ? `bg-gradient-to-r ${col.color} text-white border-transparent shadow-lg`
                                            : 'bg-neutral-900 text-neutral-500 border-white/10 hover:border-white/20'
                                            }`}
                                    >
                                        {col.label}
                                    </button>
                                ))}

                                <span className="text-neutral-700 mx-1">|</span>

                                {/* Language Toggle */}
                                {[
                                    { id: 'en', label: 'English' },
                                    { id: 'hi', label: 'हिंदी' },
                                    { id: 'all', label: 'Both' }
                                ].map(lang => (
                                    <button
                                        key={lang.id}
                                        onClick={() => setSelectedLanguage(lang.id)}
                                        className={`px-2.5 py-1.5 rounded-full text-[11px] font-medium transition-all duration-200 border ${selectedLanguage === lang.id
                                            ? 'bg-white text-neutral-900 border-white shadow-lg'
                                            : 'bg-neutral-900 text-neutral-500 border-white/10 hover:border-white/20'
                                            }`}
                                    >
                                        {lang.label}
                                    </button>
                                ))}
                            </div>

                            {/* Input Box */}
                            <div className="relative group">
                                <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 blur opacity-0 group-hover:opacity-100 transition duration-500"></div>
                                <div className="relative flex items-center gap-3 bg-neutral-900 rounded-2xl p-2 border border-white/10 shadow-xl focus-within:border-white/20 transition-colors">
                                    <input
                                        type="text"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        placeholder="Ask in English, Hindi, or Hinglish... (e.g., murder ki saza kya hai?)"
                                        disabled={isLoading}
                                        className="flex-1 bg-transparent border-none outline-none text-white px-4 py-3 placeholder:text-neutral-600 font-medium disabled:opacity-50"
                                    />
                                    <button
                                        onClick={() => handleSend()}
                                        disabled={!input.trim() || isLoading}
                                        className="p-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
                                    >
                                        <FaPaperPlane />
                                    </button>
                                </div>
                            </div>

                            <p className="text-center text-[10px] text-neutral-600 mt-3 uppercase tracking-wide">
                                AI Generated Responses may vary. Consult a Lawyer for serious advice.
                            </p>
                        </div>
                    </footer>
                )}
            </div>
        </div>
    );
}
