import { useNavigate, Link } from 'react-router-dom'
import { FaFileUpload, FaBalanceScale, FaLanguage, FaBrain, FaChevronDown } from 'react-icons/fa'
import { useLanguage } from '../context/LanguageContext';
import { useState, useEffect } from 'react';

export default function Home() {
    const navigate = useNavigate();
    const { t, language, changeLanguage } = useLanguage();
    const [activeFeature, setActiveFeature] = useState(0);

    useEffect(() => {
        const handleScroll = () => {
            const scrollPosition = window.scrollY;
            const windowHeight = window.innerHeight;
            const featureIndex = Math.floor(scrollPosition / (windowHeight * 0.6));
            setActiveFeature(Math.min(featureIndex, 3));
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const features = [
        {
            icon: FaFileUpload,
            title: "Document Analysis",
            subtitle: "Instant Legal Insights",
            description: "Upload PDFs, images, or scanned documents. Our advanced AI extracts key information, identifies risks, and provides comprehensive summaries in seconds.",
            action: () => navigate('/upload'),
            stats: ["PDF Support", "Image OCR", "Risk Assessment"]
        },
        {
            icon: FaBalanceScale,
            title: "AI Legal Assistant",
            subtitle: "Expert Guidance 24/7",
            description: "Chat with our AI trained on IPC, BNS, and comprehensive Indian legal frameworks. Get instant answers to complex legal questions with cited sources.",
            action: () => navigate('/chat'),
            stats: ["IPC & BNS", "Case Law", "Real-time Answers"]
        },
        {
            icon: FaLanguage,
            title: "Multilingual Support",
            subtitle: "Speak Your Language",
            description: "Communicate seamlessly in English, Hindi, or Romanized Hindi. Our AI understands context and nuance across languages.",
            action: null,
            stats: ["English", "हिंदी", "Hindi Romanized"]
        },
        {
            icon: FaBrain,
            title: "RAG Technology",
            subtitle: "Powered by Intelligence",
            description: "Retrieval-Augmented Generation ensures every response is grounded in verified legal documents, reducing hallucinations and increasing accuracy.",
            action: null,
            stats: ["Verified Sources", "High Accuracy", "Context-Aware"]
        }
    ];

    return (
        <div className="min-h-screen bg-neutral-950 text-white font-sans selection:bg-white selection:text-black overflow-x-hidden">

            {/* Animated Background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-[120px] animate-pulse"></div>
                <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-white/5 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: '2s' }}></div>
                <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-white/3 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '4s' }}></div>
            </div>

            {/* Language Toggle */}
            <div className="fixed top-6 right-6 z-50">
                <div className="flex gap-2 bg-neutral-900/80 backdrop-blur-md border border-white/10 rounded-xl p-1 shadow-lg">
                    <button
                        onClick={() => changeLanguage('en')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${language === 'en' ? 'bg-white/10 text-white' : 'text-neutral-400 hover:text-white'}`}
                    >
                        EN
                    </button>
                    <button
                        onClick={() => changeLanguage('hi')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${language === 'hi' ? 'bg-white/10 text-white' : 'text-neutral-400 hover:text-white'}`}
                    >
                        हिं
                    </button>
                </div>
            </div>

            {/* Hero Section */}
            <section className="relative min-h-screen flex flex-col items-center justify-between px-6 z-10 py-24">
                <div className="flex-1 flex items-center justify-center w-full">
                    <div className="text-center space-y-8 max-w-5xl">
                        <div className="space-y-4">
                            <h1 className="text-7xl md:text-9xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/30 drop-shadow-2xl p-3">
                                {t.homeWelcome}
                            </h1>
                            <div className="h-1 w-32 bg-gradient-to-r from-transparent via-white/50 to-transparent mx-auto"></div>
                        </div>

                        <p className="text-2xl md:text-3xl text-neutral-300 font-light max-w-3xl mx-auto leading-relaxed">
                            {t.homeSubtitle}
                        </p>

                        {/* CTA Buttons */}
                        <div className="flex flex-wrap justify-center gap-4 pt-12">
                            <button
                                onClick={() => navigate('/chat')}
                                className="group px-10 py-5 bg-white text-neutral-950 rounded-2xl font-bold text-base tracking-wide hover:bg-white/90 transition-all duration-300 hover:scale-105 shadow-2xl shadow-white/20 flex items-center gap-3"
                            >
                                <FaBalanceScale className="text-xl group-hover:rotate-12 transition-transform" />
                                {t.startChat}
                            </button>
                            <button
                                onClick={() => navigate('/upload')}
                                className="group px-10 py-5 bg-neutral-900/80 backdrop-blur-md border-2 border-white/20 rounded-2xl font-bold text-base tracking-wide hover:bg-neutral-800 hover:border-white/30 transition-all duration-300 hover:scale-105 flex items-center gap-3"
                            >
                                <FaFileUpload className="text-xl group-hover:translate-y-[-2px] transition-transform" />
                                {t.uploadDocs}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Scroll Indicator */}
                <div className="flex flex-col items-center gap-2 animate-bounce">
                    <span className="text-xs text-neutral-500 uppercase tracking-widest">Discover Features</span>
                    <FaChevronDown className="text-neutral-500" />
                </div>
            </section>

            {/* Timeline Section */}
            <section className="relative py-24 px-6 z-10">
                <div className="max-w-7xl mx-auto">

                    {/* Section Header */}
                    <div className="text-center mb-32">
                        <h2 className="text-5xl md:text-6xl font-black tracking-tight text-white mb-4">
                            Platform Features
                        </h2>
                        <p className="text-xl text-neutral-400 max-w-2xl mx-auto">
                            Cutting-edge technology meets legal expertise
                        </p>
                    </div>

                    {/* Timeline Container */}
                    <div className="relative">
                        {/* Vertical Line */}
                        <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-white/0 via-white/30 to-white/0 transform md:-translate-x-1/2"></div>

                        {/* Progress Indicator */}
                        <div
                            className="absolute left-8 md:left-1/2 top-0 w-px bg-white transform md:-translate-x-1/2 transition-all duration-500"
                            style={{ height: `${(activeFeature / features.length) * 100}%` }}
                        ></div>

                        {/* Timeline Items */}
                        <div className="space-y-32">
                            {features.map((feature, index) => {
                                const Icon = feature.icon;
                                const isActive = activeFeature >= index;
                                const isLeft = index % 2 === 0;

                                return (
                                    <div
                                        key={index}
                                        className={`relative transition-all duration-700 ${isActive ? 'opacity-100' : 'opacity-40'}`}
                                    >
                                        {/* Timeline Node */}
                                        <div className="absolute left-8 md:left-1/2 top-0 transform -translate-x-1/2 z-20">
                                            <div className={`relative w-16 h-16 rounded-full bg-neutral-900 border-4 flex items-center justify-center shadow-2xl backdrop-blur-md transition-all duration-500 ${isActive ? 'border-white scale-110' : 'border-white/20'}`}>
                                                <Icon className={`w-7 h-7 transition-colors duration-500 ${isActive ? 'text-white' : 'text-white/40'}`} />
                                                {isActive && (
                                                    <div className="absolute inset-0 rounded-full bg-white/20 animate-ping"></div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Content Card */}
                                        <div className={`md:flex ${isLeft ? 'md:flex-row' : 'md:flex-row-reverse'} items-center`}>
                                            <div className={`md:w-1/2 ${isLeft ? 'md:pr-24' : 'md:pl-24'} pl-24 md:pl-0`}>
                                                <div
                                                    onClick={feature.action}
                                                    className={`group relative overflow-hidden rounded-3xl bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 p-10 transition-all duration-500 hover:scale-105 hover:shadow-2xl hover:shadow-white/10 ${feature.action ? 'cursor-pointer hover:border-white/30' : ''}`}
                                                >
                                                    {/* Hover Effect */}
                                                    <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                                                    {/* Background Icon */}
                                                    <Icon className="absolute -bottom-8 -right-8 w-48 h-48 text-white opacity-5 blur-sm transform rotate-12 pointer-events-none group-hover:scale-110 transition-transform duration-700" />

                                                    <div className="relative z-10 space-y-6">
                                                        {/* Number Badge */}
                                                        <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-white/10 border border-white/20 text-sm font-bold">
                                                            {String(index + 1).padStart(2, '0')}
                                                        </div>

                                                        {/* Title */}
                                                        <div>
                                                            <h3 className="text-3xl font-black text-white mb-2 group-hover:text-white/90 transition-colors">
                                                                {feature.title}
                                                            </h3>
                                                            <p className="text-sm text-neutral-400 uppercase tracking-widest">
                                                                {feature.subtitle}
                                                            </p>
                                                        </div>

                                                        {/* Description */}
                                                        <p className="text-neutral-300 leading-relaxed text-lg group-hover:text-neutral-200 transition-colors">
                                                            {feature.description}
                                                        </p>

                                                        {/* Stats */}
                                                        <div className="flex flex-wrap gap-3 pt-4">
                                                            {feature.stats.map((stat, i) => (
                                                                <div key={i} className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-xs font-semibold text-neutral-300">
                                                                    {stat}
                                                                </div>
                                                            ))}
                                                        </div>

                                                        {/* Action Link */}
                                                        {feature.action && (
                                                            <div className="flex items-center text-white/60 font-semibold group-hover:text-white transition-colors pt-4">
                                                                <span className="uppercase tracking-widest text-sm">Explore Now</span>
                                                                <svg className="w-5 h-5 ml-2 transform group-hover:translate-x-2 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                                                                </svg>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="relative border-t border-white/5 py-12 z-10">
                <div className="container mx-auto px-6">
                    <div className="flex flex-wrap justify-center items-center gap-6 text-neutral-400 text-xs font-medium tracking-widest uppercase">
                        <span className="opacity-60">Is This Legal?</span>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <a href="https://github.com/yking-ly/NineToFive" target="_blank" rel="noopener noreferrer" className="opacity-60 hover:opacity-100 transition-opacity">
                            NineToFive
                        </a>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <Link to="/how-to-use" className="text-white/60 hover:text-white transition-colors hover:underline decoration-white/30 underline-offset-4">
                            {t.howToUse}
                        </Link>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <Link to="/settings" className="text-white/60 hover:text-white transition-colors hover:underline decoration-white/30 underline-offset-4">
                            Settings
                        </Link>
                    </div>
                </div>
            </footer>
        </div>
    )
}
