import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import TopBar from '../components/TopBar';
import { FaArrowLeft, FaBook, FaGavel, FaUsers, FaLightbulb } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

export default function KYC() {
    const [kycData, setKycData] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState('fundamental_rights');
    const [selectedArticle, setSelectedArticle] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchKYCData();
    }, []);

    const fetchKYCData = async () => {
        try {
            const response = await axios.get('http://127.0.0.1:5000/api/kyc');
            setKycData(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching KYC data:', error);
            setLoading(false);
        }
    };

    const categories = [
        { id: 'fundamental_rights', label: 'Fundamental Rights', icon: FaGavel },
        { id: 'directive_principles', label: 'Directive Principles', icon: FaLightbulb },
    ];

    return (
        <div className="min-h-screen bg-[#030303] text-white">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-indigo-600/5 rounded-full blur-[150px]"></div>
                <div className="absolute bottom-0 left-0 w-1/2 h-1/2 bg-purple-600/5 rounded-full blur-[150px]"></div>
            </div>

            {/* Header */}
            <TopBar title="Know Your Constitution" subtitle="Understanding your fundamental rights">
                <FaBook className="w-8 h-8 text-indigo-400 opacity-50" />
            </TopBar>

            {/* Main Content */}
            <main className="relative z-10 max-w-7xl mx-auto px-8 py-12">
                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="text-neutral-400">Loading...</div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                        {/* Sidebar */}
                        <div className="lg:col-span-3 space-y-4">
                            <h3 className="text-lg font-bold text-neutral-300 mb-4">Categories</h3>
                            {categories.map((cat) => (
                                <button
                                    key={cat.id}
                                    onClick={() => {
                                        setSelectedCategory(cat.id);
                                        setSelectedArticle(null);
                                    }}
                                    className={`w-full p-4 rounded-xl text-left transition-all flex items-center gap-3 ${selectedCategory === cat.id
                                        ? 'bg-white text-black shadow-lg'
                                        : 'bg-neutral-900/50 border border-white/10 hover:border-white/20 text-neutral-300'
                                        }`}
                                >
                                    <cat.icon className="w-5 h-5" />
                                    <span className="font-semibold">{cat.label}</span>
                                </button>
                            ))}

                            {/* Overview Card */}
                            {kycData?.overview && (
                                <div className="p-6 rounded-xl bg-gradient-to-br from-indigo-900/20 to-purple-900/20 border border-white/10 mt-8">
                                    <h4 className="font-bold mb-4 text-indigo-300">Quick Facts</h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-neutral-400">Total Articles:</span>
                                            <span className="font-bold text-white">{kycData.overview.total_articles}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-neutral-400">Parts:</span>
                                            <span className="font-bold text-white">{kycData.overview.parts}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-neutral-400">Adopted:</span>
                                            <span className="font-bold text-white">{kycData.overview.adoption_date}</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Content Area */}
                        <div className="lg:col-span-9">
                            <AnimatePresence mode="wait">
                                {selectedArticle ? (
                                    <motion.div
                                        key="article-detail"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -20 }}
                                        className="bg-neutral-900/50 border border-white/10 rounded-2xl p-8"
                                    >
                                        <button
                                            onClick={() => setSelectedArticle(null)}
                                            className="mb-6 text-sm text-neutral-400 hover:text-white flex items-center gap-2"
                                        >
                                            <FaArrowLeft className="w-3 h-3" />
                                            Back to list
                                        </button>

                                        <div className="mb-4">
                                            <span className="inline-block px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-xs font-bold mb-4">
                                                {selectedArticle.category}
                                            </span>
                                        </div>

                                        <h2 className="text-4xl font-bold mb-2">{selectedArticle.article}</h2>
                                        <h3 className="text-2xl text-neutral-300 mb-6">{selectedArticle.title}</h3>

                                        <div className="space-y-6">
                                            <div>
                                                <h4 className="text-sm uppercase tracking-wider text-neutral-500 mb-2">Official Text</h4>
                                                <p className="text-lg leading-relaxed text-neutral-200">
                                                    {selectedArticle.description}
                                                </p>
                                            </div>

                                            <div className="p-6 bg-green-900/10 border-l-4 border-green-500 rounded-r-xl">
                                                <h4 className="text-sm uppercase tracking-wider text-green-400 mb-2">Simplified Explanation</h4>
                                                <p className="text-lg text-green-100">
                                                    {selectedArticle.simplified}
                                                </p>
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="article-list"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="grid grid-cols-1 md:grid-cols-2 gap-6"
                                    >
                                        {kycData?.[selectedCategory]?.map((article, index) => (
                                            <motion.button
                                                key={article.id}
                                                initial={{ opacity: 0, y: 20 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: index * 0.1 }}
                                                onClick={() => setSelectedArticle(article)}
                                                className="group p-6 rounded-2xl bg-neutral-900/50 border border-white/10 hover:border-white/30 hover:bg-neutral-800 transition-all text-left"
                                            >
                                                <div className="flex items-start justify-between mb-3">
                                                    <span className="inline-block px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded text-xs font-bold">
                                                        {article.article}
                                                    </span>
                                                    <FaArrowLeft className="w-4 h-4 -rotate-180 text-neutral-600 group-hover:text-white transition-colors" />
                                                </div>
                                                <h3 className="text-xl font-bold mb-2 group-hover:text-white transition-colors">
                                                    {article.title}
                                                </h3>
                                                <p className="text-sm text-neutral-400 line-clamp-2">
                                                    {article.simplified}
                                                </p>
                                            </motion.button>
                                        ))}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
