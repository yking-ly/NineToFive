export const DEFAULT_API_URL = 'http://127.0.0.1:5000';

export const getApiUrl = () => {
    return localStorage.getItem('server_url') || DEFAULT_API_URL;
};

export const setApiUrl = (url) => {
    localStorage.setItem('server_url', url);
};
