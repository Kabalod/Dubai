import { useEffect, useState } from 'react';
import apiService from '@/services/apiService';

export default function AuthResult() {
    const [message, setMessage] = useState('Processing authentication…');

    useEffect(() => {
        try {
            const hash = window.location.hash || '';
            const params = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : hash);
            const access = params.get('access');
            const refresh = params.get('refresh');
            const error = params.get('error');

            if (error) {
                setMessage(`Authentication failed: ${error}`);
                return;
            }

            if (access && refresh) {
                localStorage.setItem('accessToken', access);
                localStorage.setItem('refreshToken', refresh);
                (async () => {
                    try {
                        const profile = await apiService.getProfile();
                        localStorage.setItem('user', JSON.stringify(profile));
                    } catch {
                        // fallback: минимальный объект, чтобы хедер показал состояние
                        if (!localStorage.getItem('user')) {
                            localStorage.setItem('user', JSON.stringify({ email: '', username: '' }));
                        }
                    } finally {
                        setMessage('Authenticated. Redirecting…');
                        setTimeout(() => window.location.replace('/'), 300);
                    }
                })();
            } else {
                setMessage('No tokens found in callback.');
            }
        } catch {
            setMessage('Unexpected error while processing auth result.');
        }
    }, []);

    return (
        <div style={{display:'grid',placeItems:'center',minHeight:'60vh'}}>
            <div style={{textAlign:'center'}}>
                <h2>{message}</h2>
                <p><a href="/">Back to Home</a></p>
            </div>
        </div>
    );
}


