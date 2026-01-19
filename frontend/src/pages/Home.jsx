import { useNavigate, Link } from 'react-router-dom'
import { FaFileUpload, FaBalanceScale, FaArrowRight } from 'react-icons/fa'

export default function Home() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-neutral-950 text-white font-sans selection:bg-white selection:text-black overflow-hidden relative">

            {/* Subtle Gradient Spots (Monochrome) */}
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-white/5 rounded-full blur-[120px] pointer-events-none"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-white/5 rounded-full blur-[150px] pointer-events-none"></div>

            <div className="container mx-auto px-6 h-screen flex flex-col items-center justify-center relative z-10">

                {/* Header / Hero */}
                <div className="text-center mb-12 space-y-6">
                    <h1 className="text-5xl md:text-7xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40 drop-shadow-sm p-3">
                        Is This Legal?
                    </h1>
                    <p className="text-lg md:text-xl text-neutral-400 font-light max-w-2xl mx-auto leading-relaxed">
                        Your personal AI legal expert. Simplify complex regulations, analyze documents, and get answers in seconds.
                    </p>
                </div>

                {/* Action Cards Container */}
                <div className="flex flex-wrap justify-center gap-6 w-full">

                    {/* CTA 1: Upload & Summary */}
                    <button
                        onClick={() => navigate('/upload')}
                        className="group relative overflow-hidden rounded-2xl glass-card p-6 hover:bg-white/10 transition-all duration-500 hover:scale-105 hover:shadow-white/5 text-left flex flex-col justify-between w-full md:w-72 h-64"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                        {/* Background Icon */}
                        <FaFileUpload className="absolute -bottom-8 -right-8 w-48 h-48 text-white opacity-5 blur-[6px] transform -rotate-12 pointer-events-none group-hover:scale-110 transition-transform duration-500" />

                        <div className="relative z-10">
                            <div className="w-12 h-12 rounded-xl bg-neutral-900 border border-white/10 flex items-center justify-center mb-4 shadow-inner group-hover:border-white/30 transition-colors">
                                <FaFileUpload className="h-5 w-5 text-white" />
                            </div>
                            <h2 className="text-lg font-bold mb-2 text-white group-hover:text-white/90 transition-colors">Upload & Summary</h2>
                            <p className="text-neutral-400 group-hover:text-neutral-300 transition-colors text-xs leading-relaxed">
                                Instant analysis. Upload PDFs/images for concise summaries.
                            </p>
                        </div>

                        <div className="relative z-10 flex items-center text-white/50 font-medium group-hover:text-white transition-colors mt-auto">
                            <span className="uppercase tracking-widest text-[10px]">Start Upload</span>
                            <FaArrowRight className="h-3 w-3 ml-2 transform group-hover:translate-x-1 transition-transform" />
                        </div>
                    </button>

                    {/* CTA 2: Chat Assistant */}
                    <button
                        onClick={() => navigate('/chat')}
                        className="group relative overflow-hidden rounded-2xl glass-card p-6 hover:bg-white/10 transition-all duration-500 hover:scale-105 hover:shadow-white/5 text-left flex flex-col justify-between w-full md:w-72 h-64"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                        {/* Background Icon */}
                        <FaBalanceScale className="absolute -bottom-8 -right-8 w-48 h-48 text-white opacity-5 blur-[6px] transform -rotate-12 pointer-events-none group-hover:scale-110 transition-transform duration-500" />

                        <div className="relative z-10">
                            <div className="w-12 h-12 rounded-xl bg-neutral-900 border border-white/10 flex items-center justify-center mb-4 shadow-inner group-hover:border-white/30 transition-colors">
                                <FaBalanceScale className="h-5 w-5 text-white" />
                            </div>
                            <h2 className="text-lg font-bold mb-2 text-white group-hover:text-white/90 transition-colors">AI Legal Assistant</h2>
                            <p className="text-neutral-400 group-hover:text-neutral-300 transition-colors text-xs leading-relaxed">
                                Chat with AI to navigate the BNS and IPC regulations.
                            </p>
                        </div>

                        <div className="relative z-10 flex items-center text-white/50 font-medium group-hover:text-white transition-colors mt-auto">
                            <span className="uppercase tracking-widest text-[10px]">Start Chat</span>
                            <FaArrowRight className="h-3 w-3 ml-2 transform group-hover:translate-x-1 transition-transform" />
                        </div>
                    </button>

                </div>

                <footer className="absolute bottom-6 w-full flex justify-center pointer-events-none">
                    <div className="glass px-6 py-3 rounded-full flex items-center gap-6 text-neutral-400 text-xs font-medium tracking-widest uppercase pointer-events-auto shadow-2xl shadow-black/50">
                        <span className="opacity-60">Is This Legal?</span>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <Link to="https://github.com/yking-ly/NineToFive" className="opacity-60">NineToFive</Link>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <Link to="/how-to-use" className="text-white/80 hover:text-white transition-colors hover:underline decoration-white/30 underline-offset-4">How to Use</Link>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <Link to="/settings" className="text-white/80 hover:text-white transition-colors hover:underline decoration-white/30 underline-offset-4">Settings</Link>
                    </div>
                </footer>
            </div>
        </div>
    )
}
