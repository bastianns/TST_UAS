import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header = ({ isAuthenticated, onLogout }) => (
  <header className="Header">
    <div className="Header-content">
      <h1>Sentiment Analysis App</h1>
      <nav>
        <Link to="/">Welcome</Link>
        {!isAuthenticated && <Link to="/login">Login</Link>}
        {!isAuthenticated && <Link to="/register">Register</Link>}
        {isAuthenticated && <Link to="/upload">Upload Video</Link>}
        {isAuthenticated && (
          <button
            onClick={onLogout}
            className="logout-button"
          >
            Logout
          </button>
        )}
      </nav>
    </div>
  </header>
);

export default Header;
