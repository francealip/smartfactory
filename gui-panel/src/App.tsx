import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DataManager from "./api/PersistentDataManager";
import Home from "./components/Home";
import LoginForm from "./components/LoginForm";

const App = () => {
    // User authentication state ---  set to true for development purposes
    const [isAuthenticated, setIsAuthenticated] = useState(process.env.NODE_ENV === 'development');
    const [userId, setUserId] = useState('');
    const [username, setUsername] = useState('');
    const [token, setToken] = useState<string | null>(null);
    const [role, setRole] = useState('');
    const [site, setSite] = useState('');

    // Loading state to track if data is still being initialized
    const [loading, setLoading] = useState(true);

    // Method to handle the login event
    const handleLogin = (userId: string, username: string, token: string, role: string, site: string) => {
        setIsAuthenticated(true);
        setUserId(userId);
        setUsername(username);
        setToken(token);
        setRole(role);
        setSite(site);
    };

    // Method to handle the logout event
    const handleLogout = () => {
        setIsAuthenticated(false);
        setUserId('');
        setUsername('');
        setToken(null);
        setRole('');
        setSite('');
    };

    // Initialize data and set loading to false once done
    async function initializeData() {
        try {
            const dataManager = DataManager.getInstance();
            await dataManager.initialize();
            console.log("Data initialization completed.");
            console.log("KPI List:", dataManager.getKpiList());
            console.log("Machine List:", dataManager.getMachineList());
        } catch (error) {
            console.error("Error during initialization:", error);
        } finally {
            setLoading(false);  // Ensure loading is false once data initialization is done
        }
    }

    // Call initializeData on component mount
    useEffect(() => {
        initializeData();
    }, []); // Empty dependency array means this will run only once on mount

    // Show loading screen while data is being initialized or user is not authenticated
    if (loading && !isAuthenticated) {
        return (
            <div className="loading-screen">
                <h1>Loading...</h1>
            </div>
        );
    }

    return (
        <Router>
            <div className="flex flex-col justify-center text-center min-h-screen bg-gray-200 font-bold">
                {isAuthenticated ? (
                    <Routes>
                        {/* Rotta principale per la dashboard */}
                        <Route
                            path="/*"
                            element={<Home userId={userId} username={username} role={role} token={token || ''} site={site}/>}
                        />
                        {/* Reindirizza qualsiasi rotta non valida */}
                        <Route path="*" element={<Navigate to="/"/>}/>
                    </Routes>
                ) : (
                    <Routes>
                        {/* Rotta per il login */}
                        <Route path="/" element={<LoginForm onLogin={handleLogin}/>}/>
                        {/* Reindirizza qualsiasi rotta non valida */}
                        <Route path="*" element={<Navigate to="/"/>}/>
                    </Routes>
                )}
            </div>
        </Router>
    );
};

export default App;
