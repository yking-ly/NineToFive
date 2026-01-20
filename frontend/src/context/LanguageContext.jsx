import { createContext, useContext, useState, useEffect } from 'react';
import { getApiUrl } from '../utils/apiConfig';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    // Default to 'en'
    const [language, setLanguage] = useState('en');
    // Store for fetched translations
    const [translations, setTranslations] = useState({});
    // Loading state for skeleton UI
    const [isLoading, setIsLoading] = useState(true);

    // Initial load and language switch handler
    useEffect(() => {
        const fetchTranslations = async () => {
            setIsLoading(true);
            try {
                // Determine API URL (using utils or default)
                // Assuming simple relative path or localhost for dev if apiConfig logic is complex
                // But getApiUrl returns the base.
                const baseUrl = getApiUrl();
                const response = await fetch(`${baseUrl}/api/translations/${language}`);
                if (!response.ok) throw new Error('Failed to load translations');

                const data = await response.json();
                setTranslations(data);
            } catch (error) {
                console.error("Translation load error:", error);
                // Fallback to English if fetch fails? 
                // We'll keep existing translations if any, or just empty to trigger rough state
            } finally {
                // Short delay to smooth out the skeleton transition if response is too fast
                // ensuring the user actually sees the effect they requested
                // (Backend has 0.5s delay, so this is just cleanup)
                setIsLoading(false);
            }
        };

        fetchTranslations();
    }, [language]);

    const changeLanguage = (newLang) => {
        setLanguage(newLang);
    };

    // 't' is the current dictionary
    const t = translations;

    return (
        <LanguageContext.Provider value={{ language, setLanguage, changeLanguage, t, isLoading }}>
            {children}
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => useContext(LanguageContext);
