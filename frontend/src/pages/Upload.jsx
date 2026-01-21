import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import TopBar from '../components/TopBar';
import { FaCloudUploadAlt, FaFileAlt, FaArrowLeft, FaCheckCircle, FaExclamationCircle, FaSpinner, FaEye, FaAlignLeft, FaShieldAlt } from 'react-icons/fa';
import { getApiUrl } from '../utils/apiConfig';
import { useLanguage } from '../context/LanguageContext';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import io from 'socket.io-client';

export default function Upload() {
    const [uploading, setUploading] = useState(false);
    const [status, setStatus] = useState(null); // 'success' | 'error' | null
    const [message, setMessage] = useState('');
    const [uploadedData, setUploadedData] = useState(null);
    const [viewMode, setViewMode] = useState(false); // Toggle full view
    const [streamingSummary, setStreamingSummary] = useState(''); // Streaming summary text
    const [summaryComplete, setSummaryComplete] = useState(false); // Summary generation complete
    const [generatingSummary, setGeneratingSummary] = useState(false); // Summary loading state
    const [summaryLanguage, setSummaryLanguage] = useState('en'); // 'en' or 'hi' for summary
    const [translatedSummary, setTranslatedSummary] = useState(''); // Hindi translated summary
    const [isTranslating, setIsTranslating] = useState(false); // Translation in progress
    const [references, setReferences] = useState([]); // References used to draft the summary
    const [searchStatus, setSearchStatus] = useState(null); // Real-time processing status
    const fileInputRef = useRef(null);
    const socketRef = useRef(null);

    // Global  Language Context
    const { t, language, changeLanguage } = useLanguage();

    const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB

    // Socket connection setup
    useEffect(() => {
        const baseUrl = getApiUrl();
        socketRef.current = io(baseUrl, {
            transports: ['polling'],
            reconnection: true
        });

        // Listen for realtime status
        socketRef.current.on('search_status', (data) => {
            setSearchStatus(data.message);
        });

        // Listen for summary chunks
        socketRef.current.on('summary_chunk', (data) => {
            setStreamingSummary((prev) => prev + data.chunk);
        });

        // Summary generation complete
        socketRef.current.on('summary_complete', (data) => {
            setSummaryComplete(true);
            setGeneratingSummary(false);
            setSearchStatus(null);
            if (data.summary_hi) {
                setTranslatedSummary(data.summary_hi);
            }
            if (data.references) {
                setReferences(data.references);
            }
        });

        // Translation status updates
        socketRef.current.on('translation_status', (data) => {
            if (data.status === 'translating') {
                setIsTranslating(true);
            } else if (data.status === 'failed') {
                setIsTranslating(false);
                console.error('Translation failed:', data.error);
            }
        });

        socketRef.current.on('translation_complete', (data) => {
            setTranslatedSummary(data.translated);
            setIsTranslating(false);
        });

        // Handle errors
        socketRef.current.on('summary_error', (data) => {
            console.error('Summary generation error:', data.error);
            setStreamingSummary('Failed to generate summary. ' + data.error);
            setSummaryComplete(true);
            setGeneratingSummary(false);
            setSearchStatus(null);
        });

        return () => {
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
        };
    }, []);

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) processFile(file);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const file = e.dataTransfer.files[0];
        if (file) processFile(file);
    };

    const processFile = async (file) => {
        if (file.size > MAX_FILE_SIZE) {
            setStatus('error');
            setMessage('File is too large. Maximum size is 15MB.');
            return;
        }

        setUploading(true);
        setStatus(null);
        setMessage(t.processing);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const baseUrl = getApiUrl();
            const response = await fetch(`${baseUrl}/api/upload`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                setStatus('success');
                setMessage('File uploaded successfully!');
                setUploadedData(data.data);

                // Immediately switch to view mode
                setViewMode(true);
                setGeneratingSummary(true);
                setStreamingSummary('');
                setSummaryComplete(false);
                setSearchStatus("Initializing...");

                // Trigger streaming summary generation via WebSocket
                setTimeout(() => {
                    socketRef.current.emit('generate_summary', {
                        filename: data.data.filename,
                        temp_path: data.temp_path,
                        language: summaryLanguage  // Send selected language
                    });
                }, 500);
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
            setMessage(error.message || 'An error occurred during upload.');
        } finally {
            setUploading(false);
        }
    };

    const getPreviewUrl = (url) => {
        if (!url) return '';
        // Convert typical google drive view link to preview link
        return url.replace('/view?usp=drivesdk', '/preview').replace('/view', '/preview');
    };

    return (
        <div className="h-screen bg-[#030303] text-white font-sans overflow-hidden relative flex flex-col">

            {/* Dynamic Background */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-indigo-600/10 rounded-full blur-[150px] animate-pulse"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }}></div>
            </div>



            {/* Navbar */}
            <TopBar title="Document Analysis" subtitle="Upload & Analyze Legal Documents" transparent={true}>
                <div className="bg-neutral-900/50 p-1 rounded-xl border border-white/5 flex gap-1 backdrop-blur-md">
                    {['en', 'hi'].map((langKey) => (
                        <button
                            key={langKey}
                            onClick={() => changeLanguage(langKey)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${language === langKey
                                ? 'bg-white text-black shadow-sm'
                                : 'text-neutral-500 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            {langKey === 'en' ? 'EN' : 'हिंदी'}
                        </button>
                    ))}
                </div>

                {viewMode && (
                    <motion.button
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        onClick={() => {
                            setViewMode(false);
                            setStatus(null);
                            setUploadedData(null);
                            setStreamingSummary('');
                            setSummaryComplete(false);
                            setGeneratingSummary(false);
                            setSummaryLanguage('en');
                            setTranslatedSummary('');
                            setIsTranslating(false);
                            setReferences([]);
                            setSearchStatus(null);
                        }}
                        className="bg-white text-black px-5 py-2 rounded-xl text-sm font-bold shadow-lg hover:bg-neutral-200 transition-colors"
                    >
                        {t.uploadNew}
                    </motion.button>
                )}
            </TopBar>

            <div className={`relative z-10 container mx-auto px-6 lg:px-12 flex flex-col ${viewMode ? 'h-[calc(100vh-100px)] pb-6' : 'h-full justify-center items-center'}`}>

                <AnimatePresence mode="wait">
                    {!viewMode ? (
                        /* UPLOAD SECTION */
                        <motion.div
                            key="upload-section"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="w-full max-w-2xl text-center"
                        >
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                            >
                                <h1 className="text-5xl md:text-7xl font-black mb-6 tracking-tighter">
                                    <span className="text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40">{t.analyzeTitle1}</span> {t.analyzeTitle2}
                                </h1>
                                <p className="text-xl text-neutral-400 mb-12 font-light leading-relaxed max-w-lg mx-auto">
                                    {t.uploadDescription}
                                </p>
                            </motion.div>

                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileSelect}
                                className="hidden"
                                accept=".pdf,.docx,.txt"
                            />

                            <motion.div
                                onDragOver={handleDragOver}
                                onDrop={handleDrop}
                                onClick={() => !uploading && fileInputRef.current.click()}
                                className={`relative group cursor-pointer backdrop-blur-xl rounded-[2.5rem] p-12 md:p-16 border-2 border-dashed transition-all duration-500 overflow-hidden ${uploading ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-white/10 bg-neutral-900/40 hover:border-white/30 hover:bg-neutral-900/60'
                                    }`}
                                whileHover={!uploading ? { scale: 1.02, y: -5 } : {}}
                                whileTap={!uploading ? { scale: 0.98 } : {}}
                            >
                                {/* Glow Effect on Hover */}
                                <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

                                {uploading ? (
                                    <div className="flex flex-col items-center justify-center relative z-20">
                                        <div className="relative w-24 h-24 mb-8">
                                            <div className="absolute inset-0 rounded-full border-4 border-white/10"></div>
                                            <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
                                            <FaShieldAlt className="absolute inset-0 m-auto text-indigo-400 w-8 h-8 animate-pulse" />
                                        </div>
                                        <h3 className="text-2xl font-bold text-white mb-2">{t.processing}</h3>
                                        <p className="text-neutral-400 text-sm tracking-widest uppercase">{t.analyzing}</p>
                                    </div>
                                ) : status === 'error' ? (
                                    <div className="flex flex-col items-center justify-center relative z-20">
                                        <div className="w-24 h-24 rounded-full bg-red-500/10 flex items-center justify-center mb-6 border border-red-500/20 shadow-[0_0_30px_rgba(239,68,68,0.15)]">
                                            <FaExclamationCircle className="h-10 w-10 text-red-500" />
                                        </div>
                                        <h3 className="text-xl font-bold text-white mb-2">{t.uploadFailed}</h3>
                                        <p className="text-red-400 mb-8">{message}</p>
                                        <span className="text-xs text-neutral-500 uppercase tracking-widest border-b border-neutral-700 pb-1 group-hover:text-white group-hover:border-white transition-all">
                                            {t.clickRetry}
                                        </span>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center relative z-20">
                                        <motion.div
                                            className="w-24 h-24 rounded-[2rem] bg-gradient-to-br from-neutral-800 to-neutral-900 border border-white/5 flex items-center justify-center mb-8 shadow-2xl group-hover:shadow-[0_0_30px_rgba(255,255,255,0.1)] transition-all duration-500"
                                            whileHover={{ rotate: 10, scale: 1.1 }}
                                        >
                                            <FaCloudUploadAlt className="h-10 w-10 text-neutral-400 group-hover:text-white transition-colors duration-300" />
                                        </motion.div>

                                        <h3 className="text-3xl font-bold text-white mb-3 tracking-tight">{t.dropFiles}</h3>
                                        <p className="text-neutral-400 mb-10 text-lg">
                                            {t.or} <span className="text-white font-semibold border-b border-white/50 hover:border-white transition-colors">{t.browseFiles}</span> {t.fromDevice}
                                        </p>

                                        <div className="flex gap-3">
                                            {['PDF', 'DOCX', 'TXT'].map((ext) => (
                                                <span key={ext} className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-[10px] font-bold text-neutral-400 uppercase tracking-widest">
                                                    {ext}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </motion.div>

                            {status === 'success' && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="mt-6 p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 font-medium flex items-center justify-center gap-2"
                                >
                                    <FaCheckCircle /> {message}
                                </motion.div>
                            )}
                        </motion.div>
                    ) : (
                        /* SPLIT VIEW SECTION */
                        <motion.div
                            key="split-view"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.6 }}
                            className="w-full h-full flex flex-col md:flex-row gap-8 max-w-[1800px] mx-auto"
                        >
                            {/* LEFT: Document Preview */}
                            <motion.div
                                initial={{ x: -100, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ duration: 0.6, delay: 0.2 }}
                                className="flex-1 bg-neutral-900/50 backdrop-blur-2xl rounded-[2.5rem] border border-white/10 overflow-hidden flex flex-col relative group"
                            >
                                <div className="absolute inset-0 border border-white/5 rounded-[2.5rem] pointer-events-none z-20"></div>

                                <div className="p-6 border-b border-white/5 flex items-center gap-4 bg-white/[0.02]">
                                    <div className="w-10 h-10 rounded-xl bg-neutral-800 flex items-center justify-center">
                                        <FaEye className="text-neutral-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-bold text-white tracking-wide uppercase">{t.docPreview}</h3>
                                        <p className="text-xs text-neutral-500">{t.readOnlyMode}</p>
                                    </div>
                                </div>
                                <div className="flex-1 relative bg-[#1a1a1a]">
                                    {uploadedData?.driveUrl ? (
                                        <iframe
                                            src={getPreviewUrl(uploadedData.driveUrl)}
                                            className="w-full h-full absolute inset-0 border-none opacity-90 hover:opacity-100 transition-opacity"
                                            title="Document Preview"
                                            allow="autoplay"
                                        ></iframe>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-neutral-500">
                                            No preview available
                                        </div>
                                    )}
                                </div>
                            </motion.div>

                            {/* RIGHT: Summary */}
                            <motion.div
                                initial={{ x: 100, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ duration: 0.6, delay: 0.4 }}
                                className="w-full md:w-[600px] bg-neutral-900/50 backdrop-blur-2xl rounded-[2.5rem] border border-white/10 flex flex-col relative"
                            >
                                <div className="p-8 border-b border-white/5 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                                            <FaAlignLeft className="text-indigo-400 w-5 h-5" />
                                        </div>
                                        <div>
                                            <h2 className="text-2xl font-black text-white">{t.aiSummary}</h2>
                                            <p className="text-xs text-neutral-500 uppercase tracking-widest font-bold">
                                                {searchStatus || (generatingSummary ? 'Generating...' : isTranslating ? 'Translating...' : t.generatedBy)}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Language Toggle for Summary */}
                                    {summaryComplete && !generatingSummary && (
                                        <div className="bg-neutral-800/50 p-1 rounded-xl border border-white/5 flex gap-1">
                                            <button
                                                onClick={() => setSummaryLanguage('en')}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${summaryLanguage === 'en'
                                                    ? 'bg-white text-black shadow-sm'
                                                    : 'text-neutral-500 hover:text-white hover:bg-white/5'
                                                    }`}
                                            >
                                                EN
                                            </button>
                                            <button
                                                onClick={() => setSummaryLanguage('hi')}
                                                disabled={!translatedSummary && !isTranslating}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${summaryLanguage === 'hi'
                                                    ? 'bg-white text-black shadow-sm'
                                                    : translatedSummary || isTranslating
                                                        ? 'text-neutral-500 hover:text-white hover:bg-white/5'
                                                        : 'text-neutral-700 cursor-not-allowed'
                                                    }`}
                                            >
                                                हिं
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                                    {generatingSummary && !summaryComplete ? (
                                        /* Skeleton Loading */
                                        <div className="space-y-4">
                                            <Skeleton
                                                count={8}
                                                height={16}
                                                baseColor="#1f1f1f"
                                                highlightColor="#2a2a2a"
                                                borderRadius="0.5rem"
                                            />
                                        </div>
                                    ) : (
                                        /* Summary Content with Markdown */
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown
                                                components={{
                                                    h1: ({ node, ...props }) => <h1 className="text-2xl font-black text-white mb-4 mt-6 first:mt-0 tracking-tight" {...props} />,
                                                    h2: ({ node, ...props }) => <h2 className="text-lg font-bold text-white mb-3 mt-6 pb-2 border-b border-white/10 flex items-center gap-2" {...props} />,
                                                    h3: ({ node, ...props }) => <h3 className="text-base font-bold text-indigo-300 mb-2 mt-4" {...props} />,
                                                    h4: ({ node, ...props }) => <h4 className="text-sm font-bold text-neutral-200 mb-1 mt-3" {...props} />,
                                                    p: ({ node, ...props }) => <p className="mb-4 text-sm leading-7 text-neutral-300/90 font-medium" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="mb-4 pl-4 space-y-2" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-4 pl-2 space-y-2 text-sm text-neutral-300" {...props} />,
                                                    li: ({ node, ...props }) => (
                                                        <li className="text-sm leading-relaxed text-neutral-300 pl-2 relative before:content-['•'] before:absolute before:left-[-1rem] before:text-indigo-500 before:font-bold" {...props}>
                                                            <span className="relative -left-2">{props.children}</span>
                                                        </li>
                                                    ),
                                                    strong: ({ node, ...props }) => <strong className="font-bold text-white bg-indigo-500/10 px-1 rounded" {...props} />,
                                                    em: ({ node, ...props }) => <em className="italic text-indigo-300/80" {...props} />,
                                                    code: ({ node, inline, ...props }) =>
                                                        inline ?
                                                            <code className="bg-neutral-800 border border-white/10 px-1.5 py-0.5 rounded text-xs text-indigo-300 font-mono tracking-tight" {...props} /> :
                                                            <code className="block bg-neutral-900/50 border border-white/5 p-4 rounded-xl text-xs text-neutral-400 font-mono overflow-x-auto my-4 shadow-inner" {...props} />,
                                                    blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-indigo-500 bg-indigo-500/5 p-4 rounded-r-xl italic text-neutral-400 text-sm my-4" {...props} />
                                                }}
                                            >
                                                {summaryLanguage === 'hi' && translatedSummary
                                                    ? translatedSummary
                                                    : streamingSummary || uploadedData?.summary || "No summary available for this document."}
                                            </ReactMarkdown>
                                        </div>
                                    )}
                                </div>

                                <div className="p-6 border-t border-white/5 bg-neutral-900/30 backdrop-blur-md">
                                    {references.length > 0 && (
                                        <div>
                                            <p className="text-indigo-400 text-[10px] font-black uppercase tracking-widest mb-3 flex items-center gap-2">
                                                <FaShieldAlt className="w-3 h-3" /> References Used
                                            </p>
                                            <div className="flex overflow-x-auto gap-3 pb-2 scrollbar-none snap-x">
                                                {references.map((ref, index) => (
                                                    <span
                                                        key={index}
                                                        className="flex-shrink-0 snap-start whitespace-nowrap inline-flex items-center px-4 py-2.5 rounded-xl bg-neutral-800/50 border border-white/5 text-xs font-semibold text-neutral-300 hover:bg-neutral-800 hover:border-indigo-500/50 hover:text-white transition-all hover:shadow-[0_0_15px_rgba(99,102,241,0.15)] cursor-default select-none group"
                                                    >
                                                        <div className="w-6 h-6 rounded-lg bg-indigo-500/10 flex items-center justify-center mr-3 group-hover:bg-indigo-500/20 transition-colors">
                                                            <FaFileAlt className="text-indigo-400 group-hover:text-indigo-300" size={10} />
                                                        </div>
                                                        {ref}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}
