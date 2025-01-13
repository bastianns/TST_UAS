import React from 'react';
import './WelcomePage.css';

const WelcomePage = () => (
  <div className="WelcomePage">
    <h1>Welcome to Sentiment Analysis</h1>
    <p>Analyze sentiments from your videos using our advanced AI.</p>
    <div className="actions">
      <a href="/login" className="button">Login</a>
      <a href="/register" className="button button-secondary">Register</a>
    </div>
  </div>
);

export default WelcomePage;
