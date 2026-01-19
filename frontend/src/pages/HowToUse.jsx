import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'

export default function HowToUse() {
    const [content, setContent] = useState('Loading guide...')
    const [loading, setLoading] = useState(true)

    // Helper to fetch content in specific language
    const fetchContent = (lang = 'en') => {
        setLoading(true);
        fetch(`http://127.0.0.1:5000/api/guide?lang=${lang}`)
            .then(res => res.json())
            .then(data => {
                setContent(data.content);
                setLoading(false);
            })
            .catch(err => {
                setContent("Error loading guide.");
                setLoading(false);
            });
    }

    useEffect(() => {
        fetchContent('en');
    }, [])

    return (
        <div className="min-h-screen bg-slate-900 text-white p-6 relative">
            <Link to="/" className="fixed top-6 left-6 text-slate-400 hover:text-white transition-colors flex items-center z-50">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Home
            </Link>

            <div className="absolute top-6 right-6 z-50 flex gap-2">
                <button
                    onClick={() => fetchContent('en')}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-semibold border border-slate-700 transition-colors focus:ring-2 focus:ring-blue-500"
                >
                    English
                </button>
                <button
                    onClick={() => fetchContent('hi')}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-semibold border border-slate-700 transition-colors focus:ring-2 focus:ring-blue-500"
                >
                    हिंदी (Hindi)
                </button>
            </div>

            <div className="max-w-3xl mx-auto pt-16">
                <div className="bg-slate-800/50 p-8 rounded-2xl shadow-xl border border-slate-700 backdrop-blur-sm min-h-[400px]">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-400 space-y-4">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                            <p>Loading translation...</p>
                        </div>
                    ) : (
                        <article className="prose prose-invert prose-lg max-w-none">
                            <ReactMarkdown>{content}</ReactMarkdown>
                        </article>
                    )}
                </div>
            </div>
        </div>
    )
}
