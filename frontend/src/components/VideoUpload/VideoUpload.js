import React, { useState, useEffect } from 'react';
import { Upload, Loader } from 'lucide-react';
import Alert from '../alert';
import { useNavigate } from 'react-router-dom';
import { uploadVideo, isAuthenticated } from '../../utils/api';

const VideoUpload = () => {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  // Check authentication on component mount
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login', { state: { returnUrl: '/upload' } });
    }
  }, [navigate]);

  const allowedTypes = ['video/mp4', 'video/avi', 'video/mov'];
  const maxSize = 100 * 1024 * 1024; // 100MB

  const validateFile = (file) => {
    if (!file) return 'Please select a file.';
    if (!allowedTypes.includes(file.type)) {
      return 'Invalid file type. Only MP4, AVI, and MOV files are allowed.';
    }
    if (file.size > maxSize) {
      return 'File size too large. Maximum size is 100MB.';
    }
    return null;
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setError('');
    setSuccess('');

    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setFile(null);
      e.target.value = '';
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
  
    if (!isAuthenticated()) {
      setError('Session expired. Please log in again.');
      navigate('/login', { state: { returnUrl: '/upload' } });
      return;
    }
  
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }
  
    setIsLoading(true);
    setError('');
    setSuccess('');
  
    try {
      console.log('Starting upload for file:', file.name);
      const response = await uploadVideo(file);
  
      if (response.error) {
        throw new Error(response.error);
      }
  
      if (response.status === 'error' && response.message.includes('Dropbox')) {
        setError('Error connecting to storage service. Please try again later.');
        return;
      }
  
      setSuccess('Video analysis complete!');
      navigate('/results', { state: { sentimentResult: response.sentiment_results } });
  
      setFile(null);
      const fileInput = document.getElementById('video-upload');
      if (fileInput) fileInput.value = '';
    } catch (error) {
      console.error('Upload failed:', error);
      
      if (error.status === 401) {
        setError('Session expired. Please log in again.');
        navigate('/login', { state: { returnUrl: '/upload' } });
      } else if (error.message.includes('Dropbox')) {
        setError('Storage service error. Please try again later.');
      } else {
        setError(error.message || 'Upload failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-6 space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Video Upload</h2>
        <p className="text-gray-600 mt-2">Upload a video for sentiment analysis</p>
      </div>

      <form onSubmit={handleUpload} className="space-y-4">
        <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
          <input
            type="file"
            id="video-upload"
            accept=".mp4,.avi,.mov"
            onChange={handleFileChange}
            className="hidden"
          />
          <label
            htmlFor="video-upload"
            className="flex flex-col items-center cursor-pointer"
          >
            <Upload className="w-12 h-12 text-gray-400" />
            <span className="mt-2 text-sm text-gray-500">
              {file ? file.name : 'Click to upload video'}
            </span>
            <span className="mt-1 text-xs text-gray-400">
              MP4, AVI, or MOV (max 100MB)
            </span>
          </label>
        </div>

        {error && <Alert type="error" message={error} />}
        {success && <Alert type="success" message={success} />}

        <button
          type="submit"
          disabled={isLoading || !file}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <Loader className="animate-spin -ml-1 mr-2 h-4 w-4" />
              Processing...
            </span>
          ) : (
            'Upload & Analyze'
          )}
        </button>
      </form>
    </div>
  );
};

export default VideoUpload;
