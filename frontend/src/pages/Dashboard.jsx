import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSession } from '../context/SessionContext';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FaComments, FaFileUpload, FaMicrophone, FaBook, FaGavel, FaHistory,
    FaChartLine, FaSignOutAlt, FaClock, FaArrowRight, FaPlus, FaTrash,
    FaFire, FaStar, FaHome, FaFileAlt, FaBars
} from 'react-icons/fa';
import axios from 'axios';

export default function Dashboard() {
    const navigate = useNavigate();
    const { user, signOut } = useAuth();
    const { sessions, currentSession, switchSession, createSession, deleteSession } = useSession();

    // State
    const [greeting, setGreeting] = useState('');
    const [activeTab, setActiveTab] = useState('overview'); // overview, documents, sessions
    const [uploads, setUploads] = useState([]);
    const [loadingUploads, setLoadingUploads] = useState(false);
    const [deletingId, setDeletingId] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true); // For mobile responsive

    useEffect(() => {
        const hour = new Date().getHours();
        if (hour < 12) setGreeting('Good Morning');
        else if (hour < 17) setGreeting('Good Afternoon');
        else setGreeting('Good Evening');
    }, []);

    // Fetch uploads when Documents tab is active
    useEffect(() => {
        if (activeTab === 'documents') {
            fetchUploads();
        }
    }, [activeTab]);

    const fetchUploads = async () => {
        setLoadingUploads(true);
        try {
            const res = await axios.get('http://127.0.0.1:5000/api/uploads');
            setUploads(res.data || []);
        } catch (error) {
            console.error("Failed to fetch uploads", error);
        } finally {
            setLoadingUploads(false);
        }
    };

    const handleSignOut = async () => {
        await signOut();
        navigate('/');
    };

    const handleNewChat = async () => {
        const session = await createSession('New Consultation');
        if (session) navigate('/chat');
    };

    const handleDeleteSession = async (e, sessionId) => {
        e.stopPropagation();
        if (confirm('Delete this session? This cannot be undone.')) {
            setDeletingId(sessionId);
            await deleteSession(sessionId);
            setDeletingId(null);
        }
    };

    const formatTimeAgo = (timestamp) => {
        if (!timestamp) return 'Just now';
        const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return date.toLocaleDateString();
    };

    // --- SUB-COMPONENTS ---

    const SidebarItem = ({ id, label, icon: Icon }) => (
        <button
            onClick={() => { setActiveTab(id); if (window.innerWidth < 768) setIsSidebarOpen(false); }}
            className={`w-full flex items-center gap-4 px-6 py-4 transition-all border-l-4 ${activeTab === id
                    ? 'border-indigo-500 bg-white/5 text-white shadow-lg'
                    : 'border-transparent text-neutral-400 hover:text-white hover:bg-white/5'
                }`}
        >
            <Icon className={`w-5 h-5 ${activeTab === id ? 'text-indigo-400' : ''}`} />
            <span className="font-semibold">{label}</span>
        </button>
    );

    const StatCard = ({ label, value, icon: Icon, color, textColor }) => (
        <motion.div
            whileHover={{ y: -5 }}
            className="group relative p-6 rounded-3xl bg-neutral-900/50 border border-white/10 overflow-hidden"
        >
            <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-0 group-hover:opacity-10 transition-opacity duration-500`}></div>
            <div className="relative z-10 flex justify-between items-start">
                <div>
                    <p className="text-neutral-400 text-sm font-medium mb-1">{label}</p>
                    <h3 className="text-4xl font-black text-white">{value}</h3>
                </div>
                <div className={`p-3 rounded-2xl bg-white/5 ${textColor}`}>
                    <Icon className="w-6 h-6" />
                </div>
            </div>
        </motion.div>
    );

    const OverviewTab = () => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-12"
        >
            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard
                    label="Total Sessions"
                    value={sessions.length}
                    icon={FaHistory}
                    color="from-blue-500 to-indigo-600"
                    textColor="text-blue-400"
                />
                <StatCard
                    label="Active Today"
                    value={sessions.filter(s => new Date(s.updatedAt?.toDate ? s.updatedAt.toDate() : s.updatedAt).toDateString() === new Date().toDateString()).length}
                    icon={FaFire}
                    color="from-orange-500 to-red-600"
                    textColor="text-orange-400"
                />
                <StatCard
                    label="Documents Analyzed"
                    value={uploads.length || "Loading..."}
                    icon={FaFileAlt}
                    color="from-purple-500 to-pink-600"
                    textColor="text-purple-400"
                />
            </div>

            {/* Quick Actions */}
            <div>
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                    <span className="w-2 h-8 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></span>
                    Quick Actions
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[
                        { title: 'New Chat', desc: 'Legal consultation', icon: FaComments, color: 'text-blue-400', action: () => navigate('/chat') },
                        { title: 'Upload', desc: 'Analyze documents', icon: FaFileUpload, color: 'text-purple-400', action: () => navigate('/upload') },
                        { title: 'Kira AI', desc: 'Voice Assistant', icon: FaMicrophone, color: 'text-red-400', action: () => navigate('/kira') },
                        { title: 'Learn Rights', desc: 'Constitution', icon: FaBook, color: 'text-green-400', action: () => navigate('/kyc') },
                        { title: 'Legal Code', desc: 'Specific Laws', icon: FaGavel, color: 'text-yellow-400', action: () => navigate('/kyl') },
                    ].map((item, i) => (
                        <motion.button
                            key={i}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={item.action}
                            className="p-6 rounded-2xl bg-neutral-900/40 border border-white/5 hover:bg-neutral-800 transition-all text-left group"
                        >
                            <div className={`mb-4 w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center ${item.color} group-hover:scale-110 transition-transform`}>
                                <item.icon className="w-6 h-6" />
                            </div>
                            <h3 className="text-lg font-bold text-white mb-1 group-hover:text-indigo-400 transition-colors">{item.title}</h3>
                            <p className="text-sm text-neutral-500">{item.desc}</p>
                        </motion.button>
                    ))}
                </div>
            </div>

            {/* Recent Sessions */}
            <div>
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                    <span className="w-2 h-8 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></span>
                    Recent Activity
                </h2>
                <div className="space-y-4">
                    {sessions.slice(0, 3).map(session => (
                        <div key={session.id} onClick={() => { switchSession(session.id); navigate('/chat'); }} className="group p-4 rounded-xl bg-neutral-900/30 border border-white/5 hover:border-white/10 cursor-pointer flex items-center justify-between transition-all">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-neutral-400 group-hover:bg-indigo-500/20 group-hover:text-indigo-400 transition-colors">
                                    <FaComments />
                                </div>
                                <div>
                                    <h4 className="font-bold text-neutral-200 group-hover:text-white">{session.title}</h4>
                                    <p className="text-xs text-neutral-500">{formatTimeAgo(session.updatedAt)}</p>
                                </div>
                            </div>
                            <FaArrowRight className="text-neutral-600 group-hover:text-white group-hover:translate-x-1 transition-all" />
                        </div>
                    ))}
                    {sessions.length === 0 && <p className="text-neutral-500 italic">No recent activity.</p>}
                </div>
            </div>
        </motion.div>
    );

    const DocumentsTab = () => (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
        >
            <h2 className="text-3xl font-black mb-8">Document History</h2>
            {loadingUploads ? (
                <div className="text-center py-20 text-neutral-500 animate-pulse">Loading records...</div>
            ) : uploads.length === 0 ? (
                <div className="text-center py-20 bg-neutral-900/30 rounded-3xl border border-white/5">
                    <FaFileUpload className="w-16 h-16 mx-auto text-neutral-700 mb-4" />
                    <h3 className="text-xl font-bold text-neutral-400">No Documents Found</h3>
                    <p className="text-neutral-600 mt-2">Upload a legal document to see it here.</p>
                    <button onClick={() => navigate('/upload')} className="mt-6 px-6 py-2 bg-indigo-600 rounded-full text-white font-bold hover:bg-indigo-500 transition-colors">Upload Now</button>
                </div>
            ) : (
                <div className="grid gap-4">
                    {uploads.map((doc, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="p-6 rounded-2xl bg-neutral-900/40 border border-white/5 hover:border-indigo-500/30 transition-all group"
                        >
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="flex items-start gap-4">
                                    <img src={doc.thumbnail || 'https://placehold.co/100x140/333/666?text=PDF'} alt="thumb" className="w-12 h-16 object-cover rounded shadow-md opacity-80 group-hover:opacity-100" />
                                    <div>
                                        <h3 className="font-bold text-lg text-white group-hover:text-indigo-400 transition-colors">{doc.filename}</h3>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {doc.doc_type && <span className="px-2 py-1 bg-white/5 rounded text-xs font-mono text-neutral-400 uppercase">{doc.doc_type}</span>}
                                            {doc.chunks_created && <span className="px-2 py-1 bg-white/5 rounded text-xs text-neutral-500">{doc.chunks_created} Chunks</span>}
                                        </div>
                                    </div>
                                </div>
                                <a
                                    href={doc.driveUrl}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-colors"
                                >
                                    <FaFileAlt /> View PDF
                                </a>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </motion.div>
    );

    return (
        <div className="flex min-h-screen bg-[#030303] text-white selection:bg-indigo-500/30 font-sans">
            {/* BACKGROUND EFFECTS */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-0 left-0 w-[50vw] h-[50vw] bg-indigo-900/10 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-0 right-0 w-[50vw] h-[50vw] bg-purple-900/10 rounded-full blur-[120px]"></div>
            </div>

            {/* SIDEBAR NAVIGATION - TABBED */}
            <motion.aside
                initial={{ x: -300 }}
                animate={{ x: isSidebarOpen ? 0 : -300 }}
                className={`fixed md:relative z-40 w-74 h-screen bg-black/80 backdrop-blur-xl border-r border-white/5 flex flex-col transition-all duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0 md:w-20 lg:w-72'}`}
            >
                <div className="p-8 border-b border-white/5 flex items-center justify-between">
                    <span className="text-2xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent hidden lg:block">NINE/FIVE</span>
                    <span className="text-2xl font-black text-indigo-500 lg:hidden">NF</span>
                    <button onClick={() => setIsSidebarOpen(false)} className="md:hidden text-white"><FaBars /></button>
                </div>

                <nav className="flex-1 py-8 space-y-2">
                    <SidebarItem id="overview" label="Overview" icon={FaHome} />
                    <SidebarItem id="documents" label="Documents" icon={FaFileAlt} />
                    <SidebarItem id="sessions" label="Sessions" icon={FaComments} />
                </nav>

                <div className="p-6 border-t border-white/5">
                    <button onClick={handleSignOut} className="w-full flex items-center gap-4 px-4 py-3 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all font-semibold">
                        <FaSignOutAlt />
                        <span className="hidden lg:inline">Sign Out</span>
                    </button>
                    <div className="mt-4 flex items-center gap-3 px-4">
                        <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center text-lg font-bold">
                            {user?.displayName?.charAt(0) || 'U'}
                        </div>
                        <div className="hidden lg:block overflow-hidden">
                            <p className="font-bold truncate text-sm">{user?.displayName}</p>
                            <p className="text-xs text-neutral-500 truncate">{user?.email}</p>
                        </div>
                    </div>
                </div>
            </motion.aside>

            {/* MAIN CONTENT AREA */}
            <main className="flex-1 relative z-10 h-screen overflow-y-auto">
                {/* Mobile Header Toggle */}
                {!isSidebarOpen && (
                    <button onClick={() => setIsSidebarOpen(true)} className="md:hidden absolute top-6 left-6 z-50 p-2 bg-neutral-800 rounded-lg text-white shadow-lg">
                        <FaBars />
                    </button>
                )}

                <div className="max-w-7xl mx-auto px-6 py-12 md:px-12">
                    <header className="mb-12 flex justify-between items-end">
                        <div>
                            <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-2">
                                {activeTab === 'overview' ? greeting : activeTab === 'documents' ? 'Archives' : 'Consultations'}
                            </h1>
                            <p className="text-lg text-neutral-400">
                                {activeTab === 'overview' ? `Welcome back, ${user?.displayName?.split(' ')[0]}` : activeTab === 'documents' ? 'Manage your uploaded legal documents' : 'Your history of legal consultations'}
                            </p>
                        </div>
                        {activeTab === 'overview' && (
                            <button onClick={() => fetchUploads()} className="hidden md:block px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 text-xs font-bold uppercase tracking-widest text-neutral-500 transition-colors">
                                Refresh Data
                            </button>
                        )}
                    </header>

                    {activeTab === 'overview' && <OverviewTab />}
                    {activeTab === 'documents' && <DocumentsTab />}
                    {activeTab === 'sessions' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {sessions.map(s => (
                                <motion.div key={s.id} onClick={() => { switchSession(s.id); navigate('/chat'); }} whileHover={{ y: -5 }} className="bg-neutral-900/40 p-6 rounded-2xl border border-white/5 cursor-pointer hover:border-indigo-500/30">
                                    <h3 className="font-bold text-lg mb-2">{s.title || 'Untitled'}</h3>
                                    <p className="text-xs text-neutral-500 mb-4">{formatTimeAgo(s.updatedAt)}</p>
                                    <div className="flex justify-between items-center">
                                        <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${s.persona === 'kira' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>{s.persona || 'Default'}</span>
                                        <button onClick={(e) => handleDeleteSession(e, s.id)} className="text-neutral-600 hover:text-red-400"><FaTrash /></button>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
