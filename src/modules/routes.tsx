import { Routes, Route } from "react-router-dom";
import Auth from "@/pages/auth/Auth";
import HomePage from "@/pages/HomePage";
import MainDashboard from "@/pages/MainDashboard";
import NotFound from "@/pages/NotFound";
import Analytics from "@/pages/analytics/Analytics";
import Reports from "@/pages/Reports";
import Policy from "@/pages/Policy/Policy";
import Profile from "@/pages/Profile";
import Payment from "@/pages/Payment";
import PricingPage from "@/pages/PricingPage";
import ProtectedRoute from "@/components/ProtectedRoute";
import GoogleRedirect from "@/pages/auth/GoogleRedirect";
import AuthResult from "@/pages/auth/AuthResult";

export default function AppRoutes() {
    return (
        <Routes>
            {/* Публичные маршруты - доступны всем */}
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<MainDashboard />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/auth/google" element={<GoogleRedirect />} />
            <Route path="/auth/callback" element={<AuthResult />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/payment" element={<Payment />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/policy" element={<Policy />} />
            
            {/* Защищенные маршруты - только для авторизованных */}
            <Route path="/profile" element={
                <ProtectedRoute>
                    <Profile />
                </ProtectedRoute>
            } />

            {/* Тестовый маршрут для отладки */}
            <Route path="/debug" element={
                <div className="p-6 max-w-4xl mx-auto">
                    <h1 className="text-3xl font-bold mb-6">🔧 Debug Page</h1>

                    <div className="space-y-4">
                        <div className="p-4 bg-blue-50 border rounded-lg">
                            <h2 className="font-semibold mb-2">Navigation Test</h2>
                            <button
                                onClick={() => window.location.href = '/profile'}
                                className="bg-blue-500 text-white px-4 py-2 rounded mr-2"
                            >
                                Go to Profile (window.location)
                            </button>
                            <button
                                onClick={() => window.history.pushState(null, '', '/profile')}
                                className="bg-green-500 text-white px-4 py-2 rounded mr-2"
                            >
                                Go to Profile (pushState)
                            </button>
                        </div>

                        <div className="p-4 bg-yellow-50 border rounded-lg">
                            <h2 className="font-semibold mb-2">Environment Check</h2>
                            <p><strong>DEMO_MODE:</strong> {import.meta.env.VITE_DEMO_MODE || 'undefined'}</p>
                            <p><strong>Mode:</strong> {import.meta.env.MODE}</p>
                            <p><strong>User Agent:</strong> {navigator.userAgent}</p>
                        </div>

                        <div className="p-4 bg-red-50 border rounded-lg">
                            <h2 className="font-semibold mb-2">Console Logs</h2>
                            <p>Open browser console (F12) to see debug messages</p>
                            <button
                                onClick={() => {
                                    console.log('🧪 Debug test - Current location:', window.location.href);
                                    console.log('🧪 Debug test - DEMO_MODE:', import.meta.env.VITE_DEMO_MODE);
                                }}
                                className="bg-red-500 text-white px-4 py-2 rounded"
                            >
                                Log to Console
                            </button>
                        </div>
                    </div>
                </div>
            } />
            
            {/* 404 страница */}
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}
