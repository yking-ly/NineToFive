import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FcGoogle } from 'react-icons/fc';
import { HiSparkles } from 'react-icons/hi2';
import { useAuth } from '../context/AuthContext';

const Login = () => {
    const { user, signInWithGoogle, loading } = useAuth();
    const navigate = useNavigate();
    const [isSigningIn, setIsSigningIn] = useState(false);

    // Redirect if already logged in
    useEffect(() => {
        if (user && !loading) {
            navigate('/');
        }
    }, [user, loading, navigate]);

    const handleGoogleSignIn = async () => {
        setIsSigningIn(true);
        try {
            await signInWithGoogle();
        } catch (error) {
            console.error('Sign in error:', error);
        } finally {
            setIsSigningIn(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full"
                />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4 overflow-hidden relative">
            {/* Animated background elements */}
            <div className="absolute inset-0 overflow-hidden">
                <motion.div
                    animate={{
                        scale: [1, 1.2, 1],
                        rotate: [0, 180, 360],
                    }}
                    transition={{
                        duration: 20,
                        repeat: Infinity,
                        ease: 'linear',
                    }}
                    className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-purple-500/20 to-transparent rounded-full blur-3xl"
                />
                <motion.div
                    animate={{
                        scale: [1.2, 1, 1.2],
                        rotate: [360, 180, 0],
                    }}
                    transition={{
                        duration: 25,
                        repeat: Infinity,
                        ease: 'linear',
                    }}
                    className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-blue-500/20 to-transparent rounded-full blur-3xl"
                />
            </div>

            {/* Login Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="relative z-10 w-full max-w-md"
            >
                <div className="glass-card p-8 md:p-12 rounded-3xl shadow-2xl">
                    {/* Logo/Icon */}
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                        className="flex justify-center mb-8"
                    >
                        <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg">
                            <HiSparkles className="text-4xl text-white" />
                        </div>
                    </motion.div>

                    {/* Title */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="text-center mb-8"
                    >
                        <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">
                            Welcome to
                            <span className="block bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent mt-2">
                                NineToFive Legal
                            </span>
                        </h1>
                        <p className="text-gray-300 text-sm md:text-base">
                            Your AI-powered legal assistant
                        </p>
                    </motion.div>

                    {/* Sign In Button */}
                    <motion.button
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleGoogleSignIn}
                        disabled={isSigningIn}
                        className="w-full bg-white hover:bg-gray-50 text-gray-800 font-semibold py-4 px-6 rounded-xl shadow-lg transition-all duration-200 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSigningIn ? (
                            <>
                                <motion.div
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                    className="w-6 h-6 border-3 border-gray-800 border-t-transparent rounded-full"
                                />
                                <span>Signing in...</span>
                            </>
                        ) : (
                            <>
                                <FcGoogle className="text-2xl" />
                                <span>Continue with Google</span>
                            </>
                        )}
                    </motion.button>

                    {/* Features */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="mt-8 space-y-3"
                    >
                        <div className="flex items-center gap-3 text-gray-300 text-sm">
                            <div className="w-2 h-2 bg-purple-400 rounded-full" />
                            <span>AI-powered legal document analysis</span>
                        </div>
                        <div className="flex items-center gap-3 text-gray-300 text-sm">
                            <div className="w-2 h-2 bg-blue-400 rounded-full" />
                            <span>Chat with Kira, your legal consultant</span>
                        </div>
                        <div className="flex items-center gap-3 text-gray-300 text-sm">
                            <div className="w-2 h-2 bg-green-400 rounded-full" />
                            <span>Secure session management</span>
                        </div>
                    </motion.div>

                    {/* Privacy Note */}
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.6 }}
                        className="mt-8 text-center text-xs text-gray-400"
                    >
                        By signing in, you agree to our Terms of Service and Privacy Policy.
                        Your data is encrypted and secure.
                    </motion.p>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
