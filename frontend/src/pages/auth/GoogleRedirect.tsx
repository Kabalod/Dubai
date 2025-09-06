import { useEffect } from 'react';

export default function GoogleRedirect() {
    useEffect(() => {
        // Немедленно дергаем backend для получения auth_url c редиректом
        const url = '/api/auth/google/login/?redirect=1';
        window.location.replace(url);
    }, []);

    return (
        <div style={{display:'grid',placeItems:'center',minHeight:'60vh'}}>
            <div style={{textAlign:'center'}}>
                <h2>Redirecting to Google…</h2>
                <p>Please wait. If nothing happens, <a href="/api/auth/google/login/?redirect=1">click here</a>.</p>
            </div>
        </div>
    );
}


