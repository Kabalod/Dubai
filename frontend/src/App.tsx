import React from "react";
import { BrowserRouter as Router } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import Routes from "@/modules/routes";
import Header from "@/components/header/Header";
import PageLayout from "@/components/layout/PageLayout";

function App() {
    return (
        <AuthProvider>
            <Router>
                <Header />
                <PageLayout>
                    <Routes />
                </PageLayout>
            </Router>
        </AuthProvider>
    );
}

export default App;
