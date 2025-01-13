import React, { useState } from 'react';
import { Loader } from 'lucide-react';
import Alert from '../alert';
import ProgressBar from '../ProgressBar';
import getConfig from '../../config';


const RegisterForm = ({ onRegister }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [registrationProgress, setRegistrationProgress] = useState(0);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError('');
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    setError('');
    setSuccessMessage('');
    setRegistrationProgress(25);

    try {
      setRegistrationProgress(50);
      const response = await fetch(`${config.BACKEND_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        }),
      });

      setRegistrationProgress(75);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      setRegistrationProgress(100);
      
      // Save API key and username in localStorage
      localStorage.setItem('apiKey', data.api_key);
      localStorage.setItem('username', formData.username);

      setSuccessMessage(data.message || 'Registration successful');

      // Call the onRegister callback with user data
      onRegister({
        username: formData.username,
        apiKey: data.api_key,
        ...data
      });

      // Clear form
      setFormData({ username: '', password: '', confirmPassword: '' });
    } catch (error) {
      setError(error.message);
      setRegistrationProgress(0);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-6 space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Register</h2>
      </div>

      {registrationProgress > 0 && (
        <div className="mb-4">
          <ProgressBar 
            progress={registrationProgress}
            color={registrationProgress === 100 ? 'green' : 'blue'}
            size="default"
          />
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Username input */}
        <div className="space-y-2">
          <label htmlFor="username" className="block text-sm font-medium">
            Username
          </label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 ${
              error && 'border-red-500'
            }`}
            placeholder="Choose a username"
            disabled={isLoading}
            required
          />
        </div>

        {/* Password input */}
        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 ${
              error && 'border-red-500'
            }`}
            placeholder="Create a password"
            disabled={isLoading}
            required
          />
        </div>

        {/* Confirm Password input */}
        <div className="space-y-2">
          <label htmlFor="confirmPassword" className="block text-sm font-medium">
            Confirm Password
          </label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 ${
              error && 'border-red-500'
            }`}
            placeholder="Confirm your password"
            disabled={isLoading}
            required
          />
        </div>

        {/* Error message */}
        {error && <Alert type="error" message={error} />}

        {/* Success message */}
        {successMessage && <Alert type="success" message={successMessage} />}

        {/* Submit button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <Loader className="animate-spin -ml-1 mr-2 h-4 w-4" />
              Registering...
            </span>
          ) : (
            'Register'
          )}
        </button>
      </form>
    </div>
  );
};

export default RegisterForm;