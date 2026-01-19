import { Link } from 'react-router-dom';

export default function Upload() {
    return (
        <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-4">
            <h1 className="text-4xl font-bold mb-4 text-purple-400">Document Upload & Summary</h1>
            <p className="text-slate-400 mb-8 max-w-md text-center">
                Upload your legal documents here for instant analysis and summarization.
                (Feature implementation coming soon)
            </p>

            <div className="border-2 border-dashed border-slate-700 rounded-xl p-12 w-full max-w-xl text-center hover:border-purple-500 transition-colors cursor-pointer bg-slate-800/50">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-slate-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                <p className="text-lg">Drag & Drop files or <span className="text-purple-400 font-semibold">Browse</span></p>
                <p className="text-sm text-slate-500 mt-2">PDF, DOCX, JPG supported</p>
            </div>

            <Link to="/" className="mt-8 text-slate-500 hover:text-white transition-colors flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Home
            </Link>
        </div>
    )
}
