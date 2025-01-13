import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginForm from './components/LoginForm/LoginForm';
import RegisterForm from './components/RegisterForm/RegisterForm';
import VideoUpload from './components/VideoUpload/VideoUpload';
import SentimentResults from './components/SentimentResults/SentimentResults';
import DropboxCallback from './pages/DropboxCallback/DropboxCallback';
import Header from './components/Header/Header';
import WelcomePage from './pages/WelcomePage/WelcomePage';
import Dashboard from './pages/Dashboard/Dashboard';
import AnalysisHistory from './components/AnalysisHistory/AnalysisHistory';
import './styles/App.css';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [sentimentResults, setSentimentResults] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    const apiKey = localStorage.getItem('apiKey');
    const username = localStorage.getItem('username');
    if (apiKey && username) {
      setIsAuthenticated(true);
      setCurrentUser(username);
    }
  }, []);

  const handleLogin = (userData) => {
    localStorage.setItem('apiKey', userData.api_key);
    localStorage.setItem('username', userData.username);
    setIsAuthenticated(true);
    setCurrentUser(userData.username);
  };

  const handleLogout = () => {
    localStorage.removeItem('apiKey');
    localStorage.removeItem('username');
    setIsAuthenticated(false);
    setCurrentUser(null);
    setSentimentResults(null);
  };

  const handleSentimentResults = (results) => {
    setSentimentResults(results);
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header 
          isAuthenticated={isAuthenticated} 
          onLogout={handleLogout}
          username={currentUser} 
        />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route 
              path="/" 
              element={isAuthenticated ? <Navigate to="/dashboard" /> : <WelcomePage />} 
            />
            <Route
              path="/register"
              element={
                isAuthenticated ? (
                  <Navigate to="/dashboard" />
                ) : (
                  <RegisterForm onRegister={handleLogin} />
                )
              }
            />
            <Route
              path="/login"
              element={
                isAuthenticated ? (
                  <Navigate to="/dashboard" />
                ) : (
                  <LoginForm onLogin={handleLogin} />
                )
              }
            />
            <Route
              path="/dashboard"
              element={
                isAuthenticated ? (
                  <Dashboard username={currentUser} />
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
            <Route
              path="/upload"
              element={
                isAuthenticated ? (
                  <VideoUpload onAnalysisComplete={handleSentimentResults} />
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
            <Route
              path="/results"
              element={
                isAuthenticated ? (
                  <SentimentResults sentimentResults={sentimentResults} />
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
            <Route
              path="/history"
              element={
                isAuthenticated ? (
                  <AnalysisHistory username={currentUser} />
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
            <Route path="/callback" element={<DropboxCallback />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;