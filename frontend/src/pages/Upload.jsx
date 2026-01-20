import { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { FaCloudUploadAlt, FaFileAlt, FaArrowLeft, FaCheckCircle, FaExclamationCircle, FaSpinner, FaEye, FaAlignLeft } from 'react-icons/fa';
import { getApiUrl } from '../utils/apiConfig';
import { useLanguage } from '../context/LanguageContext';

export default function Upload() {
    const [uploading, setUploading] = useState(false);
    const [status, setStatus] = useState(null); // 'success' | 'error' | null
    const [message, setMessage] = useState('');
    const [uploadedData, setUploadedData] = useState(null);
    const [viewMode, setViewMode] = useState(false); // New state to toggle full view
    const fileInputRef = useRef(null);

    // Global Language Context
    const { t, language, toggleLanguage } = useLanguage();

    const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB

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
        setMessage(t.processing); // Use translation

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
                setViewMode(true); // Automatically switch to view mode on success
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
        <div className="h-screen bg-neutral-950 text-white font-sans selection:bg-white selection:text-black overflow-hidden relative flex flex-col">

            {/* Background elements */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-white/5 rounded-full blur-[180px]"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-white/5 rounded-full blur-[150px]"></div>
            </div>

            {/* Navbar / Header for non-view mode or just consistent header */}
            <nav className="relative z-20 p-6 flex justify-between items-center container mx-auto flex-shrink-0">
                <Link to="/" className="text-neutral-500 hover:text-white transition-colors flex items-center gap-2 group text-sm font-medium tracking-wide uppercase">
                    <FaArrowLeft className="group-hover:-translate-x-1 transition-transform" />
                    {t.backDashboard}
                </Link>

                <div className="flex items-center gap-4">
                    <button
                        onClick={toggleLanguage}
                        className="px-3 py-2 rounded-lg bg-neutral-900 border border-white/10 text-xs font-semibold tracking-wide text-neutral-300 hover:text-white hover:bg-neutral-800 transition-all flex items-center gap-2 shadow-sm"
                    >
                        <span>{language === 'en' ? "🇮🇳 Hindi" : "🇬🇧 English"}</span>
                    </button>

                    {viewMode && (
                        <button
                            onClick={() => { setViewMode(false); setStatus(null); setUploadedData(null); }}
                            className="text-xs font-bold bg-neutral-800 hover:bg-neutral-700 px-4 py-2 rounded-lg transition-colors border border-white/10 uppercase tracking-widest shadow-lg hover:shadow-white/5"
                        >
                            {t.uploadNew}
                        </button>
                    )}
                </div>
            </nav>

            <div className={`relative z-10 container mx-auto px-6 flex flex-col ${viewMode ? 'h-[calc(100vh-100px)] pb-6' : 'h-screen items-center justify-center'}`}>

                {!viewMode ? (
                    /* UPLOAD SECTION */
                    <>
                        <h1 className="text-4xl md:text-5xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 tracking-tight text-center">
                            {t.docAnalysis}
                        </h1>

                        <p className="text-neutral-400 mb-12 max-w-md text-center text-lg font-light leading-relaxed">
                            {t.uploadDescription}
                        </p>

                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            className="hidden"
                            accept=".pdf,.docx,.txt"
                        />

                        <div
                            onDragOver={handleDragOver}
                            onDrop={handleDrop}
                            onClick={() => !uploading && fileInputRef.current.click()}
                            className={`glass-card w-full max-w-2xl rounded-3xl p-12 text-center transition-all duration-300 hover:border-white/20 group cursor-pointer border-dashed border-2 ${uploading ? 'border-blue-500/50 cursor-wait' : 'border-white/10'} bg-neutral-900/40 relative overflow-hidden`}
                        >
                            {uploading && (
                                <div className="absolute inset-0 bg-neutral-950/80 z-20 flex flex-col items-center justify-center backdrop-blur-sm">
                                    <FaSpinner className="animate-spin h-10 w-10 text-white mb-4" />
                                    <p className="text-white font-medium tracking-wide animate-pulse">{t.processing}</p>
                                </div>
                            )}

                            {!uploading && status === 'error' ? (
                                <div className="animate-fade-in-up">
                                    <div className="w-20 h-20 mx-auto bg-red-500/20 rounded-full flex items-center justify-center mb-6 shadow-[0_0_20px_rgba(239,68,68,0.3)]">
                                        <FaExclamationCircle className="h-10 w-10 text-red-500" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-2">{t.uploadFailed}</h3>
                                    <p className="text-red-400 mb-6">{message}</p>
                                    <p className="text-xs text-neutral-600 mt-6 uppercase tracking-widest click-to-upload">{t.clickRetry}</p>
                                </div>
                            ) : (
                                // Default Status
                                <>
                                    <div className="w-20 h-20 mx-auto bg-neutral-800 rounded-full flex items-center justify-center mb-6 shadow-inner group-hover:scale-110 transition-transform duration-300">
                                        <FaCloudUploadAlt className="h-10 w-10 text-white/80 group-hover:text-white transition-colors" />
                                    </div>

                                    <h3 className="text-xl font-bold text-white mb-2">{t.dropFiles}</h3>
                                    <p className="text-neutral-500 mb-8 font-medium">{t.or} <span className="text-white underline underline-offset-4 decoration-white/30 hover:decoration-white transition-all">{t.browseFiles}</span> {t.fromDevice}</p>

                                    <div className="flex justify-center gap-4 text-xs font-semibold tracking-widest text-neutral-600 uppercase">
                                        <span className="bg-neutral-900/80 px-3 py-1.5 rounded-md border border-white/5 flex items-center gap-2">
                                            <FaFileAlt /> PDF
                                        </span>
                                        <span className="bg-neutral-900/80 px-3 py-1.5 rounded-md border border-white/5 flex items-center gap-2">
                                            <FaFileAlt /> DOCX
                                        </span>
                                        <span className="bg-neutral-900/80 px-3 py-1.5 rounded-md border border-white/5 flex items-center gap-2">
                                            <FaFileAlt /> TXT
                                        </span>
                                    </div>
                                    <p className="text-[10px] text-neutral-700 mt-6">Max File Size: 15MB</p>
                                </>
                            )}
                        </div>
                    </>
                ) : (
                    /* SPLIT VIEW SECTION */
                    <div className="w-full h-full min-h-0 flex flex-col md:flex-row gap-6 animate-fade-in-up max-w-[1800px] mx-auto">

                        {/* LEFT: Document Preview */}
                        <div className="flex-1 glass-card rounded-3xl overflow-hidden flex flex-col border border-white/10 bg-neutral-900/50 h-full">
                            <div className="p-4 border-b border-white/5 flex items-center gap-3 bg-white/5 flex-shrink-0">
                                <FaEye className="text-neutral-400" />
                                <h3 className="text-sm font-bold tracking-wider uppercase text-neutral-300">{t.docPreview}</h3>
                            </div>
                            <div className="flex-1 bg-neutral-900 relative">
                                {uploadedData?.driveUrl ? (
                                    <iframe
                                        src={getPreviewUrl(uploadedData.driveUrl)}
                                        className="w-full h-full absolute inset-0 border-none"
                                        title="Document Preview"
                                        allow="autoplay"
                                    ></iframe>
                                ) : (
                                    <div className="flex items-center justify-center h-full text-neutral-500">
                                        No preview available
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* RIGHT: Summary */}
                        <div className="w-full md:w-[600px] glass-card rounded-3xl p-8 flex flex-col border border-white/10 bg-neutral-900/50 h-full flex-shrink-0">
                            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10 flex-shrink-0">
                                <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                                    <FaAlignLeft className="text-indigo-400" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">{t.aiSummary}</h2>
                                    <p className="text-xs text-neutral-500 uppercase tracking-wider">{t.generatedBy}</p>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                                <div className="prose prose-invert prose-sm max-w-none">
                                    <p className="text-neutral-300 leading-relaxed text-base">
                                        {uploadedData?.summary || "No summary available for this document."}
                                    </p>
                                </div>
                            </div>

                            <div className="mt-6 pt-6 border-t border-white/10 flex-shrink-0">
                                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
                                    <h4 className="text-yellow-500 text-xs font-bold uppercase tracking-wide mb-2">{t.disclaimer}</h4>
                                    <p className="text-neutral-400 text-xs leading-relaxed">
                                        {t.disclaimerText}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
