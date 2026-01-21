import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaMicrophone, FaHistory, FaTimes, FaFileAlt, FaBriefcase, FaBalanceScale, FaUserAstronaut, FaArrowLeft } from 'react-icons/fa';
import { HiBars3 } from "react-icons/hi2";
import { io } from 'socket.io-client';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { useSession } from '../context/SessionContext';
import { motion, AnimatePresence } from 'framer-motion';
import SessionSidebar from '../components/SessionSidebar';
import UserProfile from '../components/UserProfile';

export default function Kira() {
    const navigate = useNavigate();
    // Session State
    const [isActive, setIsActive] = useState(false);
    const [status, setStatus] = useState('idle'); // idle, listening, processing, speaking
    const [transcript, setTranscript] = useState('');
    const [messages, setMessages] = useState([]);
    const [currentSources, setCurrentSources] = useState([]); // Buffer for current response sources
    const [showLog, setShowLog] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Refs
    const socketRef = useRef(null);
    const recognitionRef = useRef(null);
    const synthRef = useRef(window.speechSynthesis);
    const sentenceBufferRef = useRef("");
    const isInterruptedRef = useRef(false);
    const firstTokenReceivedRef = useRef(false);
    const statusRef = useRef(status); // Ref to track status without re-running effects
    const isActiveRef = useRef(isActive); // Ref for precise On/Off control in callbacks

    const { language } = useLanguage();
    const { user } = useAuth();
    const {
        currentSession,
        createSession,
        loadChatHistory,
        saveChatMessage
    } = useSession();

    // Sync Refs
    useEffect(() => { statusRef.current = status; }, [status]);
    useEffect(() => { isActiveRef.current = isActive; }, [isActive]);

    // Load Chat History when session changes
    useEffect(() => {
        const fetchHistory = async () => {
            if (currentSession?.id) {
                const history = await loadChatHistory(currentSession.id);
                // Convert to UI format
                const formattedHistory = history.map(msg => ({
                    role: msg.role,
                    content: msg.content,
                    sources: msg.sources || []
                }));
                setMessages(formattedHistory);
            } else {
                setMessages([]);
            }
        };
        fetchHistory();
    }, [currentSession]);

    // =================================================================================
    // 1. SOCKET CONNECTION
    // =================================================================================
    useEffect(() => {
        socketRef.current = io('http://127.0.0.1:5000', {
            transports: ['polling'],
            upgrade: false,
            reconnection: true,
            reconnectionAttempts: 10,
            timeout: 60000,
            pingTimeout: 60000,
            pingInterval: 25000
        });
        const socket = socketRef.current;

        socket.on('response_chunk', (chunk) => {
            if (isInterruptedRef.current) return;
            if (!firstTokenReceivedRef.current) {
                setStatus('speaking');
                firstTokenReceivedRef.current = true;
            }
            setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg && lastMsg.role === 'assistant') {
                    // Update content
                    return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + chunk }];
                } else {
                    return [...prev, { role: 'assistant', content: chunk, sources: [] }];
                }
            });
            handleTTSStreaming(chunk);
        });

        socket.on('sources', (sources) => {
            setCurrentSources(sources);
            setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg) {
                    return [...prev.slice(0, -1), { ...lastMsg, sources: sources }];
                }
                return prev;
            });
        });

        socket.on('response_complete', () => {
            if (sentenceBufferRef.current.trim() && !isInterruptedRef.current) {
                speakText(sentenceBufferRef.current);
                sentenceBufferRef.current = "";
            }
        });

        return () => {
            socket.disconnect();
            synthRef.current.cancel();
            if (recognitionRef.current) recognitionRef.current.stop();
        };
    }, []);

    // =================================================================================
    // 2. SPEECH RECOGNITION (Creation & Event Handling)
    // =================================================================================
    useEffect(() => {
        if (!window.SpeechRecognition && !window.webkitSpeechRecognition) return;
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = language === 'hi' ? 'hi-IN' : 'en-US';

        recognition.onresult = (event) => {
            let interim = '';
            let final = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) final += event.results[i][0].transcript;
                else interim += event.results[i][0].transcript;
            }

            const currentStatus = statusRef.current;
            if ((currentStatus === 'speaking' || currentStatus === 'processing') &&
                (final.trim().length > 0 || interim.trim().length > 3)) {
                handleInterruption();
            }

            setTranscript(interim || final);
            if (final.trim()) {
                handleUserMessage(final);
                setTranscript('');
            }
        };

        recognition.onerror = (event) => {
            if (event.error === 'aborted') return;
            console.error("Speech Recognition Error:", event.error);
            if (event.error === 'not-allowed') {
                setIsActive(false);
                setStatus('idle');
            }
        };

        recognition.onend = () => {
            if (isActiveRef.current) {
                setTimeout(() => {
                    if (isActiveRef.current && recognitionRef.current) {
                        try { recognitionRef.current.start(); } catch (e) { }
                    }
                }, 300);
            } else {
                setStatus('idle');
            }
        };

        recognitionRef.current = recognition;

        return () => {
            recognition.onend = null;
            recognition.stop();
        };
    }, [language]);

    // =================================================================================
    // 3. SESSION CONTROL (Start/Stop)
    // =================================================================================
    useEffect(() => {
        if (isActive) {
            setStatus('listening');
            try { recognitionRef.current?.start(); } catch (e) { }
        } else {
            setStatus('idle');
            recognitionRef.current?.stop();
        }
    }, [isActive]);

    const toggleSession = () => {
        setIsActive(!isActive);
    };

    // =================================================================================
    // 4. SPEECH & LOGIC
    // =================================================================================
    const handleTTSStreaming = (textChunk) => {
        sentenceBufferRef.current += textChunk;

        const buffer = sentenceBufferRef.current;
        const words = buffer.split(/\s+/).filter(w => w.length > 0);
        const hasSentenceEnd = /[.!?।]\s*$/.test(buffer);
        const hasPhraseEnd = /[,;:]\s*$/.test(buffer);

        let shouldSpeak = false;
        let keepInBuffer = 0;

        if (hasSentenceEnd) {
            shouldSpeak = true;
            keepInBuffer = 0;
        } else if (hasPhraseEnd && words.length >= 4) {
            shouldSpeak = true;
            keepInBuffer = 0;
        } else if (words.length >= 8) {
            shouldSpeak = true;
            keepInBuffer = 2;
        } else if (words.length >= 6 && /[,;:]/.test(buffer)) {
            shouldSpeak = true;
            keepInBuffer = 1;
        }

        if (shouldSpeak && words.length > keepInBuffer) {
            const wordsToSpeak = words.slice(0, words.length - keepInBuffer);
            const wordsToKeep = words.slice(words.length - keepInBuffer);
            const textToSpeak = wordsToSpeak.join(' ').trim();

            if (textToSpeak.length > 0) {
                speakText(textToSpeak);
            }
            sentenceBufferRef.current = wordsToKeep.join(' ');
        }
    };

    const speakText = (text) => {
        if (isInterruptedRef.current || !text) return;
        const utterance = new SpeechSynthesisUtterance(text);
        const voices = synthRef.current.getVoices();

        let selectedVoice = voices.find(v => (v.lang === 'en-IN' || v.lang === 'en_IN') && (v.name.includes('Female') || v.name.includes('female'))) ||
            voices.find(v => v.lang === 'en-IN' || v.lang === 'en_IN') ||
            voices.find(v => v.name.includes('Female')) ||
            voices.find(v => v.lang === 'en-US');

        if (selectedVoice) utterance.voice = selectedVoice;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        synthRef.current.speak(utterance);
    };

    const handleInterruption = () => {
        if (isInterruptedRef.current) return;
        isInterruptedRef.current = true;
        synthRef.current.cancel();
        sentenceBufferRef.current = "";
        if (socketRef.current) socketRef.current.emit('stop_generation');
        setTimeout(() => { isInterruptedRef.current = false; }, 200);
    };

    const getFillerPhrase = () => {
        const fillers = [
            "Let me review that for you.",
            "Checking our legal database.",
            "One moment, analyzing your query.",
            "Let me look into that.",
            "Searching relevant case law.",
        ];
        return fillers[Math.floor(Math.random() * fillers.length)];
    };

    const handleUserMessage = async (msg) => {
        isInterruptedRef.current = false;
        firstTokenReceivedRef.current = false;
        setCurrentSources([]);

        // Create session if it doesn't exist
        let activeSessionId = currentSession?.id;
        if (!activeSessionId) {
            const newSession = await createSession(msg.slice(0, 30) + "...", 'kira');
            if (newSession) activeSessionId = newSession.id;
        }

        setMessages(prev => [...prev, { role: 'user', content: msg }]);
        setStatus('processing');

        // Save User Message
        if (activeSessionId) {
            await saveChatMessage(activeSessionId, 'user', msg, [], language);
        }

        const fillerPhrase = getFillerPhrase();
        speakText(fillerPhrase);

        const chatHistory = [...messages, { role: 'user', content: msg }];
        socketRef.current.emit('send_message', {
            message: msg,
            history: chatHistory,
            language: language,
            persona: 'kira',
            sessionId: activeSessionId,
            userId: user ? user.uid : 'guest'
        });
    };

    // Initial check for mobile
    useEffect(() => {
        if (window.innerWidth < 768) {
            setIsSidebarOpen(false);
        } else {
            setIsSidebarOpen(true);
        }
    }, []);

    // ... (rest of useEffects)

    return (
        <div className="h-screen bg-neutral-900 text-neutral-100 font-sans flex flex-col md:flex-row overflow-hidden selection:bg-indigo-500/30">

            {/* Sidebar */}
            <div className="relative z-20">
                <SessionSidebar
                    isOpen={isSidebarOpen}
                    onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                    persona="kira"
                />
            </div>

            <div className={`flex-1 flex flex-col relative h-full transition-all duration-300 ${isSidebarOpen ? 'md:ml-80' : ''}`}>
                {/* Elegant Background */}
                <div className="absolute inset-0 bg-neutral-900 z-0">
                    <div className="absolute top-0 right-0 w-1/2 h-full bg-neutral-800/10 skew-x-12 transform origin-top"></div>
                    <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-black/50 to-transparent"></div>
                </div>

                {/* Header */}
                <header className="relative z-50 px-8 py-6 flex justify-between items-center border-b border-white/5 bg-neutral-900/50 backdrop-blur-sm">
                    <div className="flex items-center gap-4">
                        <motion.button
                            whileHover={{ scale: 1.1, x: -3 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => navigate('/dashboard')}
                            className="hidden md:flex p-2 bg-white/5 hover:bg-white/10 rounded-lg text-neutral-400 hover:text-white transition-all mr-2"
                        >
                            <FaArrowLeft />
                        </motion.button>
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="md:hidden p-2 -ml-2 text-white/70 hover:text-white"
                        >
                            <HiBars3 className="w-6 h-6" />
                        </button>

                        <Link to="/" className="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-colors">
                            <FaTimes className="text-neutral-400" />
                        </Link>
                        <div>
                            <h1 className="text-lg font-serif tracking-wide text-white">Kira</h1>
                            <p className="text-xs text-neutral-500 uppercase tracking-widest font-medium">Legal Advisor</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        {user ? (
                            <UserProfile />
                        ) : (
                            <Link to="/login" className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-bold transition-all">
                                Sign In
                            </Link>
                        )}
                        <div className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wider transition-colors border ${isActive ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' : 'bg-neutral-800 border-neutral-700 text-neutral-500'}`}>
                            {isActive ? (status === 'speaking' ? 'SPEAKING' : status === 'listening' ? 'LISTENING' : 'CONNECTED') : 'DISCONNECTED'}
                        </div>
                        <button onClick={() => setShowLog(!showLog)} className="p-2 text-neutral-400 hover:text-white transition-colors">
                            <FaHistory />
                        </button>
                    </div>
                </header>

                {/* Main Workspace */}
                <main className="flex-1 relative z-10 flex flex-col md:flex-row items-stretch overflow-hidden">
                    {/* LEFT: Interaction Zone */}
                    <div className="flex-1 flex flex-col items-center justify-center p-8 relative">
                        {/* Transcript / Prompter */}
                        <div className="flex-1 w-full max-w-3xl flex flex-col justify-end pb-40 text-center">
                            <AnimatePresence mode="wait">
                                {transcript ? (
                                    <motion.p
                                        key="user-input"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="text-3xl md:text-5xl font-light text-white leading-tight"
                                    >
                                        "{transcript}"
                                    </motion.p>
                                ) : status === 'processing' ? (
                                    <motion.div
                                        key="ai-thinking"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="flex flex-col items-center gap-6"
                                    >
                                        <motion.div
                                            animate={{ scale: [1, 1.1, 1] }}
                                            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                                        >
                                            <FaBalanceScale className="w-12 h-12 text-indigo-400 opacity-80" />
                                        </motion.div>
                                        <p className="text-neutral-400 font-serif italic text-lg">Analyzing legal precedents...</p>
                                    </motion.div>
                                ) : status === 'speaking' ? (
                                    <motion.div
                                        key="ai-vis"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="flex flex-col items-center gap-6"
                                    >
                                        <div className="flex items-center gap-1.5 h-16">
                                            {[...Array(12)].map((_, i) => (
                                                <motion.div
                                                    key={i}
                                                    className="w-1.5 bg-indigo-400 rounded-full"
                                                    animate={{ height: [10, 60, 10] }}
                                                    transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.05, ease: "easeInOut" }}
                                                />
                                            ))}
                                        </div>
                                        <p className="text-neutral-400 font-serif italic text-lg">Advisor is speaking...</p>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="idle-prompt"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 0.5 }}
                                        className="text-neutral-500"
                                    >
                                        {isActive ? "I am listening. State your inquiry." : "Press the microphone to begin consultation."}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Control Button */}
                        <div className="absolute bottom-12 left-0 right-0 flex justify-center">
                            <button
                                onClick={toggleSession}
                                className={`group relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 outline-none ${isActive
                                    ? 'bg-white text-black shadow-2xl shadow-white/20 scale-110'
                                    : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:border-neutral-500'
                                    }`}
                            >
                                {isActive && (
                                    <div className="absolute -inset-4 border border-white/20 rounded-full animate-ping opacity-40"></div>
                                )}
                                {isActive ? (
                                    status === 'processing' ? <FaBalanceScale className="w-8 h-8 animate-pulse" /> :
                                        <div className="w-8 h-8 rounded-full bg-red-500 animate-pulse shadow-inner"></div>
                                ) : (
                                    <FaMicrophone className="w-6 h-6" />
                                )}
                            </button>
                        </div>
                    </div>

                    {/* RIGHT: Reference Panel (Dynamic) */}
                    <AnimatePresence>
                        {(status === 'speaking' || currentSources.length > 0) && (
                            <motion.div
                                initial={{ x: 100, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: 100, opacity: 0 }}
                                className="w-full md:w-80 bg-neutral-800/50 backdrop-blur-md border-l border-white/5 p-6 flex flex-col gap-6"
                            >
                                <div className="flex items-center gap-2 text-indigo-400 mb-2">
                                    <FaFileAlt />
                                    <span className="text-xs font-bold uppercase tracking-widest">Active References</span>
                                </div>

                                <div className="space-y-4">
                                    {currentSources.length > 0 ? currentSources.map((source, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.1 }}
                                            className="bg-neutral-900 border border-white/10 p-4 rounded-lg hover:border-indigo-500/50 transition-colors group cursor-pointer"
                                            onClick={() => window.open(source.driveUrl, '_blank')}
                                        >
                                            <div className="flex justify-between items-start">
                                                <h4 className="text-sm font-medium text-neutral-200 line-clamp-2 group-hover:text-white">
                                                    {source.filename}
                                                </h4>
                                                <FaBriefcase className="text-neutral-600 text-xs mt-1" />
                                            </div>
                                            <div className="mt-2 text-[10px] text-neutral-500 uppercase tracking-wider">
                                                Relevant Exhibit
                                            </div>
                                        </motion.div>
                                    )) : (
                                        <div className="h-32 flex items-center justify-center text-neutral-600 text-xs italic">
                                            Searching legal database...
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </main>
            </div>

            {/* HISTORY LOG (Slide Over) */}
            <AnimatePresence>
                {showLog && (
                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        className="fixed inset-y-0 right-0 w-full md:w-[500px] bg-white text-black z-[60] shadow-2xl flex flex-col"
                    >
                        <div className="p-6 border-b border-neutral-100 flex justify-between items-center bg-neutral-50">
                            <h2 className="font-serif text-xl font-bold text-neutral-800">Consultation Transcript</h2>
                            <button onClick={() => setShowLog(false)}><FaTimes className="text-neutral-400 hover:text-black" /></button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-white">
                            {messages.map((msg, i) => (
                                <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-2">
                                        {msg.role === 'user' ? 'Client Inquiry' : 'Legal Advisor'}
                                    </span>
                                    <div className={`text-base leading-relaxed p-6 rounded-2xl ${msg.role === 'user'
                                        ? 'bg-neutral-100 text-neutral-800 rounded-br-none'
                                        : 'bg-indigo-50 border border-indigo-100 text-neutral-800 rounded-bl-none'
                                        }`}>
                                        {msg.content}
                                    </div>
                                    {msg.sources && msg.sources.length > 0 && (
                                        <div className="mt-2 flex gap-2 overflow-x-auto max-w-full pb-2">
                                            {msg.sources.map((s, idx) => (
                                                <span key={idx} className="flex-shrink-0 text-[10px] bg-white border border-neutral-200 px-2 py-1 rounded text-neutral-500">
                                                    Ref: {s.filename.substring(0, 15)}...
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

        </div>
    );
}
