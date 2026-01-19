import { Link } from 'react-router-dom';
import { FaCloudUploadAlt, FaFileAlt, FaArrowLeft } from 'react-icons/fa';

export default function Upload() {
    return (
        <div className="min-h-screen bg-neutral-950 text-white font-sans selection:bg-white selection:text-black overflow-hidden relative">

            {/* Background elements */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-white/5 rounded-full blur-[180px]"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-white/5 rounded-full blur-[150px]"></div>
            </div>

            <div className="relative z-10 container mx-auto px-6 h-screen flex flex-col items-center justify-center">

                <h1 className="text-4xl md:text-5xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 tracking-tight text-center">
                    Document Analysis
                </h1>

                <p className="text-neutral-400 mb-12 max-w-md text-center text-lg font-light leading-relaxed">
                    Upload your legal documents for instant summary and risk assessment using our advanced RAG engine.
                </p>

                <div className="glass-card w-full max-w-2xl rounded-3xl p-12 text-center transition-all duration-300 hover:border-white/20 group cursor-pointer border-dashed border-2 border-white/10 bg-neutral-900/40">
                    <div className="w-20 h-20 mx-auto bg-neutral-800 rounded-full flex items-center justify-center mb-6 shadow-inner group-hover:scale-110 transition-transform duration-300">
                        <FaCloudUploadAlt className="h-10 w-10 text-white/80 group-hover:text-white transition-colors" />
                    </div>

                    <h3 className="text-xl font-bold text-white mb-2">Drop your files here</h3>
                    <p className="text-neutral-500 mb-8 font-medium">or <span className="text-white underline underline-offset-4 decoration-white/30 hover:decoration-white transition-all">browse files</span> from your computer</p>

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
                </div>

                <Link to="/" className="mt-12 text-neutral-500 hover:text-white transition-colors flex items-center gap-2 group text-sm font-medium tracking-wide uppercase">
                    <FaArrowLeft className="group-hover:-translate-x-1 transition-transform" />
                    Back to Dashboard
                </Link>
            </div>
        </div>
    )
}
