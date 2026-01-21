import { useNavigate, useLocation } from 'react-router-dom';
import { FaArrowLeft, FaHome } from 'react-icons/fa';
import { motion } from 'framer-motion';

export default function TopBar({ title, subtitle, transparent = false, children }) {
    const navigate = useNavigate();
    const location = useLocation();

    // Check if we are on the dashboard
    const isDashboard = location.pathname === '/' || location.pathname === '/dashboard';

    // If on dashboard, we might not want a back button, or maybe we do depending on design.
    // But user asked for "back button in the top bar of all pages".
    // Usually "all pages" implies pages *other* than the main landing.

    return (
        <header className={`relative z-50 px-6 py-4 flex items-center gap-4 ${transparent ? 'bg-transparent' : 'bg-[#030303]/80 backdrop-blur-xl border-b border-white/5'}`}>
            {!isDashboard && (
                <motion.button
                    whileHover={{ scale: 1.1, x: -3 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => navigate('/dashboard')}
                    className="p-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/5 text-white/80 hover:text-white transition-all shadow-lg"
                    title="Back to Dashboard"
                >
                    <FaArrowLeft />
                </motion.button>
            )}

            <div>
                {title && <h1 className="text-xl font-bold text-white tracking-tight">{title}</h1>}
                {subtitle && <p className="text-xs text-neutral-400 font-medium tracking-wide">{subtitle}</p>}
            </div>

            <div className="flex-1"></div>

            {children && <div className="flex items-center gap-4">{children}</div>}

            {/* Optional: Add user profile or extra actions here later */}
        </header>
    );
}
