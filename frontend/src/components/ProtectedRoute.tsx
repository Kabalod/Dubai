import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  console.log('🔒 ProtectedRoute check:', { 
    isAuthenticated, 
    hasUser: !!user, 
    isLoading, 
    currentPath: location.pathname 
  });

  // Показываем загрузку пока проверяем авторизацию
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authorization...</p>
        </div>
      </div>
    );
  }

  // Если НЕ авторизован ИЛИ нет данных пользователя - перенаправляем на /auth
  if (!isAuthenticated || !user) {
    console.log('🔒 Access denied - redirecting to /auth');
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  console.log('🔒 Access granted for user:', user.email);
  return <>{children}</>;
};

export default ProtectedRoute;
