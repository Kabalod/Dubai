// Centralized runtime configuration for API endpoints
// Prefer Vite env (`VITE_*`), fallback to generic env (`FRONTEND_API_URL`) injected via Vite define

const normalizeBase = (url: string) => url.replace(/\/$/, "");

// Production/Development API base URL configuration
// Берём из Vite env, иначе используем относительный путь (через Caddy прокси)
const envBase = (import.meta.env.VITE_FRONTEND_API_URL as string) || 
                (import.meta.env.VITE_API_BASE_URL as string) || 
                (import.meta.env.API_BASE_URL as string) || '';
export const API_BASE_URL: string = normalizeBase(String(envBase || ''));

// Google OAuth Client ID для frontend
export const GOOGLE_CLIENT_ID: string = import.meta.env.VITE_GOOGLE_CLIENT_ID || 
                                       import.meta.env.GOOGLE_CLIENT_ID || '';

// Frontend URL для redirects
export const FRONTEND_URL: string = import.meta.env.VITE_FRONTEND_URL || 
                                   import.meta.env.FRONTEND_URL || 
                                   window.location.origin;

// Feature flags
const flag = (v: any): boolean => String(v).toLowerCase() === 'true' || v === true || v === '1';
export const DEMO_MODE: boolean = flag((import.meta.env as any).VITE_DEMO_MODE || (import.meta.env as any).DEMO_MODE || false);

console.log('🔧 Environment:', import.meta.env.MODE);
console.log('🔧 API_BASE_URL:', API_BASE_URL);
console.log('🔧 GOOGLE_CLIENT_ID:', GOOGLE_CLIENT_ID ? 'configured' : 'missing');



// Memory LLM removed from project - keeping URL for backwards compatibility but unused
// export const MEMORY_API_URL: string =
//     (import.meta.env.VITE_MEMORY_API_URL as string) || `${API_BASE_URL}/memory`;


