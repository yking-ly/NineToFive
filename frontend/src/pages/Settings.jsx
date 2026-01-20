import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaSave, FaServer, FaCheckCircle } from 'react-icons/fa';
import { getApiUrl, setApiUrl, DEFAULT_API_URL } from '../utils/apiConfig';
import { useLanguage } from '../context/LanguageContext';
import { motion, AnimatePresence } from 'framer-motion';

export default function Settings() {
    const navigate = useNavigate();
    const [url, setUrl] = useState('');
    const [saved, setSaved] = useState(false);

    // Global Language Context
    const { t, language, changeLanguage } = useLanguage();

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
        <div className="min-h-screen bg-[#030303] text-white font-sans selection:bg-white selection:text-black overflow-hidden relative flex flex-col items-center justify-center p-6">

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
            <div className="absolute top-8 right-8 z-50 flex gap-2 bg-neutral-900 border border-white/10 rounded-lg p-1">
                {['en', 'hi'].map((langKey) => (
                    <button
                        key={langKey}
                        onClick={() => changeLanguage(langKey)}
                        className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${language === langKey
                                ? 'bg-white text-black shadow-sm'
                                : 'text-neutral-400 hover:text-white'
                            }`}
                    >
                        {langKey === 'en' ? 'EN' : 'HI'}
                    </button>
                ))}
            </div>

            <motion.div
                className="relative z-10 w-full max-w-lg"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
            >
                <div className="text-center mb-10">
                    <motion.h1
                        className="text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-2"
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                    >
                        {t.settingsTitle}
                    </motion.h1>
                    <motion.p
                        className="text-neutral-400"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3, duration: 0.5 }}
                    >
                        {t.configDesc}
                    </motion.p>
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
                            <motion.button
                                type="submit"
                                className="flex-1 bg-white text-black font-bold py-3 px-6 rounded-xl hover:bg-neutral-200 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-white/5"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                <FaSave /> {t.saveChanges}
                            </motion.button>

                            <motion.button
                                type="button"
                                onClick={handleReset}
                                className="px-4 py-3 rounded-xl border border-white/10 text-neutral-400 hover:text-white hover:bg-white/5 transition-colors text-sm font-semibold"
                                title={t.resetTooltip}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {t.reset}
                            </motion.button>
                        </div>
                    </form>

                    {/* Success Notification */}
                    <AnimatePresence>
                        {saved && (
                            <motion.div
                                initial={{ opacity: 0, height: 0, y: 10 }}
                                animate={{ opacity: 1, height: 'auto', y: 0 }}
                                exit={{ opacity: 0, height: 0, y: -10 }}
                                className="mt-6 p-3 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center gap-3 text-green-400 text-sm font-medium"
                            >
                                <FaCheckCircle />
                                {t.savedSuccess}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </div>
    );
}
