import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { API_BASE_URL, DEMO_MODE } from '../config';

// ========================================
// API Configuration (base comes from env via src/config.ts)
// ========================================

class ApiService {
    private api: AxiosInstance;

    constructor() {
        // ✅ ИСПРАВЛЕНО: в продакшне используем прокси через Caddy для избежания CORS
        const baseURL = process.env.NODE_ENV === 'production' 
            ? '/api' // использует прокси Caddy
            : `${API_BASE_URL}/api`;
            
        this.api = axios.create({
            baseURL: baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        });

        console.log('🔧 ApiService initialized with baseURL:', baseURL);

        // Request interceptor to add auth token
        this.api.interceptors.request.use(
            (config) => {
                const token = localStorage.getItem('accessToken');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor to handle token refresh
        this.api.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;

                if (error.response?.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;

                    const refreshToken = localStorage.getItem('refreshToken');
                    if (refreshToken) {
                        try {
                            const response = await this.refreshToken(refreshToken);
                            localStorage.setItem('accessToken', response.data.access);
                            
                            // Retry original request with new token
                            originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
                            return this.api(originalRequest);
                        } catch (refreshError) {
                            // Refresh failed, logout user
                            this.logout();
                            window.location.href = '/auth';
                        }
                    } else {
                        // No refresh token, logout user
                        this.logout();
                        window.location.href = '/auth';
                    }
                }

                return Promise.reject(error);
            }
        );
    }

    // ========================================
    // Authentication Methods
    // ========================================

    async login(email: string, password: string) {
        console.log('🔑 ApiService login attempt with email:', email);
        
        const response = await this.api.post('/auth/login/', {
            username: email, // ✅ ИСПРАВЛЕНО: бекенд ожидает username, но передаем email
            password,
        });

        console.log('🔑 Login response from backend:', response.data);

        // ✅ ИСПРАВЛЕНО: поддерживаем разные форматы ответа от бекенда
        if (response.data?.access) {
            // Новый формат: { access, refresh, user }
            localStorage.setItem('accessToken', response.data.access);
            localStorage.setItem('refreshToken', response.data.refresh);
            localStorage.setItem('user', JSON.stringify(response.data.user));
            console.log('✅ Tokens saved (new format)');
        } else if (response.data?.tokens) {
            // Старый формат: { tokens: { access, refresh }, user }
            localStorage.setItem('accessToken', response.data.tokens.access);
            localStorage.setItem('refreshToken', response.data.tokens.refresh);
            localStorage.setItem('user', JSON.stringify(response.data.user));
            console.log('✅ Tokens saved (old format)');
        }

        return response.data;
    }

    async register(userData: {
        username: string;
        email: string;
        password: string;
        password_confirm: string;
        first_name?: string;
        last_name?: string;
    }) {
        const response = await this.api.post('/auth/register/', userData);

        if (response.data.tokens) {
            localStorage.setItem('accessToken', response.data.tokens.access);
            localStorage.setItem('refreshToken', response.data.tokens.refresh);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }

        return response.data;
    }

    async logout() {
        try {
            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken) {
                await this.api.post('/auth/logout/', {
                    refresh_token: refreshToken,
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
        }
    }

    async refreshToken(refreshToken: string) {
        return this.api.post('/auth/token/refresh/', {
            refresh: refreshToken,
        });
    }

    // ========================================
    // Stats API  
    // ========================================

    async getStats() {
        console.log('📊 ApiService.getStats() called');
        const response = await this.api.get('/stats/');
        console.log('📊 Stats response:', response.data);
        return response.data;
    }

    // ========================================
    // Properties API
    // ========================================

    async getProperties(params: {
        search?: string;
        property_type?: string;
        listing_type?: 'sale' | 'rent';
        min_price?: number;
        max_price?: number;
        bedrooms?: string;
        area?: string;
        limit?: number;
        offset?: number;
    } = {}) {
        const response = await this.api.get('/properties/', { params });
        return response.data;
    }

    async getAreas() {
        const response = await this.api.get('/areas/');
        return response.data;
    }

    async getBuildings(params: {
        area?: string;
        limit?: number;
        offset?: number;
    } = {}) {
        const response = await this.api.get('/buildings/', { params });
        return response.data;
    }

    // ========================================
    // Analytics API
    // ========================================

    async getAnalytics() {
        const response = await this.api.get('/analytics/');
        return response.data;
    }

    async getBuildingReports(params: {
        area?: string;
        bedrooms?: string;
        limit?: number;
        offset?: number;
    } = {}) {
        const response = await this.api.get('/reports/', { params });
        return response.data;
    }

    // ========================================
    // Health Check
    // ========================================

    async getHealthCheck() {
        const response = await this.api.get('/health/');
        return response.data;
    }

    // ========================================
    // New Authentication API (OTP-based)
    // ========================================

    async otpLogin(email: string, otp_code?: string): Promise<LoginResponse> {
        const response = await this.api.post('/auth/login/', {
            email,
            otp_code
        });
        
        if (response.data.access) {
            localStorage.setItem('accessToken', response.data.access);
            localStorage.setItem('refreshToken', response.data.refresh);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        
        return response.data;
    }

    async registerUser(userData: RegisterRequest): Promise<LoginResponse> {
        const response = await this.api.post('/auth/register/', userData);
        
        if (response.data.access) {
            localStorage.setItem('accessToken', response.data.access);
            localStorage.setItem('refreshToken', response.data.refresh);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        
        return response.data;
    }

    // ========================================
    // Password Reset API
    // ========================================

    async requestPasswordReset(email: string) {
        console.log('🔑 Requesting password reset for:', email);
        const response = await this.api.post('/auth/password/reset/', {
            email
        });
        console.log('🔑 Password reset requested:', response.data);
        return response.data;
    }

    async confirmPasswordReset(email: string, password1: string, password2: string, token?: string) {
        console.log('🔑 Confirming password reset for:', email);
        const response = await this.api.post('/auth/password/reset/confirm/', {
            email,
            password1,
            password2,
            token // Если бекенд требует токен из email
        });
        console.log('🔑 Password reset confirmed:', response.data);
        return response.data;
    }

    // ========================================
    // Profile API
    // ========================================

    async getProfile(): Promise<User> {
        const response = await this.api.get('/profile/me/');
        return response.data;
    }

    async updateProfile(profileData: Partial<User>): Promise<User> {
        const response = await this.api.put('/profile/me/', profileData);
        return response.data;
    }

    async partialUpdateProfile(profileData: Partial<User>): Promise<User> {
        const response = await this.api.patch('/profile/me/', profileData);
        return response.data;
    }

    // ========================================
    // Admin API
    // ========================================

    async getUsers(): Promise<User[]> {
        const response = await this.api.get('/admin/users/');
        return response.data;
    }

    async getPayments(): Promise<Payment[]> {
        const response = await this.api.get('/admin/payments/');
        return response.data;
    }

    // ========================================
    // User Reports API  
    // ========================================

    async getUserReports(): Promise<UserReportHistory[]> {
        const response = await this.api.get('/reports/history/');
        return response.data;
    }

    async generateReport(reportType: string, parameters: Record<string, any>): Promise<UserReportHistory> {
        const response = await this.api.post('/reports/generate/', {
            report_type: reportType,
            parameters
        });
        return response.data;
    }

    // ========================================
    // Utility Methods
    // ========================================

    private decodeJwtPayload(token: string): any | null {
        try {
            const part = token.split('.')[1];
            if (!part) return null;
            let base64 = part.replace(/-/g, '+').replace(/_/g, '/');
            const pad = base64.length % 4;
            if (pad === 2) base64 += '==';
            else if (pad === 3) base64 += '=';
            const json = atob(base64);
            return JSON.parse(json);
        } catch {
            return null;
        }
    }

    isAuthenticated(): boolean {
        // DEMO MODE: всегда возвращаем true
        if (DEMO_MODE) {
            console.log('🎭 DEMO MODE: Always authenticated (DEMO_MODE=true)');
            return true;
        }

        const token = localStorage.getItem('accessToken');
        if (!token) return false;
        try {
            if (token.length < 10) return false;
            const payload = this.decodeJwtPayload(token);
            if (!payload) return true; // дадим шанс интерсептору/refresh
            const currentTime = Math.floor(Date.now() / 1000);
            if (payload.exp && payload.exp < currentTime) {
                console.log('Token expired, clearing auth');
                this.clearAuth();
                return false;
            }
            return true;
        } catch (error) {
            console.error('Token validation error:', error);
            return true;
        }
    }

    isDemoMode(): boolean {
        return DEMO_MODE;
    }

    getCurrentUser() {
        // DEMO MODE: возвращаем фейкового премиум пользователя
        if (DEMO_MODE) {
            console.log('🎭 DEMO MODE: Returning mock premium user');
            return {
                id: 999,
                username: 'demo_premium_user',
                email: 'demo@premium.user',
                first_name: 'Demo',
                last_name: 'Premium',
                is_premium: true,
                subscription_type: 'premium',
                subscription_status: 'active',
                subscription_end_date: '2026-12-31',
                properties_count: 25,
                reports_count: 15
            };
        }

        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    // Полная очистка авторизации (для отладки)
    clearAuth() {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken'); 
        localStorage.removeItem('user');
        console.log('🔐 Auth cleared - user logged out');
    }

    setAuthToken(token: string) {
        localStorage.setItem('accessToken', token);
    }

    getAuthToken(): string | null {
        return localStorage.getItem('accessToken');
    }
}

// ========================================
// Export singleton instance
// ========================================

export const apiService = new ApiService();
export default apiService;

// ========================================
// Types for TypeScript
// ========================================

export interface Property {
    id: string;
    title: string;
    display_address: string;
    bedrooms: string;
    bathrooms: string;
    price: number;
    price_currency: string;
    property_type: string;
    listing_type: 'sale' | 'rent';
    added_on: string;
    latitude?: number;
    longitude?: number;
    numeric_area?: number;
    furnishing?: string;
    broker?: string;
    agent?: string;
    verified: boolean;
}

export interface Area {
    id: number;
    name: string;
    verified_value: string;
    numbers_of_processed_ads: number;
    sum_number_of_days_for_all_ads: number;
}

export interface Building {
    id: number;
    name: string;
    area: Area;
    latitude?: number;
    longitude?: number;
    numbers_of_processed_rent_ads: number;
    numbers_of_processed_sale_ads: number;
}

export interface Analytics {
    total_properties: number;
    total_sale_properties: number;
    total_rent_properties: number;
    total_buildings: number;
    total_areas: number;
    avg_sale_price?: number;
    avg_rent_price?: number;
    properties_by_type: Record<string, number>;
    properties_by_bedrooms: Record<string, number>;
    properties_by_area: Record<string, number>;
}

export interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    is_staff: boolean;
    is_superuser: boolean;
    date_joined: string;
    last_login?: string;
    groups: string[];
    user_permissions: string[];
}

export interface OTPCode {
    id: number;
    email: string;
    code: string;
    created_at: string;
    expires_at: string;
    is_used: boolean;
    attempts: number;
}

export interface Payment {
    id: number;
    user: number;
    stripe_charge_id: string;
    amount: string;
    currency: string;
    status: string;
    created_at: string;
    updated_at: string;
    description?: string;
}

export interface PaymentEventAudit {
    id: number;
    created_at: string;
    updated_at: string;
    provider: string;
    event_type: string;
    event_id: string;
    payload: Record<string, any>;
    processed_at?: string;
    status: string;
    error_message?: string;
    related_payment?: number;
}

export interface UserReportHistory {
    id: number;
    user: number;
    report_type: string;
    generated_at: string;
    file_path: string;
    parameters: Record<string, any>;
}

export interface AuthTokens {
    access: string;
    refresh: string;
}

export interface RegisterRequest {
    username: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
}

export interface OTPLoginRequest {
    email: string;
    otp_code?: string;
}

export interface LoginResponse {
    access: string;
    refresh: string;
    user: User;
}