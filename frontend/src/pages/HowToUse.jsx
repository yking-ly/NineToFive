import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useLanguage } from '../context/LanguageContext';

export default function HowToUse() {
    const [content, setContent] = useState('Loading guide...')
    const [loading, setLoading] = useState(true)

    // Global Language Context
    const { t, language, toggleLanguage } = useLanguage();

    // Helper to fetch content in specific language
    const fetchContent = (lang) => {
        setLoading(true);
        fetch(`http://127.0.0.1:5000/api/guide?lang=${lang}`)
            .then(res => res.json())
            .then(data => {
                setContent(data.content);
                setLoading(false);
            })
            .catch(err => {
                setContent(lang === 'hi' ? "गाइड लोड करने में त्रुटि।" : "Error loading guide.");
                setLoading(false);
            });
    }

    useEffect(() => {
        fetchContent(language);
    }, [language])

    return (
        <div className="min-h-screen bg-neutral-950 text-white p-6 relative selection:bg-white selection:text-black">

            {/* Background elements */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-white/5 rounded-full blur-[180px]"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-white/5 rounded-full blur-[150px]"></div>
            </div>

            <nav className="relative z-50 flex justify-between items-center max-w-5xl mx-auto mb-10 pt-4">
                <Link to="/" className="text-neutral-400 hover:text-white transition-colors flex items-center group text-sm font-medium tracking-wide uppercase">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 transform group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    <span className="font-medium tracking-wide">{t.backHome}</span>
                </Link>

                <button
                    onClick={toggleLanguage}
                    className="px-3 py-2 rounded-lg bg-neutral-900 border border-white/10 text-xs font-semibold tracking-wide text-neutral-300 hover:text-white hover:bg-neutral-800 transition-all flex items-center gap-2 shadow-sm"
                >
                    <span>{language === 'en' ? "🇮🇳 Hindi" : "🇬🇧 English"}</span>
                </button>
            </nav>

            <div className="max-w-4xl mx-auto relative z-10 animate-fade-in-up">
                <div className="glass-card rounded-3xl p-8 md:p-14 min-h-[600px] border border-white/10 shadow-2xl bg-neutral-900/30">
                    <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-neutral-400">{t.userGuide}</h1>
                        <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
                    </div>

                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-80 text-neutral-500 space-y-6">
                            <div className="animate-spin rounded-full h-12 w-12 border-2 border-white/10 border-t-white"></div>
                            <p className="text-xs tracking-[0.2em] uppercase font-medium">{t.translating}</p>
                        </div>
                    ) : (
                        <article className="prose prose-invert prose-lg max-w-none 
                            prose-headings:text-white prose-headings:font-semibold prose-headings:tracking-tight
                            prose-h1:text-4xl prose-h2:text-2xl prose-h3:text-xl
                            prose-p:text-neutral-300 prose-p:leading-relaxed
                            prose-strong:text-white prose-strong:font-bold
                            prose-li:text-neutral-300 prose-li:marker:text-white/50
                            prose-blockquote:border-l-white/20 prose-blockquote:bg-white/5 prose-blockquote:py-2 prose-blockquote:px-4 prose-blockquote:rounded-r-lg prose-blockquote:not-italic
                            prose-a:text-white prose-a:underline prose-a:decoration-white/30 prose-a:underline-offset-4 hover:prose-a:decoration-white">
                            <ReactMarkdown>{content}</ReactMarkdown>
                        </article>
                    )}
                </div>

                <div className="text-center mt-12 text-neutral-600 text-sm">
                    Is This Legal? &copy; 2026
                </div>
            </div>
        </div>
    )
}
