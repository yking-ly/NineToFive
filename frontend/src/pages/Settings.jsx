import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaSave, FaServer, FaCheckCircle } from 'react-icons/fa';
import { getApiUrl, setApiUrl, DEFAULT_API_URL } from '../utils/apiConfig';
import { useLanguage } from '../context/LanguageContext';

export default function Settings() {
    const navigate = useNavigate();
    const [url, setUrl] = useState('');
    const [saved, setSaved] = useState(false);

    // Global Language Context
    const { t, language, toggleLanguage } = useLanguage();

    useEffect(() => {
        setUrl(getApiUrl());
    }, []);

    const handleSave = (e) => {
        e.preventDefault();
        // Basic validation: ensure it starts with http/https
        let formattedUrl = url.trim();
        if (!formattedUrl) {
            formattedUrl = DEFAULT_API_URL;
        }
        // Remove trailing slash if present for consistency
        if (formattedUrl.endsWith('/')) {
            formattedUrl = formattedUrl.slice(0, -1);
        }

        setApiUrl(formattedUrl);
        setUrl(formattedUrl);
        setSaved(true);

        // Hide success message after 2 seconds
        setTimeout(() => setSaved(false), 2000);
    };

    const handleReset = () => {
        setApiUrl(DEFAULT_API_URL);
        setUrl(DEFAULT_API_URL);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="min-h-screen bg-neutral-950 text-white font-sans selection:bg-white selection:text-black overflow-hidden relative flex flex-col items-center justify-center p-6">

            {/* Background Elements */}
            <div className="absolute top-[-20%] left-[-20%] w-[800px] h-[800px] bg-white/5 rounded-full blur-[150px] pointer-events-none"></div>
            <div className="absolute bottom-[-20%] right-[-20%] w-[600px] h-[600px] bg-white/5 rounded-full blur-[120px] pointer-events-none"></div>

            {/* Back Button */}
            <button
                onClick={() => navigate('/')}
                className="absolute top-8 left-8 flex items-center gap-2 text-neutral-500 hover:text-white transition-colors group text-sm font-medium tracking-wide uppercase z-20"
            >
                <FaArrowLeft className="group-hover:-translate-x-1 transition-transform" />
                {t.backDashboard}
            </button>

            {/* Language Toggle */}
            <button
                onClick={toggleLanguage}
                className="absolute top-8 right-8 z-50 px-3 py-2 rounded-lg bg-neutral-900 border border-white/10 text-xs font-semibold tracking-wide text-neutral-300 hover:text-white hover:bg-neutral-800 transition-all flex items-center gap-2 shadow-sm"
            >
                <span>{language === 'en' ? "🇮🇳 Hindi" : "🇬🇧 English"}</span>
            </button>

            <div className="relative z-10 w-full max-w-lg">
                <div className="text-center mb-10">
                    <h1 className="text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-2">
                        {t.settingsTitle}
                    </h1>
                    <p className="text-neutral-400">{t.configDesc}</p>
                </div>

                <div className="glass-card p-8 rounded-3xl border border-white/10 bg-neutral-900/50 shadow-2xl">
                    <form onSubmit={handleSave} className="space-y-6">

                        <div className="space-y-2">
                            <label htmlFor="serverUrl" className="block text-sm font-bold text-neutral-300 uppercase tracking-wider flex items-center gap-2">
                                <FaServer className="text-neutral-500" /> {t.serverUrl}
                            </label>
                            <div className="relative group">
                                <div className="absolute -inset-0.5 bg-gradient-to-r from-white/10 to-white/5 rounded-xl blur opacity-0 group-hover:opacity-100 transition duration-500"></div>
                                <input
                                    id="serverUrl"
                                    type="text"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    placeholder="http://127.0.0.1:5000"
                                    className="relative w-full bg-neutral-950 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-neutral-700 focus:outline-none focus:border-white/30 transition-colors"
                                />
                            </div>
                            <p className="text-[10px] text-neutral-500">
                                {t.serverUrlHelp} <span className="font-mono text-neutral-400">{DEFAULT_API_URL}</span>.
                            </p>
                        </div>

                        <div className="pt-4 flex items-center gap-3">
                            <button
                                type="submit"
                                className="flex-1 bg-white text-black font-bold py-3 px-6 rounded-xl hover:bg-neutral-200 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-white/5"
                            >
                                <FaSave /> {t.saveChanges}
                            </button>

                            <button
                                type="button"
                                onClick={handleReset}
                                className="px-4 py-3 rounded-xl border border-white/10 text-neutral-400 hover:text-white hover:bg-white/5 transition-colors text-sm font-semibold"
                                title={t.resetTooltip}
                            >
                                {t.reset}
                            </button>
                        </div>
                    </form>

                    {/* Success Notification */}
                    <div className={`mt-6 p-3 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center gap-3 text-green-400 text-sm font-medium transition-all duration-300 ${saved ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2 pointer-events-none'}`}>
                        <FaCheckCircle />
                        {t.savedSuccess}
                    </div>
                </div>
            </div>
        </div>
    );
}
