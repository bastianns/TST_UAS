import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2, Upload, BarChart2, History } from "lucide-react";

const Dashboard = () => {
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const apiKey = localStorage.getItem("apiKey");
        if (!apiKey) {
          throw new Error("No API key found. Please log in again.");
        }

        const response = await fetch(
          "https://sensiwithme.my.id/api/check-session",
          {
            mode: "cors",
            headers: {
              Authorization: `Bearer ${apiKey}`,
              "Content-Type": "application/json",
            },
            credentials: "include",
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === "invalid") {
          throw new Error("Session invalid. Please log in again.");
        }

        setUserData({ username: data.username, apiKey });
      } catch (err) {
        setError(err.message || "An unexpected error occurred");
        localStorage.removeItem("apiKey");
        navigate("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [navigate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold text-gray-900">
                Welcome to Your Dashboard
              </h1>
              <button
                onClick={() => {
                  localStorage.removeItem("apiKey");
                  navigate("/login");
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Logout
              </button>
            </div>
          </div>
          <div className="p-6">
            {error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <h5 className="text-red-800 font-medium mb-1">Error</h5>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            ) : (
              userData && (
                <div className="space-y-4">
                  <div className="p-4 bg-white rounded-lg border border-gray-200">
                    <p className="text-sm font-medium text-gray-500">
                      Username
                    </p>
                    <p className="mt-1 text-lg font-semibold text-gray-900">
                      {userData.username}
                    </p>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200">
                    <p className="text-sm font-medium text-gray-500">API Key</p>
                    <p className="mt-1 font-mono text-sm text-gray-900 break-all">
                      {userData.apiKey}
                    </p>
                  </div>
                </div>
              )
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link to="/upload" className="block">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <div className="p-6">
                <div className="text-center">
                  <Upload className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Upload Video
                  </h3>
                  <p className="text-gray-500">
                    Upload new videos for sentiment analysis
                  </p>
                </div>
              </div>
            </div>
          </Link>

          <Link to="/results" className="block">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <div className="p-6">
                <div className="text-center">
                  <BarChart2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    View Results
                  </h3>
                  <p className="text-gray-500">
                    Check sentiment analysis results
                  </p>
                </div>
              </div>
            </div>
          </Link>

          <Link to="/history" className="block">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <div className="p-6">
                <div className="text-center">
                  <History className="h-12 w-12 text-purple-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    History
                  </h3>
                  <p className="text-gray-500">View your analysis history</p>
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
