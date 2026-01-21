import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
    HiUser,
    HiCog,
    HiLogout,
    HiChevronDown,
    HiSparkles
} from 'react-icons/hi';
import { useAuth } from '../context/AuthContext';

const UserProfile = () => {
    const { user, signOut } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);
    const navigate = useNavigate();

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSignOut = async () => {
        try {
            await signOut();
            navigate('/login');
        } catch (error) {
            console.error('Sign out error:', error);
        }
    };

    if (!user) return null;

    return (
        <div className="relative" ref={dropdownRef}>
            {/* User Avatar Button */}
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 glass px-3 py-2 rounded-xl hover:bg-white/10 transition-all duration-200"
            >
                {user.photoURL ? (
                    <img
                        src={user.photoURL}
                        alt={user.displayName}
                        className="w-8 h-8 rounded-full border-2 border-purple-400"
                    />
                ) : (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                        <HiUser className="text-white text-lg" />
                    </div>
                )}

                <div className="hidden md:block text-left">
                    <p className="text-sm font-medium text-white truncate max-w-[120px]">
                        {user.displayName || 'User'}
                    </p>
                    <p className="text-xs text-gray-400 truncate max-w-[120px]">
                        {user.email}
                    </p>
                </div>

                <HiChevronDown
                    className={`text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''
                        }`}
                />
            </motion.button>

            {/* Dropdown Menu */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 mt-2 w-64 glass-card rounded-xl shadow-2xl overflow-hidden z-50"
                    >
                        {/* User Info */}
                        <div className="p-4 border-b border-white/10">
                            <div className="flex items-center gap-3">
                                {user.photoURL ? (
                                    <img
                                        src={user.photoURL}
                                        alt={user.displayName}
                                        className="w-12 h-12 rounded-full border-2 border-purple-400"
                                    />
                                ) : (
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                                        <HiUser className="text-white text-xl" />
                                    </div>
                                )}

                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-white truncate">
                                        {user.displayName || 'User'}
                                    </p>
                                    <p className="text-xs text-gray-400 truncate">
                                        {user.email}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Menu Items */}
                        <div className="p-2">
                            <motion.button
                                whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.1)' }}
                                onClick={() => {
                                    navigate('/');
                                    setIsOpen(false);
                                }}
                                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-white transition-colors"
                            >
                                <HiSparkles className="text-lg text-purple-400" />
                                <span className="text-sm font-medium">Dashboard</span>
                            </motion.button>

                            <motion.button
                                whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.1)' }}
                                onClick={() => {
                                    navigate('/settings');
                                    setIsOpen(false);
                                }}
                                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-white transition-colors"
                            >
                                <HiCog className="text-lg text-blue-400" />
                                <span className="text-sm font-medium">Settings</span>
                            </motion.button>

                            <div className="my-2 border-t border-white/10" />

                            <motion.button
                                whileHover={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}
                                onClick={handleSignOut}
                                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-red-400 transition-colors"
                            >
                                <HiLogout className="text-lg" />
                                <span className="text-sm font-medium">Sign Out</span>
                            </motion.button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default UserProfile;
