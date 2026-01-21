import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaArrowLeft, FaGavel, FaShieldAlt, FaUserShield, FaCar, FaHome } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

export default function KYL() {
    const [kylData, setKylData] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState('criminal_law');
    const [selectedItem, setSelectedItem] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchKYLData();
    }, []);

    const fetchKYLData = async () => {
        try {
            const response = await axios.get('http://127.0.0.1:5000/api/kyl');
            setKylData(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching KYL data:', error);
            setLoading(false);
        }
    };

    const categories = [
        { id: 'criminal_law', label: 'Criminal Law', icon: FaGavel },
        { id: 'civil_rights', label: 'Your Rights', icon: FaUserShield },
        { id: 'everyday_law', label: 'Everyday Law', icon: FaShieldAlt },
    ];

    return (
        <div className="min-h-screen bg-[#030303] text-white">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-0 left-0 w-1/2 h-1/2 bg-purple-600/5 rounded-full blur-[150px]"></div>
                <div className="absolute bottom-0 right-0 w-1/2 h-1/2 bg-pink-600/5 rounded-full blur-[150px]"></div>
            </div>

            {/* Header */}
            <header className="relative z-10 px-8 py-6 border-b border-white/5 bg-[#030303]/80 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link to="/" className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center hover:bg-white/10 transition-colors border border-white/5">
                            <FaArrowLeft className="text-neutral-400" />
                        </Link>
                        <div>
                            <h1 className="text-2xl font-bold">Know Your Law</h1>
                            <p className="text-sm text-neutral-400">Understanding legal provisions that affect you</p>
                        </div>
                    </div>
                    <FaGavel className="w-12 h-12 text-purple-400 opacity-50" />
                </div>
            </header>

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
                                        setSelectedItem(null);
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

                            {/* Info Card */}
                            <div className="p-6 rounded-xl bg-gradient-to-br from-purple-900/20 to-pink-900/20 border border-white/10 mt-8">
                                <h4 className="font-bold mb-2 text-purple-300">💡 Did You Know?</h4>
                                <p className="text-sm text-neutral-300">
                                    Understanding your legal rights is the first step to protecting yourself and your loved ones.
                                </p>
                            </div>
                        </div>

                        {/* Content Area */}
                        <div className="lg:col-span-9">
                            <AnimatePresence mode="wait">
                                {selectedItem ? (
                                    <motion.div
                                        key="item-detail"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -20 }}
                                        className="bg-neutral-900/50 border border-white/10 rounded-2xl p-8"
                                    >
                                        <button
                                            onClick={() => setSelectedItem(null)}
                                            className="mb-6 text-sm text-neutral-400 hover:text-white flex items-center gap-2"
                                        >
                                            <FaArrowLeft className="w-3 h-3" />
                                            Back to list
                                        </button>

                                        <h2 className="text-4xl font-bold mb-2">{selectedItem.section || selectedItem.title}</h2>
                                        <h3 className="text-2xl text-neutral-300 mb-6">{selectedItem.title}</h3>

                                        <div className="space-y-6">
                                            {selectedItem.description && (
                                                <div>
                                                    <h4 className="text-sm uppercase tracking-wider text-neutral-500 mb-2">Description</h4>
                                                    <p className="text-lg leading-relaxed text-neutral-200">
                                                        {selectedItem.description}
                                                    </p>
                                                </div>
                                            )}

                                            {selectedItem.example && (
                                                <div className="p-6 bg-purple-900/10 border-l-4 border-purple-500 rounded-r-xl">
                                                    <h4 className="text-sm uppercase tracking-wider text-purple-400 mb-2">Example</h4>
                                                    <p className="text-lg text-purple-100">{selectedItem.example}</p>
                                                </div>
                                            )}

                                            {selectedItem.severity && (
                                                <div className="flex items-center gap-4">
                                                    <div className="px-4 py-2 bg-red-900/20 border border-red-500/30 rounded-lg">
                                                        <span className="text-xs text-red-300 font-bold uppercase">Severity</span>
                                                        <p className="text-sm text-red-100 mt-1">{selectedItem.severity}</p>
                                                    </div>
                                                </div>
                                            )}

                                            {selectedItem.rights && (
                                                <div>
                                                    <h4 className="text-sm uppercase tracking-wider text-neutral-500 mb-4">Your Rights</h4>
                                                    <ul className="space-y-3">
                                                        {selectedItem.rights.map((right, idx) => (
                                                            <li key={idx} className="flex items-start gap-3">
                                                                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                                                                <span className="text-lg text-neutral-200">{right}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}

                                            <div className="p-6 bg-green-900/10 border-l-4 border-green-500 rounded-r-xl">
                                                <h4 className="text-sm uppercase tracking-wider text-green-400 mb-2">In Simple Words</h4>
                                                <p className="text-lg text-green-100">{selectedItem.simplified}</p>
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="item-list"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="grid grid-cols-1 md:grid-cols-2 gap-6"
                                    >
                                        {kylData?.[selectedCategory]?.map((item, index) => (
                                            <motion.button
                                                key={item.id || index}
                                                initial={{ opacity: 0, y: 20 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: index * 0.1 }}
                                                onClick={() => setSelectedItem(item)}
                                                className="group p-6 rounded-2xl bg-neutral-900/50 border border-white/10 hover:border-white/30 hover:bg-neutral-800 transition-all text-left"
                                            >
                                                {item.topic ? (
                                                    // Everyday law items
                                                    <>
                                                        <div className="flex items-start justify-between mb-3">
                                                            <span className="inline-block px-3 py-1 bg-purple-500/20 text-purple-300 rounded text-xs font-bold">
                                                                {item.topic}
                                                            </span>
                                                            <FaArrowLeft className="w-4 h-4 -rotate-180 text-neutral-600 group-hover:text-white transition-colors" />
                                                        </div>
                                                        <h3 className="text-lg font-bold mb-2 group-hover:text-white transition-colors">
                                                            {item.topic}
                                                        </h3>
                                                        <p className="text-sm text-neutral-400">
                                                            {item.key_points?.length} key points to know
                                                        </p>
                                                    </>
                                                ) : (
                                                    // Criminal law / rights items
                                                    <>
                                                        <div className="flex items-start justify-between mb-3">
                                                            {item.section && (
                                                                <span className="inline-block px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs font-bold">
                                                                    {item.section}
                                                                </span>
                                                            )}
                                                            <FaArrowLeft className="w-4 h-4 -rotate-180 text-neutral-600 group-hover:text-white transition-colors" />
                                                        </div>
                                                        <h3 className="text-xl font-bold mb-2 group-hover:text-white transition-colors">
                                                            {item.title}
                                                        </h3>
                                                        <p className="text-sm text-neutral-400 line-clamp-2">
                                                            {item.simplified || item.description}
                                                        </p>
                                                    </>
                                                )}
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
