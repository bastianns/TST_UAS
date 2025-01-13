import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2, Upload } from "lucide-react";
import { config } from "../../config/environment";

const SentimentResults = () => {
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchResults = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(
        () => controller.abort(),
        config.API_TIMEOUT
      );
  
      try {
        setIsLoading(true);
        setError("");
  
        const apiKey = localStorage.getItem("apiKey");
        if (!apiKey) {
          throw new Error("API key is missing. Please log in again.");
        }
  
        console.log("Fetching results from:", `${config.BACKEND_URL}/api/last_analysis`);
        console.log("API Key:", apiKey.substring(0, 10) + '...'); // Log partially for security
  
        const response = await fetch(`${config.BACKEND_URL}/api/last_analysis`, {
          method: "GET",
          headers: {
            Accept: "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          signal: controller.signal,
        });
  
        console.log("Response status:", response.status);
        
        const data = await response.json();
        console.log("Response data:", data);
  
        if (!response.ok) {
          if (response.status === 404) {
            console.warn("No analysis results found");
            setResults(null);
            return;
          }
          throw new Error(data.message || "Failed to fetch results");
        }
  
        setResults(data);
      } catch (err) {
        console.error("Detailed fetch error:", err);
        setError(err.message || "An unexpected error occurred");
      } finally {
        clearTimeout(timeoutId);
        setIsLoading(false);
      }
    };
  
    fetchResults();
  }, []);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-center p-8 bg-white rounded-lg shadow-lg">
          <Loader2 className="w-6 h-6 mr-2 animate-spin text-blue-600" />
          <span className="text-gray-700">Loading analysis results...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => navigate("/dashboard")}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
          <div className="text-center p-6">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              No Analysis Results
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              You haven't analyzed any videos yet. Upload a video to get
              started.
            </p>
          </div>
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => navigate("/dashboard")}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </button>
            <button
              onClick={() => navigate("/upload")}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
            >
              <Upload className="w-4 h-4 mr-2" />
              Upload Video
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Analysis Results</h1>
          <button
            onClick={() => navigate("/dashboard")}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </button>
        </div>

        <div className="grid gap-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <h2 className="text-lg font-medium mb-4">Video Details</h2>
            <p className="text-sm text-gray-600">
              Filename: {results.video_name}
            </p>
            <p className="text-sm text-gray-600">
              Analyzed: {new Date(results.created_at).toLocaleString()}
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h2 className="text-lg font-medium mb-4">Sentiment Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-white rounded-lg border border-gray-200">
                <p className="text-sm text-gray-500">Overall Sentiment</p>
                <p className="text-lg font-medium text-gray-900">
                  {results.sentiment}
                </p>
              </div>
              <div className="p-4 bg-white rounded-lg border border-gray-200">
                <p className="text-sm text-gray-500">Polarity Score</p>
                <p className="text-lg font-medium text-gray-900">
                  {results.overall_polarity?.toFixed(2) || "N/A"}
                </p>
              </div>
            </div>
          </div>

          {results.profanity_level && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h2 className="text-lg font-medium mb-4">Content Analysis</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-500">Profanity Level</p>
                  <p className="text-lg font-medium text-gray-900">
                    {results.profanity_level}
                  </p>
                </div>
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-500">Profanity Count</p>
                  <p className="text-lg font-medium text-gray-900">
                    {results.profanity_count || 0}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SentimentResults;
