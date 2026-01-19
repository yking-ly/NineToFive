import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaUserAstronaut, FaPaperPlane, FaArrowLeft, FaComments, FaRobot, FaUser, FaFilter } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';

export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [selectedCollections, setSelectedCollections] = useState(["ipc", "bns", "mapping"]); // All selected by default
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const toggleCollection = (collection) => {
        setSelectedCollections(prev => {
            if (prev.includes(collection)) {
                // Don't allow deselecting all
                if (prev.length === 1) return prev;
                return prev.filter(c => c !== collection);
            } else {
                return [...prev, collection];
            }
        });
    };

    const handleSend = async (text = null) => {
        const query = text || input;
        if (!query.trim()) return;

        // Add User Message
        const userMsg = { role: 'user', content: query };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch('http://127.0.0.1:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    collections: selectedCollections  // Pass selected filters
                }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                const aiMsg = {
                    role: 'ai',
                    content: data.answer,
                    duration: data.duration_seconds,
                    collections: selectedCollections // Track which collections were searched
                };
                setMessages(prev => [...prev, aiMsg]);
            } else {
                const errorMsg = { role: 'ai', content: "⚠️ Sorry, I encountered an error retrieving the information." };
                setMessages(prev => [...prev, errorMsg]);
            }

        } catch (error) {
            console.error("Chat Error:", error);
            const errorMsg = { role: 'ai', content: "⚠️ Connection Failed: Make sure the backend server is running." };
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

    return (
        <div className="min-h-screen bg-neutral-950 text-white font-sans flex flex-col relative overflow-hidden">

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
                        <h1 className="text-lg font-bold text-white tracking-tight">AI Legal Assistant</h1>
                        <div className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]"></span>
                            <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-semibold">Online • RAG Active</span>
                        </div>
                    </div>
                </div>

                <Link to="/" className="text-sm font-medium text-neutral-500 hover:text-white transition-colors flex items-center gap-2 group">
                    <span className="hidden sm:inline">Exit Chat</span>
                    <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                        <FaArrowLeft className="w-3 h-3 group-hover:-translate-x-0.5 transition-transform" />
                    </div>
                </Link>
            </header>

            {/* Chat Area */}
            <main className="flex-1 relative z-10 overflow-y-auto p-4 md:p-8 flex flex-col">
                <div className="max-w-3xl w-full mx-auto flex flex-col flex-1">

                    {messages.length === 0 ? (
                        /* Empty State */
                        <div className="flex-1 flex flex-col items-center justify-center space-y-8 opacity-0 animate-[fadeIn_0.5s_ease-out_forwards]">
                            <div className="w-24 h-24 mx-auto rounded-3xl bg-gradient-to-br from-neutral-800 to-neutral-900 border border-white/5 flex items-center justify-center shadow-2xl shadow-black/50">
                                <FaComments className="w-10 h-10 text-white/20" />
                            </div>

                            <div className="space-y-4 text-center">
                                <h2 className="text-3xl font-bold text-white tracking-tight">How can I help you today?</h2>
                                <p className="text-neutral-400 max-w-lg mx-auto leading-relaxed">
                                    I am trained on the Indian Penal Code (IPC), Bhartiya Nyaya Sanhita (BNS), and mapping tables. Ask me about sections, punishments, or changes.
                                </p>
                            </div>

                            <div className="flex flex-wrap justify-center gap-3">
                                <button onClick={() => handleSend("What is Section 302 related to?")} className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5 cursor-pointer">
                                    What is Section 302?
                                </button>
                                <button onClick={() => handleSend("What is the punishment for mob lynching in BNS?")} className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5 cursor-pointer">
                                    Punishment for mob lynching
                                </button>
                                <button onClick={() => handleSend("Difference between IPC and BNS definitions")} className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5 cursor-pointer">
                                    Compare IPC vs BNS
                                </button>
                            </div>
                        </div>
                    ) : (
                        /* Message List */
                        <div className="space-y-6 pb-4">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'} animate-[slideUp_0.3s_ease-out]`}>
                                    {/* Avatar */}
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-white text-neutral-900' : 'bg-neutral-800 border border-white/10 text-green-400'}`}>
                                        {msg.role === 'user' ? <FaUser className="w-3 h-3" /> : <FaRobot className="w-4 h-4" />}
                                    </div>

                                    {/* Bubble */}
                                    <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user' ? 'bg-white text-neutral-900 rounded-tr-sm' : 'glass border border-white/10 text-neutral-200 rounded-tl-sm'}`}>
                                        {msg.role === 'user' ? (
                                            msg.content
                                        ) : (
                                            <div className="prose prose-invert prose-sm max-w-none">
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                {msg.duration && (
                                                    <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-neutral-500 font-mono">
                                                        Generated in {msg.duration}s
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="flex gap-4 animate-pulse">
                                    <div className="w-8 h-8 rounded-full bg-neutral-800 border border-white/10 flex items-center justify-center text-green-400">
                                        <FaRobot className="w-4 h-4" />
                                    </div>
                                    <div className="glass border border-white/10 rounded-2xl p-4 rounded-tl-sm text-neutral-400 text-sm">
                                        <span className="inline-block animate-bounce">●</span>
                                        <span className="inline-block animate-bounce delay-100 mx-1">●</span>
                                        <span className="inline-block animate-bounce delay-200">●</span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>
            </main>

            {/* Input Area */}
            <footer className="relative z-20 p-4 md:p-6 bg-neutral-950/80 backdrop-blur-xl border-t border-white/5">
                <div className="max-w-3xl mx-auto">
                    {/* Collection Filter Toggles */}
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-semibold flex items-center gap-1">
                            <FaFilter className="w-2.5 h-2.5" /> Search in:
                        </span>
                        {[
                            { id: 'ipc', label: 'IPC', color: 'from-orange-500 to-red-500' },
                            { id: 'bns', label: 'BNS', color: 'from-blue-500 to-indigo-500' },
                            { id: 'mapping', label: 'Mapping', color: 'from-green-500 to-emerald-500' }
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
                                placeholder="Type a message regarding your legal queries..."
                                disabled={isLoading}
                                className="flex-1 bg-transparent border-none outline-none text-white px-4 py-3 placeholder:text-neutral-600 font-medium disabled:opacity-50"
                            />
                            <button
                                onClick={() => handleSend()}
                                disabled={!input.trim() || isLoading}
                                className="w-12 h-12 bg-white text-black rounded-xl flex items-center justify-center hover:bg-neutral-200 transition-colors shadow-lg shadow-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? <span className="animate-spin text-lg">↻</span> : <FaPaperPlane className="w-4 h-4" />}
                            </button>
                        </div>
                    </div>
                    <p className="text-center text-[10px] text-neutral-600 mt-4 uppercase tracking-widest font-medium">
                        AI generated responses may vary. Consult a lawyer for serious advice.
                    </p>
                </div>
            </footer>
        </div>
    )
}
