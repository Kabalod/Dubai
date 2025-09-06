import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService, User } from '../services/apiService'
import { DEMO_MODE } from '../config';

// ========================================
// Auth Context Types
// ========================================

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    register: (userData: RegisterData) => Promise<void>;
    logout: () => void;
    checkAuth: () => void;
    requestPasswordReset: (email: string) => Promise<void>;
    confirmPasswordReset: (email: string, password1: string, password2: string, token?: string) => Promise<void>;
}

interface RegisterData {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
}

interface AuthProviderProps {
    children: ReactNode;
}

// ========================================
// Create Context
// ========================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ========================================
// Auth Provider Component
// ========================================

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check authentication status on mount
    useEffect(() => {
        const performAuthCheck = () => {
            setIsLoading(true);

            try {
                console.log('🔐 Checking authentication...');
                console.log('🔐 DEMO_MODE from config:', import.meta.env.VITE_DEMO_MODE);

                // DEMO MODE: сразу создаем пользователя если режим включен
                if (import.meta.env.VITE_DEMO_MODE === 'true' || import.meta.env.DEMO_MODE === 'true') {
                    console.log('🎭 DEMO MODE detected, creating mock user...');
                    const mockUser = apiService.getCurrentUser();
                    setUser(mockUser);
                    localStorage.setItem('user', JSON.stringify(mockUser));
                    setIsLoading(false);
                    return;
                }

                const isAuth = apiService.isAuthenticated();
                console.log('🔐 Is authenticated:', isAuth);
                
                if (isAuth) {
                    const userData = apiService.getCurrentUser();
                    console.log('🔐 User data from storage:', userData);

                    // ✅ ИСПРАВЛЕНО: если токен есть, но пользователя нет - очищаем все (кроме демо режима)
                    if (!userData && !DEMO_MODE) {
                        console.log('⚠️ Valid token but no user data - clearing auth');
                        apiService.clearAuth();
                        setUser(null);
                    } else if (userData) {
                        setUser(userData);
                    } else if (DEMO_MODE) {
                        // DEMO MODE: пользователь должен быть, но его нет - создаем фейкового
                        console.log('🎭 DEMO MODE: Creating mock user...');
                        const mockUser = apiService.getCurrentUser();
                        setUser(mockUser);

                        // Также сохраняем в localStorage для надежности
                        localStorage.setItem('user', JSON.stringify(mockUser));
                        console.log('🎭 DEMO MODE: Mock user saved to localStorage');
                    }
                } else {
                    console.log('🔐 No valid authentication found');
                    setUser(null);
                }
            } catch (error) {
                console.error('❌ Auth check error:', error);
                // Очищаем авторизацию при ошибке (кроме демо режима)
                if (!DEMO_MODE) {
                    apiService.clearAuth();
                    setUser(null);
                } else {
                    // DEMO MODE: при ошибке создаем фейкового пользователя
                    console.log('🎭 DEMO MODE: Auth check error, creating mock user...');
                    const mockUser = apiService.getCurrentUser();
                    setUser(mockUser);
                }
            } finally {
                setIsLoading(false);
            }
        };
        
        performAuthCheck();
    }, []);

    const checkAuth = () => {
        setIsLoading(true);
        
        try {
            const isAuth = apiService.isAuthenticated();
            if (isAuth) {
                const userData = apiService.getCurrentUser();
                
                // ✅ ИСПРАВЛЕНО: проверяем данные пользователя
                if (!userData) {
                    console.log('⚠️ Valid token but no user data - clearing auth');
                    apiService.clearAuth();
                    setUser(null);
                } else {
                    setUser(userData);
                }
            } else {
                setUser(null);
            }
        } catch (error) {
            console.error('Auth check error:', error);
            apiService.clearAuth();
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (username: string, password: string): Promise<void> => {
        setIsLoading(true);
        
        try {
            const response = await apiService.login(username, password);
            setUser(response.user);
            
            // Show success message
            console.log('Login successful:', response.message);
            
        } catch (error: any) {
            console.error('Login error:', error);
            
            // Extract error message
            let errorMessage = 'Login failed';
            if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            throw new Error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (userData: RegisterData): Promise<void> => {
        setIsLoading(true);
        
        try {
            const response = await apiService.register(userData);
            setUser(response.user);
            
            console.log('Registration successful:', response.message);
            
        } catch (error: any) {
            console.error('Registration error:', error);
            
            // ✅ УЛУЧШЕННАЯ обработка ошибок регистрации
            let errorMessage = 'Registration failed';
            if (error.response?.data) {
                const errors = error.response.data;
                
                // Handle field-specific errors
                if (typeof errors === 'object') {
                    const errorMessages = [];
                    for (const [field, messages] of Object.entries(errors)) {
                        if (Array.isArray(messages)) {
                            // Специальная обработка для распространенных ошибок
                            if (field === 'email' && messages.some(msg => msg.includes('already exists'))) {
                                errorMessages.push('Пользователь с таким email уже зарегистрирован');
                            } else if (field === 'username' && messages.some(msg => msg.includes('already exists'))) {
                                errorMessages.push('Пользователь с таким именем уже существует');
                            } else {
                                errorMessages.push(`${field}: ${messages.join(', ')}`);
                            }
                        } else {
                            errorMessages.push(`${field}: ${messages}`);
                        }
                    }
                    errorMessage = errorMessages.join('; ');
                } else if (typeof errors === 'string') {
                    errorMessage = errors;
                }
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            throw new Error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        setIsLoading(true);
        
        try {
            apiService.logout();
            setUser(null);
            
            // Redirect to login page
            window.location.href = '/auth';
            
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const requestPasswordReset = async (email: string): Promise<void> => {
        setIsLoading(true);
        
        try {
            await apiService.requestPasswordReset(email);
            console.log('Password reset email sent successfully');
            
        } catch (error: any) {
            console.error('Password reset request error:', error);
            
            let errorMessage = 'Failed to send password reset email';
            if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            throw new Error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const confirmPasswordReset = async (email: string, password1: string, password2: string, token?: string): Promise<void> => {
        setIsLoading(true);
        
        try {
            await apiService.confirmPasswordReset(email, password1, password2, token);
            console.log('Password reset confirmed successfully');
            
        } catch (error: any) {
            console.error('Password reset confirm error:', error);
            
            let errorMessage = 'Failed to reset password';
            if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            throw new Error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    // ✅ ИСПРАВЛЕНО: проверяем И токен И пользователя
    const isAuthenticated = !!user && apiService.isAuthenticated();

    const value: AuthContextType = {
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        checkAuth,
        requestPasswordReset,
        confirmPasswordReset,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// ========================================
// Custom Hook
// ========================================

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

// ========================================
// Higher-Order Component for Protected Routes
// ========================================

interface ProtectedRouteProps {
    children: ReactNode;
    fallback?: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
    children,
    fallback
}) => {
    const { isAuthenticated, isLoading, user } = useAuth();

    console.log('🔒 ProtectedRoute check:', {
        isAuthenticated,
        isLoading,
        user: user ? { email: user.email, id: user.id } : null
    });

    if (isLoading) {
        console.log('⏳ ProtectedRoute: Loading...');
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        console.log('❌ ProtectedRoute: User not authenticated, showing fallback');
        return fallback || (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Access Denied</h2>
                    <p className="text-gray-600 mb-6">Please log in to access this page.</p>
                    <a
                        href="/auth"
                        className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                    >
                        Go to Login
                    </a>
                </div>
            </div>
        );
    }

    console.log('✅ ProtectedRoute: Access granted');
    return <>{children}</>;
};