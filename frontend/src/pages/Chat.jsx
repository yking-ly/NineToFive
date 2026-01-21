import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaUserAstronaut, FaPaperPlane, FaArrowLeft, FaComments, FaRobot, FaUser } from 'react-icons/fa';
import { HiSparkles, HiBars3, HiXMark } from "react-icons/hi2";
import ReactMarkdown from 'react-markdown';
import { io } from 'socket.io-client';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { useSession } from '../context/SessionContext';
import { motion, AnimatePresence } from 'framer-motion';
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import SessionSidebar from '../components/SessionSidebar';
import UserProfile from '../components/UserProfile';

export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [selectedTag, setSelectedTag] = useState(null);
    const [loadingStatus, setLoadingStatus] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const messagesEndRef = useRef(null);
    const socketRef = useRef(null);

    // Contexts
    const { t, language, changeLanguage, isLoading: isLangLoading } = useLanguage();
    const { user } = useAuth();
    const {
        currentSession,
        createSession,
        loadChatHistory,
        saveChatMessage
    } = useSession();

    // Legal category tags
    const getLegalTags = (lang) => {
        const isHindi = lang === 'hi';
        return [
            { id: 'ipc', label: 'IPC', fullName: isHindi ? 'भारतीय दंड संहिता' : 'Indian Penal Code' },
            { id: 'bns', label: 'BNS', fullName: isHindi ? 'भारतीय न्याय संहिता' : 'Bharatiya Nyaya Sanhita' },
            { id: 'crpc', label: 'CrPC', fullName: isHindi ? 'दंड प्रक्रिया संहिता' : 'Criminal Procedure Code' },
            { id: 'bnss', label: 'BNSS', fullName: isHindi ? 'भारतीय नागरिक सुरक्षा संहिता' : 'Bharatiya Nagarik Suraksha Sanhita' },
            { id: 'iea', label: 'IEA', fullName: isHindi ? 'भारतीय साक्ष्य अधिनियम' : 'Indian Evidence Act' },
            { id: 'bsa', label: 'BSA', fullName: isHindi ? 'भारतीय साक्ष्य अधिनियम' : 'Bharatiya Sakshya Adhiniyam' },
        ];
    };

    const legalTags = getLegalTags(language);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load Chat History when session changes
    useEffect(() => {
        const fetchHistory = async () => {
            if (currentSession?.id) {
                const history = await loadChatHistory(currentSession.id);
                // Convert Firestore timestamps to serializable format if needed, or just use as is
                // Mapping structure to match UI
                const formattedHistory = history.map(msg => ({
                    role: msg.role,
                    content: msg.content,
                    sources: msg.sources || [],
                    tag: msg.tag
                }));
                setMessages(formattedHistory);
            } else {
                setMessages([]);
            }
        };
        fetchHistory();
    }, [currentSession]);

    // Initialize Socket
    useEffect(() => {
        socketRef.current = io('http://127.0.0.1:5000', {
            transports: ['polling'],
            upgrade: false,
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000,
            timeout: 60000,
            pingTimeout: 60000,
            pingInterval: 25000
        });

        const socket = socketRef.current;

        socket.on('connect', () => {
            console.log("✅ Connected to WebSocket Server");
        });

        socket.on('search_status', (data) => {
            setLoadingStatus(data.message);
        });

        socket.on('response_chunk', (chunk) => {
            setLoadingStatus(null);
            setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg.role === 'assistant') {
                    return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + chunk }];
                } else {
                    return [...prev, { role: 'assistant', content: chunk }];
                }
            });
        });

        socket.on('sources', (sources) => {
            setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg.role === 'assistant') {
                    return [...prev.slice(0, -1), { ...lastMsg, sources: sources }];
                }
                return prev;
            });
        });

        socket.on('response_complete', () => {
            setIsProcessing(false);
            setLoadingStatus(null);
        });

        socket.on('error', (data) => {
            console.error("Socket Error:", data);
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: " + data.error }]);
            setIsProcessing(false);
            setLoadingStatus(null);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || !socketRef.current) return;

        // Create session if it doesn't exist
        let activeSessionId = currentSession?.id;
        if (!activeSessionId) {
            const newSession = await createSession(input.slice(0, 30) + "...", 'default');
            if (newSession) activeSessionId = newSession.id;
        }

        const userMessage = {
            role: 'user',
            content: input,
            tag: selectedTag
        };

        // UI Update
        setMessages(prev => [
            ...prev,
            userMessage,
            { role: 'assistant', content: '', sources: [] }
        ]);

        // Save User Message to Context (Firestore/Local)
        if (activeSessionId) {
            await saveChatMessage(activeSessionId, 'user', input, [], language);
        }

        setInput("");
        setIsProcessing(true);

        const chatHistory = [...messages, userMessage];

        socketRef.current.emit('send_message', {
            message: userMessage.content,
            history: chatHistory,
            language: language,
            tag: selectedTag,
            sessionId: activeSessionId,
            userId: user ? user.uid : 'guest'
        });
    };

    return (
        <SkeletonTheme baseColor="#1a1a1a" highlightColor="#2a2a2a">
            <div className="h-screen bg-[#030303] text-white font-sans flex relative overflow-hidden">

                {/* Sidebar (Desktop: Persistent, Mobile: Drawer) */}
                <div className="hidden md:block relative z-30">
                    <SessionSidebar
                        isOpen={true}
                        onToggle={() => { }}
                        persona="default"
                    />
                </div>
                {/* Mobile Sidebar */}
                <div className="md:hidden relative z-40">
                    <SessionSidebar
                        isOpen={isSidebarOpen}
                        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                        persona="default"
                    />
                </div>

                {/* Main Content */}
                <div className="flex-1 flex flex-col relative h-full">

                    {/* Background elements */}
                    <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                        <div className="absolute top-10 right-10 w-[500px] h-[500px] bg-indigo-600/5 rounded-full blur-[150px] animate-pulse"></div>
                        <div className="absolute bottom-10 left-10 w-[400px] h-[400px] bg-purple-600/5 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }}></div>
                    </div>

                    {/* Header */}
                    <header className="relative z-20 px-8 py-5 flex items-center justify-between border-b border-white/5 bg-[#030303]/80 backdrop-blur-xl">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="md:hidden p-2 -ml-2 text-white/70 hover:text-white"
                            >
                                <HiBars3 className="w-6 h-6" />
                            </button>

                            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                                <FaUserAstronaut className="text-white w-6 h-6" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-white tracking-tight">
                                    {isLangLoading ? <Skeleton width={150} /> : t.title}
                                </h1>
                                <div className="flex items-center gap-2">
                                    <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                    </span>
                                    <span className="text-[10px] uppercase tracking-widest text-neutral-400 font-bold">
                                        {isLangLoading ? <Skeleton width={80} /> : t.subtitle}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="bg-neutral-900/50 p-1 rounded-xl border border-white/5 flex gap-1">
                                {['en', 'hi', 'hi-romanized'].map((langKey) => (
                                    <button
                                        key={langKey}
                                        onClick={() => changeLanguage(langKey)}
                                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${language === langKey
                                            ? 'bg-white text-black shadow-sm'
                                            : 'text-neutral-500 hover:text-white hover:bg-white/5'
                                            }`}
                                    >
                                        {langKey === 'en' ? 'EN' : langKey === 'hi' ? 'हिंदी' : 'Hinglish'}
                                    </button>
                                ))}
                            </div>

                            {user ? (
                                <UserProfile />
                            ) : (
                                <Link to="/login" className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-bold transition-all">
                                    Sign In
                                </Link>
                            )}
                        </div>
                    </header>

                    {/* Chat Area */}
                    <main className="flex-1 relative z-10 overflow-y-auto p-4 md:p-8 flex flex-col scroll-smooth">
                        {messages.length === 0 ? (
                            <div className="flex-1 flex flex-col items-center justify-center w-full max-w-7xl mx-auto px-4 md:px-12">
                                {/* Decongested Two-Column Approach */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center w-full">

                                    {/* Left Column: Intro Text */}
                                    <motion.div
                                        className="text-left space-y-8"
                                        initial={{ opacity: 0, x: -50 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ duration: 0.8 }}
                                    >
                                        <motion.div
                                            initial={{ scale: 0.8 }}
                                            animate={{ scale: 1 }}
                                            transition={{ duration: 0.5 }}
                                            className="w-24 h-24 rounded-[2rem] bg-gradient-to-br from-neutral-900 to-black border border-white/10 flex items-center justify-center shadow-2xl relative"
                                        >
                                            <div className="absolute inset-0 bg-white/5 rounded-[2rem] blur-xl opacity-50"></div>
                                            <HiSparkles className="w-10 h-10 text-indigo-400 opacity-80" />
                                        </motion.div>

                                        <div className="space-y-4">
                                            <h2 className="text-5xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white via-white to-white/40 tracking-tighter leading-tight">
                                                {isLangLoading ? <Skeleton count={2} /> : t.introTitle}
                                            </h2>
                                            <p className="text-neutral-400 text-xl leading-relaxed max-w-lg font-light">
                                                {isLangLoading ? <Skeleton count={3} /> : t.introText}
                                            </p>
                                        </div>
                                    </motion.div>

                                    {/* Right Column: Suggestions Grid */}
                                    <motion.div
                                        className="grid grid-cols-1 gap-4 w-full"
                                        initial={{ opacity: 0, x: 50 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ duration: 0.8, delay: 0.2 }}
                                    >
                                        {[1, 2, 3].map((i) => (
                                            <button
                                                key={i}
                                                onClick={() => !isLangLoading && setInput(t[`q${i}`])}
                                                disabled={isLangLoading}
                                                className="group relative p-6 rounded-2xl bg-neutral-900/40 border border-white/10 text-left hover:border-white/20 hover:bg-neutral-800 transition-all flex justify-between items-center"
                                            >
                                                <span className="text-lg text-neutral-300 group-hover:text-white transition-colors font-medium">
                                                    {isLangLoading ? <Skeleton width={200} /> : t[`q${i}`]}
                                                </span>
                                                <FaArrowLeft className="opacity-0 group-hover:opacity-100 -rotate-180 transform translate-x-2 group-hover:translate-x-0 transition-all text-indigo-400" />
                                            </button>
                                        ))}
                                    </motion.div>
                                </div>
                            </div>
                        ) : (
                            <div className="max-w-4xl w-full mx-auto space-y-8 pb-32">
                                {messages.map((msg, idx) => (
                                    <motion.div
                                        key={idx}
                                        className={`flex gap-6 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        transition={{ duration: 0.3, ease: 'easeOut' }}
                                    >
                                        {msg.role === 'assistant' && (
                                            <div className="w-10 h-10 rounded-2xl bg-neutral-800 flex items-center justify-center border border-white/5 shadow-lg flex-shrink-0 mt-2">
                                                <FaRobot className="w-5 h-5 text-indigo-400" />
                                            </div>
                                        )}

                                        <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-[85%]`}>
                                            <div className={`p-6 rounded-3xl backdrop-blur-sm shadow-xl ${msg.role === 'user'
                                                ? 'bg-white text-black rounded-tr-sm'
                                                : 'bg-neutral-900/80 border border-white/10 text-neutral-200 rounded-tl-sm'
                                                }`}>

                                                {msg.role === 'user' && msg.tag && (
                                                    <div className="mb-3">
                                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-black/5 border border-black/5 text-[10px] font-bold uppercase tracking-wider">
                                                            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>
                                                            {legalTags.find(t => t.id === msg.tag)?.label || msg.tag}
                                                        </span>
                                                    </div>
                                                )}

                                                <div className={`text-sm md:text-base leading-relaxed ${msg.role === 'assistant'
                                                    ? 'prose prose-invert prose-p:text-neutral-300 prose-headings:text-white prose-strong:text-white prose-code:text-indigo-300 prose-code:bg-indigo-950/30 prose-code:px-1 prose-code:rounded prose-ul:marker:text-neutral-500'
                                                    : 'whitespace-pre-wrap font-medium'
                                                    }`}>
                                                    {msg.role === 'assistant' ? (
                                                        <ReactMarkdown
                                                            components={{
                                                                code: ({ node, inline, className, children, ...props }) => (
                                                                    inline
                                                                        ? <code className="bg-white/10 rounded px-1.5 py-0.5 text-xs font-mono border border-white/5" {...props}>{children}</code>
                                                                        : <div className="relative my-4"><pre className="bg-[#0a0a0a] rounded-xl p-4 overflow-x-auto border border-white/10"><code className="text-sm font-mono text-neutral-300" {...props}>{children}</code></pre></div>
                                                                )
                                                            }}
                                                        >
                                                            {msg.content}
                                                        </ReactMarkdown>
                                                    ) : (
                                                        msg.content
                                                    )}
                                                </div>
                                            </div>

                                            {/* Sources Section */}
                                            {msg.sources && msg.sources.length > 0 && (
                                                <motion.div
                                                    className="mt-4 pl-2"
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    transition={{ delay: 0.5 }}
                                                >
                                                    <p className="text-[10px] uppercase font-bold text-neutral-500 mb-3 tracking-widest pl-1">
                                                        {isLangLoading ? <Skeleton width={100} /> : t.sources}
                                                    </p>
                                                    <div className="flex flex-wrap gap-3">
                                                        {msg.sources.map((source, sIdx) => (
                                                            <motion.a
                                                                key={sIdx}
                                                                href={source.driveUrl || '#'}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="flex items-center gap-3 bg-neutral-900 border border-white/10 hover:border-white/30 rounded-xl p-3 transition-all group no-underline shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                                                            >
                                                                {source.thumbnail ? (
                                                                    <img
                                                                        src={source.thumbnail}
                                                                        alt={source.filename}
                                                                        className="w-8 h-8 rounded-lg object-cover bg-neutral-800"
                                                                        onError={(e) => {
                                                                            e.target.style.display = 'none';
                                                                            e.target.nextElementSibling.style.display = 'flex';
                                                                        }}
                                                                    />
                                                                ) : null}
                                                                <div
                                                                    className="w-8 h-8 rounded-lg bg-neutral-800 flex items-center justify-center text-sm font-bold text-neutral-500 group-hover:text-white transition-colors"
                                                                    style={{ display: source.thumbnail ? 'none' : 'flex' }}
                                                                >
                                                                    📄
                                                                </div>
                                                                <div className="flex flex-col">
                                                                    <span className="text-xs font-medium text-neutral-300 group-hover:text-white transition-colors truncate max-w-[120px]">
                                                                        {source.filename}
                                                                    </span>
                                                                    <span className="text-[9px] text-neutral-500 uppercase tracking-wider group-hover:text-neutral-400">{t.trustedSource}</span>
                                                                </div>
                                                            </motion.a>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}

                                {isProcessing && (
                                    <motion.div
                                        className="flex gap-6 items-start"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                    >
                                        <div className="w-10 h-10 rounded-2xl bg-neutral-800 flex items-center justify-center border border-white/5 shadow-lg">
                                            <FaRobot className="w-5 h-5 text-indigo-400" />
                                        </div>
                                        <div className="p-4 rounded-2xl bg-neutral-900/50 border border-white/10 flex items-center gap-2">
                                            <div className="flex space-x-1">
                                                <motion.div className="w-2 h-2 bg-indigo-500 rounded-full" animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, repeat: Infinity }} />
                                                <motion.div className="w-2 h-2 bg-indigo-500 rounded-full" animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, delay: 0.2, repeat: Infinity }} />
                                                <motion.div className="w-2 h-2 bg-indigo-500 rounded-full" animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, delay: 0.4, repeat: Infinity }} />
                                            </div>
                                            <span className="text-xs text-neutral-500 font-medium ml-2 uppercase tracking-wider">
                                                {isLangLoading ? <Skeleton width={100} /> : (loadingStatus || t.loading)}
                                            </span>
                                        </div>
                                    </motion.div>
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </main>

                    {/* Input Floating Footer */}
                    <div className="absolute bottom-6 left-0 right-0 px-4 md:px-8 z-30 pointer-events-none">
                        <div className="max-w-3xl mx-auto w-full pointer-events-auto">
                            {/* Tag Selection */}
                            <AnimatePresence>
                                <motion.div
                                    className="mb-4 flex flex-wrap items-center justify-center gap-2"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <span className="text-[10px] uppercase font-bold text-neutral-500 tracking-wider h-6 flex items-center mr-1">
                                        {isLangLoading ? <Skeleton width={50} /> : t.filterBy}
                                    </span>
                                    {legalTags.map(tag => (
                                        <button
                                            key={tag.id}
                                            onClick={() => setSelectedTag(selectedTag === tag.id ? null : tag.id)}
                                            className={`px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all border ${selectedTag === tag.id
                                                ? 'bg-white text-black border-white shadow-[0_0_15px_rgba(255,255,255,0.3)]'
                                                : 'bg-black/40 text-neutral-500 border-white/10 hover:border-white/30 hover:text-white backdrop-blur-md'
                                                }`}
                                            title={tag.fullName}
                                        >
                                            {tag.label}
                                        </button>
                                    ))}
                                    {selectedTag && (
                                        <button
                                            onClick={() => setSelectedTag(null)}
                                            className="text-[10px] text-neutral-500 hover:text-white underline transition-colors h-6 flex items-center ml-1"
                                        >
                                            {t.clear}
                                        </button>
                                    )}
                                </motion.div>
                            </AnimatePresence>

                            <form
                                onSubmit={handleSendMessage}
                                className="relative group bg-neutral-900/40 backdrop-blur-2xl border border-white/10 rounded-[2rem] p-2 flex items-center shadow-2xl transition-all focus-within:bg-neutral-900/60 focus-within:border-white/20 focus-within:shadow-[0_0_30px_rgba(0,0,0,0.5)]"
                            >
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder={(isProcessing || isLangLoading) ? (t.analyzing || "Loading...") : t.placeholder}
                                    disabled={isProcessing}
                                    className="flex-1 bg-transparent border-none outline-none text-white px-6 py-4 placeholder:text-neutral-500 text-lg font-medium"
                                />
                                <button
                                    type="submit"
                                    disabled={isProcessing || !input.trim()}
                                    className="w-14 h-14 bg-white text-black rounded-full flex items-center justify-center transition-all shadow-lg hover:scale-105 disabled:opacity-50 disabled:scale-100 disabled:cursor-not-allowed group-hover:shadow-[0_0_20px_rgba(255,255,255,0.2)]"
                                >
                                    <FaPaperPlane className={`w-5 h-5 ${isProcessing ? 'opacity-50' : ''}`} />
                                </button>
                            </form>

                            <div className="text-center mt-3">
                                <p className="text-[10px] text-neutral-600 uppercase tracking-widest font-medium">
                                    {isLangLoading ? <Skeleton width={200} /> : t.aiDisclaimer}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </SkeletonTheme>
    )
}
