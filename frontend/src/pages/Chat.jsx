import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaUserAstronaut, FaPaperPlane, FaArrowLeft, FaComments, FaRobot, FaUser } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { io } from 'socket.io-client';
import { useLanguage } from '../context/LanguageContext';

export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [selectedTag, setSelectedTag] = useState(null);
    const messagesEndRef = useRef(null);
    const socketRef = useRef(null);

    // Global Language Context
    const { t, language, changeLanguage } = useLanguage();

    // Legal category tags
    const legalTags = [
        { id: 'ipc', label: 'IPC', fullName: 'Indian Penal Code' },
        { id: 'bns', label: 'BNS', fullName: 'Bharatiya Nyaya Sanhita' },
        { id: 'crpc', label: 'CrPC', fullName: 'Criminal Procedure Code' },
        { id: 'bnss', label: 'BNSS', fullName: 'Bharatiya Nagarik Suraksha Sanhita' },
        { id: 'iea', label: 'IEA', fullName: 'Indian Evidence Act' },
        { id: 'bsa', label: 'BSA', fullName: 'Bharatiya Sakshya Adhiniyam' },
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Initialize Socket
    useEffect(() => {
        // Connect to Flask-SocketIO backend with robust settings
        socketRef.current = io('http://127.0.0.1:5000', {
            transports: ['websocket', 'polling'], // Try WebSocket first, fallback to polling
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000,
        });

        const socket = socketRef.current;

        socket.on('connect', () => {
            console.log("✅ Connected to WebSocket Server");
        });

        socket.on('response_chunk', (chunk) => {
            setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                // Check if last message is assistant, otherwise add one (shouldn't happen with correct flow)
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
                return prev; // Waiting for first chunk to create bubble usually, or create it here? 
                // Better flow: create empty bubble on send, then update.
            });
        });

        socket.on('response_complete', () => {
            setIsLoading(false);
        });

        socket.on('error', (data) => {
            console.error("Socket Error:", data);
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: " + data.error }]);
            setIsLoading(false);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!input.trim() || !socketRef.current) return;

        const userMessage = {
            role: 'user',
            content: input,
            tag: selectedTag // Store the tag with the message
        };

        // Add User Message AND placeholder Assistant Message immediately for instant feedback
        setMessages(prev => [
            ...prev,
            userMessage,
            { role: 'assistant', content: '', sources: [] }
        ]);

        setInput("");
        setIsLoading(true);

        const chatHistory = [...messages, userMessage];

        // Emit to Backend with selected tag
        socketRef.current.emit('send_message', {
            message: userMessage.content,
            history: chatHistory,
            language: language,
            tag: selectedTag // Include the selected tag
        });
    };

    return (
        <div className="h-screen bg-neutral-950 text-white font-sans flex flex-col relative overflow-hidden">

            {/* Background elements */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-10 right-10 w-96 h-96 bg-white/5 rounded-full blur-[150px]"></div>
            </div>

            {/* Header */}
            <header className="relative z-20 glass border-b border-white/5 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-neutral-800 flex items-center justify-center border border-white/10 shadow-inner">
                        <FaUserAstronaut className="text-white/80" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-white tracking-tight">{t.title}</h1>
                        <div className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]"></span>
                            <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-semibold">{t.subtitle}</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {/* Language Selection Radio Buttons */}
                    <div className="flex items-center gap-2 bg-neutral-800/50 border border-white/10 rounded-lg p-1">
                        <button
                            onClick={() => changeLanguage('en')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${language === 'en'
                                    ? 'bg-white text-black shadow-lg'
                                    : 'text-neutral-400 hover:text-white'
                                }`}
                        >
                            English
                        </button>
                        <button
                            onClick={() => changeLanguage('hi')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${language === 'hi'
                                    ? 'bg-white text-black shadow-lg'
                                    : 'text-neutral-400 hover:text-white'
                                }`}
                        >
                            हिंदी
                        </button>
                        <button
                            onClick={() => changeLanguage('hi-romanized')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${language === 'hi-romanized'
                                    ? 'bg-white text-black shadow-lg'
                                    : 'text-neutral-400 hover:text-white'
                                }`}
                        >
                            Hindi (Roman)
                        </button>
                    </div>
                    <Link to="/" className="text-sm font-medium text-neutral-500 hover:text-white transition-colors flex items-center gap-2 group">
                        <span className="hidden sm:inline">Exit</span>
                        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                            <FaArrowLeft className="w-3 h-3 group-hover:-translate-x-0.5 transition-transform" />
                        </div>
                    </Link>
                </div>
            </header>

            {/* Chat Area */}
            <main className="flex-1 relative z-0 overflow-y-auto p-4 md:p-8 flex flex-col custom-scrollbar">
                {messages.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-center space-y-8 min-h-[50vh]">
                        <div className="w-24 h-24 mx-auto rounded-3xl bg-gradient-to-br from-neutral-800 to-neutral-900 border border-white/5 flex items-center justify-center shadow-2xl shadow-black/50">
                            <FaComments className="w-10 h-10 text-white/20" />
                        </div>

                        <div className="space-y-4">
                            <h2 className="text-3xl font-bold text-white tracking-tight">{t.introTitle}</h2>
                            <p className="text-neutral-400 max-w-lg mx-auto leading-relaxed">
                                {t.introText}
                            </p>
                        </div>

                        <div className="flex flex-wrap justify-center gap-3">
                            <button onClick={() => setInput(t.q1)} className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5">
                                {t.q1}
                            </button>
                            <button onClick={() => setInput(t.q2)} className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5">
                                {t.q2}
                            </button>
                            <button onClick={() => setInput(t.q3)} className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5">
                                {t.q3}
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="max-w-3xl w-full mx-auto space-y-6 pb-4">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                {msg.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-full bg-neutral-800 flex items-center justify-center border border-white/10 flex-shrink-0">
                                        <FaRobot className="w-4 h-4 text-green-500" />
                                    </div>
                                )}

                                <div className={`max-w-[80%] space-y-2`}>
                                    <div className={`p-4 rounded-2xl ${msg.role === 'user'
                                        ? 'bg-white text-black'
                                        : 'bg-neutral-900 border border-white/10 text-neutral-200'
                                        }`}>
                                        {/* Show tag badge for user messages */}
                                        {msg.role === 'user' && msg.tag && (
                                            <div className="mb-2">
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-black/10 text-[10px] font-bold uppercase tracking-wider">
                                                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                                                    {legalTags.find(t => t.id === msg.tag)?.label || msg.tag}
                                                </span>
                                            </div>
                                        )}
                                        <div className={`text-sm leading-relaxed max-w-none ${msg.role === 'assistant'
                                            ? 'prose prose-invert prose-sm prose-p:leading-relaxed prose-pre:p-0 prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-hr:my-2'
                                            : 'whitespace-pre-wrap'
                                            }`}>
                                            {msg.role === 'assistant' ? (
                                                <ReactMarkdown
                                                    components={{
                                                        code: ({ node, inline, className, children, ...props }) => (
                                                            inline
                                                                ? <code className="bg-white/10 rounded px-1 py-0.5 text-xs font-mono" {...props}>{children}</code>
                                                                : <pre className="bg-black/30 rounded-lg p-3 overflow-x-auto my-2 border border-white/5"><code className="text-xs font-mono" {...props}>{children}</code></pre>
                                                        ),
                                                        ul: ({ node, ...props }) => <ul className="list-disc pl-4 my-1 space-y-0.5" {...props} />,
                                                        ol: ({ node, ...props }) => <ol className="list-decimal pl-4 my-1 space-y-0.5" {...props} />
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
                                        <div className="mt-2 pl-2">
                                            <p className="text-[10px] uppercase font-bold text-neutral-500 mb-2">{t.sources}</p>
                                            <div className="flex flex-wrap gap-2">
                                                {msg.sources.map((source, sIdx) => (
                                                    <a
                                                        key={sIdx}
                                                        href={source.driveUrl || '#'}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="flex items-center gap-2 bg-neutral-800/50 hover:bg-neutral-800 border border-white/5 hover:border-white/20 rounded-lg p-2 transition-all group no-underline"
                                                    >
                                                        {source.thumbnail ? (
                                                            <img
                                                                src={source.thumbnail}
                                                                alt={source.filename}
                                                                className="w-8 h-8 rounded object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                                                                onError={(e) => {
                                                                    // Fallback to document icon if image fails to load
                                                                    e.target.style.display = 'none';
                                                                    e.target.nextElementSibling.style.display = 'flex';
                                                                }}
                                                            />
                                                        ) : null}
                                                        {/* Fallback icon (hidden by default, shown on image error) */}
                                                        <div
                                                            className="w-8 h-8 rounded bg-neutral-700 flex items-center justify-center text-xs font-bold text-neutral-400"
                                                            style={{ display: source.thumbnail ? 'none' : 'flex' }}
                                                        >
                                                            📄
                                                        </div>
                                                        <span className="text-xs text-neutral-400 group-hover:text-white truncate max-w-[150px]">
                                                            {source.filename}
                                                        </span>
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {msg.role === 'user' && (
                                    <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center flex-shrink-0">
                                        <FaUser className="w-4 h-4 text-black" />
                                    </div>
                                )}
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex gap-4">
                                <div className="w-8 h-8 rounded-full bg-neutral-800 flex items-center justify-center border border-white/10 flex-shrink-0">
                                    <FaRobot className="w-4 h-4 text-green-500" />
                                </div>
                                <div className="p-4 rounded-2xl bg-neutral-900 border border-white/10 text-neutral-400 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse delay-75"></span>
                                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse delay-150"></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </main>

            {/* Input Area */}
            <footer className="relative z-20 p-2">
                <div className="max-w-3xl mx-auto relative">
                    {/* Tag Selection */}
                    <div className="mb-3 px-2">
                        <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-[10px] uppercase font-bold text-neutral-500 tracking-wider">
                                Filter by:
                            </span>
                            {legalTags.map(tag => (
                                <button
                                    key={tag.id}
                                    onClick={() => setSelectedTag(selectedTag === tag.id ? null : tag.id)}
                                    className={`group relative px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${selectedTag === tag.id
                                        ? 'bg-white text-black shadow-lg shadow-white/20 scale-105'
                                        : 'bg-neutral-800/50 text-neutral-400 hover:bg-neutral-800 hover:text-white border border-white/5 hover:border-white/10'
                                        }`}
                                    title={tag.fullName}
                                >
                                    {tag.label}
                                    {selectedTag === tag.id && (
                                        <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                    )}
                                </button>
                            ))}
                            {selectedTag && (
                                <button
                                    onClick={() => setSelectedTag(null)}
                                    className="text-[10px] text-neutral-500 hover:text-white underline transition-colors"
                                >
                                    Clear
                                </button>
                            )}
                        </div>
                    </div>

                    <form onSubmit={handleSendMessage} className="relative flex items-center gap-3 bg-transparent rounded-2xl p-2 border border-white/10 shadow-xl focus-within:border-white/20 transition-colors">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={isLoading ? t.loading : t.placeholder}
                            disabled={isLoading}
                            className="flex-1 bg-transparent border-none outline-none text-white px-4 py-3 placeholder:text-neutral-600 font-medium disabled:opacity-50"
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="w-12 h-12 bg-white text-black rounded-xl flex items-center justify-center hover:bg-neutral-200 transition-colors shadow-lg shadow-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <FaPaperPlane className="w-4 h-4" />
                        </button>
                    </form>
                </div>
            </footer>
        </div>
    )
}
