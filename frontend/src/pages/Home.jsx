import { useNavigate, Link } from 'react-router-dom'
import { FaFileUpload, FaBalanceScale, FaLanguage, FaBrain, FaChevronDown, FaArrowRight, FaMicrophone } from 'react-icons/fa'
import { useLanguage } from '../context/LanguageContext';
import { useState, useRef } from 'react';
import { motion, useScroll, useTransform, useSpring, useMotionValue, useMotionTemplate } from 'framer-motion';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

function FeatureCard({ feature, index }) {
    const cardRef = useRef(null);
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);

    const handleMouseMove = (e) => {
        const { left, top } = cardRef.current.getBoundingClientRect();
        mouseX.set(e.clientX - left);
        mouseY.set(e.clientY - top);
    };

    const background = useMotionTemplate`radial-gradient(
        650px circle at ${mouseX}px ${mouseY}px,
        rgba(255, 255, 255, 0.1),
        transparent 80%
    )`;

    return (
        <motion.div
            ref={cardRef}
            onMouseMove={handleMouseMove}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.8, delay: index * 0.1 }}
            className="group relative rounded-3xl border border-white/10 bg-neutral-900/50 p-8 md:p-12 overflow-hidden hover:border-white/20 transition-colors"
        >
            <motion.div
                className="pointer-events-none absolute -inset-px opacity-0 transition duration-300 group-hover:opacity-100"
                style={{ background }}
            />

            <div className="relative z-10 flex flex-col h-full">
                <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-500">
                    <feature.icon className="w-8 h-8 text-white/80 group-hover:text-white transition-colors" />
                </div>

                <h3 className="text-3xl font-bold text-white mb-4 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-neutral-400 transition-all">
                    {feature.title}
                </h3>

                <p className="text-neutral-400 text-lg leading-relaxed mb-8 flex-grow">
                    {feature.description}
                </p>

                <div className="flex flex-wrap gap-2 mb-8">
                    {feature.stats.map((stat, i) => (
                        <span key={i} className="px-3 py-1 rounded-full bg-white/5 border border-white/5 text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                            {stat}
                        </span>
                    ))}
                </div>

                {feature.action && (
                    <div
                        onClick={feature.action}
                        className="flex items-center gap-2 text-white font-semibold cursor-pointer group/link w-fit"
                    >
                        <span className="border-b border-transparent group-hover/link:border-white transition-colors">{feature.tryItNow}</span>
                        <FaArrowRight className="text-xs transform group-hover/link:translate-x-1 transition-transform" />
                    </div>
                )}
            </div>
        </motion.div>
    );
}

export default function Home() {
    const navigate = useNavigate();
    const { t, language, changeLanguage, isLoading } = useLanguage();
    const containerRef = useRef(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end end"]
    });

    const scaleY = useSpring(scrollYProgress, {
        stiffness: 100,
        damping: 30,
        restDelta: 0.001
    });

    const headerOpacity = useTransform(scrollYProgress, [0, 0.1], [1, 0]);
    const headerY = useTransform(scrollYProgress, [0, 0.1], [0, -50]);

    const features = [
        {
            icon: FaFileUpload,
            title: t.feature1Title,
            description: t.feature1Desc,
            action: () => navigate('/upload'),
            stats: language === 'hi' ? ["ओसीआर (OCR)", "जोखिम विश्लेषण", "सारांश"] : ["OCR", "Risk Analysis", "Summarization"],
            tryItNow: t.tryItNow
        },
        {
            icon: FaBalanceScale,
            title: t.feature2Title,
            description: t.feature2Desc,
            action: () => navigate('/chat'),
            stats: ["IPC/OTC", "BNS", t.sources || "Citations"],
            tryItNow: t.tryItNow
        },
        {
            icon: FaLanguage,
            title: t.feature3Title,
            description: t.feature3Desc,
            action: null,
            stats: ["English", "हिंदी", "Hinglish"],
            tryItNow: t.tryItNow
        },
        {
            icon: FaMicrophone,
            title: t.feature4Title,
            description: t.feature4Desc,
            action: () => navigate('/kira'),
            stats: language === 'hi' ? ["वॉयस चैट", "लाइव संदर्भ", "कानूनी सलाहकार"] : ["Voice Advisory", "Live Citations", "Legal Advisor"],
            tryItNow: t.tryItNow
        }
    ];

    return (
        <motion.div
            ref={containerRef}
            className="min-h-screen bg-[#030303] text-white overflow-hidden relative"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            {/* Scroll Progress Bar (Right Side) */}
            <motion.div
                className="fixed right-0 top-0 bottom-0 w-1 bg-white/10 z-50 origin-top"
            >
                <motion.div
                    className="w-full bg-gradient-to-b from-indigo-500 via-purple-500 to-pink-500"
                    style={{ scaleY, transformOrigin: "top" }}
                />
            </motion.div>

            {/* Dynamic Background */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-indigo-600/10 rounded-full blur-[120px] mix-blend-screen animate-pulse duration-[10s]"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-purple-600/10 rounded-full blur-[120px] mix-blend-screen animate-pulse duration-[7s]"></div>
            </div>

            {/* Navbar / Language Switcher */}
            <motion.nav
                className="fixed top-0 left-0 right-0 z-40 px-8 py-6 flex justify-between items-center mix-blend-difference"
                style={{ opacity: headerOpacity, y: headerY }}
            >
                <div className="font-bold tracking-tighter text-2xl">NINE TO FIVE</div>
                <div className="flex items-center gap-4">
                    <Link to="/kira" className="hidden md:block text-[10px] font-black tracking-widest text-red-500 hover:text-red-400 border border-red-500/20 bg-red-500/5 px-4 py-2 rounded-lg transition-all hover:bg-red-500/10 hover:border-red-500/40 hover:shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                        KIRA // PERSONA
                    </Link>
                    <div className="flex gap-2 bg-white/5 backdrop-blur-md rounded-full p-1 border border-white/10">
                        {['en', 'hi'].map((langKey) => (
                            <button
                                key={langKey}
                                onClick={() => changeLanguage(langKey)}
                                className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase transition-all ${language === langKey ? 'bg-white text-black' : 'text-neutral-400 hover:text-white'
                                    }`}
                            >
                                {langKey === 'en' ? 'EN' : 'HI'}
                            </button>
                        ))}
                    </div>
                </div>
            </motion.nav>

            {/* HERO SECTION */}
            <section className="relative min-h-screen flex items-center justify-center px-6 z-10">
                <div className="max-w-[1400px] w-full grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">

                    {/* Text Content */}
                    <div className="relative z-10 order-2 lg:order-1">
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
                        >
                            <span className="inline-block py-1 px-3 rounded-full bg-white/5 border border-white/10 text-xs font-bold tracking-[0.2em] text-indigo-400 mb-8 uppercase">
                                AI Powered Legal Assistant
                            </span>
                            <h1 className="text-7xl md:text-9xl font-black tracking-tighter leading-[0.9] mb-8">
                                <span className="block text-transparent bg-clip-text bg-gradient-to-br from-white via-white to-white/50">
                                    {isLoading ? <Skeleton width={300} baseColor="#202020" highlightColor="#444" /> : t.homeTitlePart1}
                                </span>
                                <span className="block text-white">
                                    {isLoading ? <Skeleton width={250} baseColor="#202020" highlightColor="#444" /> : t.homeTitlePart2}
                                </span>
                            </h1>
                            <p className="text-xl md:text-2xl text-neutral-400 max-w-lg mb-12 font-light leading-relaxed">
                                {isLoading ? <Skeleton count={2} baseColor="#202020" highlightColor="#444" /> : t.homeSubtitle}
                            </p>

                            <div className="flex flex-wrap gap-6">
                                <motion.button
                                    onClick={() => navigate('/chat')}
                                    className="px-10 py-5 bg-white text-black rounded-full font-bold text-lg tracking-wide hover:scale-105 transition-transform duration-300 flex items-center gap-3"
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    {t.startChat}
                                    <FaArrowRight />
                                </motion.button>
                                <motion.button
                                    onClick={() => navigate('/upload')}
                                    className="px-10 py-5 bg-transparent border border-white/20 text-white rounded-full font-bold text-lg tracking-wide hover:bg-white/5 hover:border-white transition-all duration-300 group"
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    {t.uploadDocs}
                                </motion.button>
                            </div>
                        </motion.div>
                    </div>

                    {/* Abstract Visual / Right Side */}
                    <motion.div
                        className="relative z-10 order-1 lg:order-2 flex justify-center lg:justify-end"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                    >
                        <div className="relative w-[300px] h-[400px] md:w-[500px] md:h-[600px]">
                            {/* Decorative Cards Stack */}
                            <motion.div
                                className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-[40px] border border-white/10 backdrop-blur-3xl z-10"
                                animate={{ y: [0, -20, 0] }}
                                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                            />
                            <motion.div
                                className="absolute inset-0 bg-neutral-900 border border-white/5 rounded-[40px] z-20 m-6 shadow-2xl flex flex-col p-8"
                                animate={{ y: [0, -10, 0] }}
                                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                            >
                                <div className="space-y-6">
                                    <div className="w-16 h-16 rounded-2xl bg-indigo-500 flex items-center justify-center">
                                        <FaBalanceScale className="text-2xl text-white" />
                                    </div>
                                    <div className="space-y-3">
                                        <div className="h-2 w-1/3 bg-white/20 rounded-full"></div>
                                        <div className="h-4 w-3/4 bg-white rounded-full"></div>
                                        <div className="h-16 w-full bg-white/5 rounded-2xl border border-white/5 mt-4"></div>
                                    </div>
                                    <div className="flex-1"></div>
                                    <div className="flex gap-4">
                                        <div className="h-12 flex-1 bg-white rounded-xl"></div>
                                        <div className="h-12 w-12 bg-white/10 rounded-xl"></div>
                                    </div>
                                </div>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>

                <motion.div
                    className="absolute bottom-12 left-1/2 -translate-x-1/2 text-neutral-500 text-sm tracking-widest uppercase animate-bounce"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.5 }}
                >
                    {t.scroll}
                </motion.div>
            </section>

            {/* FEATURES SECTION */}
            <section className="relative py-32 px-6">
                <div className="max-w-[1400px] mx-auto">
                    <motion.div
                        className="mb-24 md:pl-12 border-l-2 border-white/10"
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="text-5xl md:text-7xl font-bold mb-6">{t.capabilitiesTitle}</h2>
                        <p className="text-xl text-neutral-400 max-w-xl">
                            {t.capabilitiesSubtitle}
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {features.map((feature, idx) => (
                            <FeatureCard key={idx} feature={feature} index={idx} />
                        ))}
                    </div>
                </div>
            </section>

            {/* CALL TO ACTION FOOTER */}
            <section className="py-32 relative overflow-hidden flex items-center justify-center text-center px-6">
                <motion.div
                    className="relative z-10 max-w-3xl border border-white/10 bg-[#0a0a0a] rounded-[3rem] p-12 md:p-24 shadow-2xl"
                    initial={{ scale: 0.9, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    viewport={{ once: true }}
                >
                    <h2 className="text-4xl md:text-6xl font-black mb-8 tracking-tight">
                        {t.footerCtaTitle}
                    </h2>
                    <p className="text-neutral-400 text-xl mb-12">
                        {t.footerCtaDesc}
                    </p>
                    <button
                        onClick={() => navigate('/chat')}
                        className="px-12 py-5 bg-white text-black text-xl font-bold rounded-full hover:scale-105 transition-transform shadow-[0_0_40px_rgba(255,255,255,0.3)] hover:shadow-[0_0_60px_rgba(255,255,255,0.5)] duration-300"
                    >
                        {t.getStartedNow}
                    </button>

                    <footer className="mt-20 pt-10 border-t border-white/10 flex justify-center gap-8 text-sm text-neutral-500 font-medium tracking-widest uppercase">
                        <Link to="/how-to-use" className="hover:text-white transition-colors">{t.howToUse}</Link>
                        <Link to="/settings" className="hover:text-white transition-colors">{t.settingsTitle}</Link>
                    </footer>
                </motion.div>

                {/* Background Glow */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/10 rounded-full blur-[150px] pointer-events-none"></div>
            </section>
        </motion.div>
    )
}
