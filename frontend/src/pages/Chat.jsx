import { Link } from 'react-router-dom';
import { FaUserAstronaut, FaPaperPlane, FaArrowLeft, FaComments } from 'react-icons/fa';

export default function Chat() {
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
                            <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-semibold">Online • v1.0</span>
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
            <main className="flex-1 relative z-10 overflow-y-auto p-4 md:p-8 flex flex-col items-center justify-center">
                <div className="max-w-2xl w-full text-center space-y-8">
                    <div className="w-24 h-24 mx-auto rounded-3xl bg-gradient-to-br from-neutral-800 to-neutral-900 border border-white/5 flex items-center justify-center shadow-2xl shadow-black/50">
                        <FaComments className="w-10 h-10 text-white/20" />
                    </div>

                    <div className="space-y-4">
                        <h2 className="text-3xl font-bold text-white tracking-tight">How can I help you today?</h2>
                        <p className="text-neutral-400 max-w-lg mx-auto leading-relaxed">
                            I am trained on the Indian Penal Code (IPC), Bhartiya Nyaya Sanhita (BNS), and other legal frameworks. Ask me anything.
                        </p>
                    </div>

                    <div className="flex flex-wrap justify-center gap-3">
                        <button className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5">
                            What is Section 302?
                        </button>
                        <button className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5">
                            Explain property rights for women
                        </button>
                        <button className="glass px-5 py-2.5 rounded-full text-sm text-neutral-300 hover:bg-white/10 hover:text-white transition-all hover:scale-105 border border-white/5">
                            Difference between IPC and BNS
                        </button>
                    </div>
                </div>
            </main>

            {/* Input Area */}
            <footer className="relative z-20 p-4 md:p-6 bg-neutral-950/80 backdrop-blur-xl border-t border-white/5">
                <div className="max-w-3xl mx-auto relative group">
                    <div className="absolute -inset-0.5 rounded-2xl blur"></div>
                    <div className="relative flex items-center gap-3 bg-neutral-900 rounded-2xl p-2 border border-white/10 shadow-xl">
                        <input
                            type="text"
                            placeholder="Type a message regarding your legal queries..."
                            className="flex-1 bg-transparent border-none outline-none text-white px-4 py-3 placeholder:text-neutral-600 font-medium"
                        />
                        <button className="w-12 h-12 bg-white text-black rounded-xl flex items-center justify-center hover:bg-neutral-200 transition-colors shadow-lg shadow-white/10">
                            <FaPaperPlane className="w-4 h-4" />
                        </button>
                    </div>
                    <p className="text-center text-[10px] text-neutral-600 mt-4 uppercase tracking-widest font-medium">
                        AI generated responses may vary. Consult a lawyer for serious advice.
                    </p>
                </div>
            </footer>
        </div>
    )
}
