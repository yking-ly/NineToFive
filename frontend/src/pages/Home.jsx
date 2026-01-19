import { useNavigate, Link } from 'react-router-dom'

export default function Home() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white font-sans selection:bg-purple-500 selection:text-white overflow-hidden relative">

            {/* Abstract Background Shapes */}
            <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-purple-600/30 rounded-full blur-[100px] animate-pulse"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px]"></div>

            <div className="container mx-auto px-4 h-screen flex flex-col items-center justify-center relative z-10">

                {/* Header / Hero */}
                <div className="text-center mb-16 space-y-6">
                    <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-blue-200 via-white to-purple-200 drop-shadow-lg">
                        Is This Legal?
                    </h1>
                    <p className="text-xl md:text-2xl text-slate-300 font-light max-w-2xl mx-auto leading-relaxed">
                        Your personal AI legal expert. Simplify complex regulations, analyze documents, and get answers in seconds.
                    </p>
                </div>

                {/* Action Cards Container */}
                <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">

                    {/* CTA 1: Upload & Summary */}
                    <button
                        onClick={() => navigate('/upload')}
                        className="group relative overflow-hidden rounded-3xl bg-white/5 border border-white/10 p-8 hover:bg-white/10 transition-all duration-500 hover:scale-[1.02] hover:shadow-2xl hover:shadow-purple-500/20 text-left flex flex-col justify-between h-80"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 via-transparent to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                        <div className="relative z-10">
                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mb-6 shadow-lg group-hover:shadow-indigo-500/50 transition-shadow">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                </svg>
                            </div>
                            <h2 className="text-3xl font-bold mb-2 group-hover:text-purple-200 transition-colors">Upload & Summarize</h2>
                            <p className="text-slate-400 group-hover:text-slate-200 transition-colors">
                                Instant analysis of legal documents. Upload PDFs or images to get concise summaries and risk assessments.
                            </p>
                        </div>

                        <div className="relative z-10 flex items-center text-purple-400 font-semibold group-hover:text-purple-300">
                            <span>Start Upload</span>
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                            </svg>
                        </div>
                    </button>

                    {/* CTA 2: Chat Assistant */}
                    <button
                        onClick={() => navigate('/chat')}
                        className="group relative overflow-hidden rounded-3xl bg-white/5 border border-white/10 p-8 hover:bg-white/10 transition-all duration-500 hover:scale-[1.02] hover:shadow-2xl hover:shadow-blue-500/20 text-left flex flex-col justify-between h-80"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 via-transparent to-blue-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                        <div className="relative z-10">
                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mb-6 shadow-lg group-hover:shadow-blue-500/50 transition-shadow">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                </svg>
                            </div>
                            <h2 className="text-3xl font-bold mb-2 group-hover:text-blue-200 transition-colors">AI Legal Assistant</h2>
                            <p className="text-slate-400 group-hover:text-slate-200 transition-colors">
                                Have questions about specific laws? Chat with our AI to navigate the Indian Penal Code and more.
                            </p>
                        </div>

                        <div className="relative z-10 flex items-center text-blue-400 font-semibold group-hover:text-blue-300">
                            <span>Start Chat</span>
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                            </svg>
                        </div>
                    </button>

                </div>

                <footer className="absolute bottom-6 text-slate-500 text-sm flex gap-4">
                    <span>Powered by Advanced RAG • Not Legal Advice</span>
                    <Link to="/how-to-use" className="hover:text-white transition-colors underline">How to Use</Link>
                </footer>
            </div>
        </div>
    )
}
