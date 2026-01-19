import { Link } from 'react-router-dom';

export default function Chat() {
    return (
        <div className="min-h-screen bg-slate-900 text-white flex flex-col">
            {/* Header */}
            <div className="bg-slate-800 p-4 shadow-md flex items-center justify-between border-b border-slate-700">
                <div className="flex items-center">
                    <h1 className="text-xl font-bold text-blue-400">AI Legal Assistant</h1>
                    <span className="ml-3 px-2 py-0.5 rounded bg-blue-900/50 text-blue-200 text-xs text-center border border-blue-800">BETA</span>
                </div>

                <Link to="/" className="text-sm text-slate-400 hover:text-white">Exit Chat</Link>
            </div>

            {/* Chat Area - Placeholder */}
            <div className="flex-1 p-6 overflow-y-auto flex flex-col items-center justify-center text-slate-500 space-y-4">
                <div className="bg-slate-800/50 p-6 rounded-full inline-block">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-blue-500/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                </div>
                <p className="text-lg">Start a conversation to get legal insights.</p>
                <div className="flex gap-2">
                    <button className="px-4 py-2 bg-slate-800 rounded-full text-sm hover:bg-slate-700 transition">What is Section 302?</button>
                    <button className="px-4 py-2 bg-slate-800 rounded-full text-sm hover:bg-slate-700 transition">Explain basic property rights</button>
                </div>
            </div>

            {/* Input Area */}
            <div className="p-4 bg-slate-800/80 border-t border-slate-700">
                <div className="max-w-4xl mx-auto flex gap-4">
                    <input
                        type="text"
                        placeholder="Type your legal question here..."
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                    />
                    <button className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-semibold transition shadow-lg shadow-blue-600/20">
                        Send
                    </button>
                </div>
            </div>
        </div>
    )
}
