import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2, Calendar, RefreshCw } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import Alert from "../alert";

const AnalysisHistory = () => {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const navigate = useNavigate();

  // Validate individual history item
  const validateHistoryItem = (item) => {
    const requiredFields = [
      "video_name",
      "created_at",
      "sentiment",
      "overall_polarity",
      "profanity_level",
      "profanity_count",
    ];

    const missingFields = requiredFields.filter(
      (field) => !item.hasOwnProperty(field)
    );
    if (missingFields.length > 0) {
      throw new Error(
        `Invalid history item: Missing fields: ${missingFields.join(", ")}`
      );
    }

    // Validate data types
    if (typeof item.video_name !== "string")
      throw new Error("video_name must be a string");
    if (!Date.parse(item.created_at))
      throw new Error("created_at must be a valid date");
    if (typeof item.sentiment !== "string")
      throw new Error("sentiment must be a string");
    if (typeof item.overall_polarity !== "number")
      throw new Error("overall_polarity must be a number");
    if (typeof item.profanity_level !== "string")
      throw new Error("profanity_level must be a string");
    if (typeof item.profanity_count !== "number")
      throw new Error("profanity_count must be a number");

    return true;
  };

  // Validate response data
  const validateResponseData = (data) => {
    if (!Array.isArray(data)) {
      throw new Error("Response data must be an array");
    }

    data.forEach((item, index) => {
      try {
        validateHistoryItem(item);
      } catch (err) {
        throw new Error(`Invalid item at index ${index}: ${err.message}`);
      }
    });

    return true;
  };

  const handleError = useCallback((error, context = "") => {
    const errorMessage = error?.message || "An unexpected error occurred";
    console.error(`${context}: ${errorMessage}`, error);
    setError(`${context}: ${errorMessage}`);
    setIsLoading(false);
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      setIsLoading(true);
      setError("");

      const apiKey = localStorage.getItem("apiKey");
      if (!apiKey) {
        navigate("/login");
        return;
      }

      const response = await fetch(
        `https://sensiwithme.my.id/api/analysis_history`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${apiKey}`,
            Accept: "application/json",
          },
          credentials: "include",
        }
      );

      // First check if the response is JSON
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Server returned non-JSON response");
      }

      const responseData = await response.json();

      // Check for error status in response
      if (!response.ok) {
        throw new Error(
          responseData.message || `Server error (${response.status})`
        );
      }

      // Validate response structure
      if (!responseData.data || !Array.isArray(responseData.data)) {
        throw new Error(
          "Invalid response format: missing or invalid data array"
        );
      }

      // Validate and transform each history item
      const validatedData = responseData.data
        .map((item) => {
          if (!item.video_name || !item.created_at) {
            console.warn("Invalid history item:", item);
            return null;
          }

          return {
            video_name: item.video_name,
            created_at: new Date(item.created_at),
            sentiment: item.sentiment || "unknown",
            overall_polarity: parseFloat(item.overall_polarity || 0),
            profanity_level: item.profanity_level || "none",
            profanity_count: parseInt(item.profanity_count || 0),
          };
        })
        .filter(Boolean); // Remove any null items

      setHistory(validatedData);
      setError("");
    } catch (err) {
      handleError(err, "Failed to fetch history");
    } finally {
      setIsLoading(false);
    }
  }, [navigate, handleError]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const getSentimentColor = useCallback((sentiment) => {
    const colors = {
      positive: "bg-green-100 text-green-800",
      negative: "bg-red-100 text-red-800",
      neutral: "bg-yellow-100 text-yellow-800",
    };
    return colors[sentiment?.toLowerCase()] || "bg-gray-100 text-gray-800";
  }, []);

  const LoadingState = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-center">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        <span>Loading analysis history...</span>
      </div>
    </div>
  );

  const ErrorState = () => (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <Alert type="error" message={error} />
      <div className="flex space-x-4">
        <button
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          onClick={() => navigate("/dashboard")}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Return to Dashboard
        </button>
        <button
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          onClick={() => {
            setRetryCount((prev) => prev + 1);
            fetchHistory();
          }}
          disabled={isLoading}
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
          />
          {isLoading ? "Retrying..." : "Retry"}
        </button>
      </div>
    </div>
  );

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState />;

  return (
    <div className="bg-white rounded-lg shadow max-w-6xl mx-auto">
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-2xl font-bold">Analysis History</h2>
        <button
          onClick={() => navigate("/dashboard")}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </button>
      </div>
      <div className="p-6">
        {history.length === 0 ? (
          <Alert
            type="info"
            message="No analysis history found. Try uploading a video first."
          />
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Video Name</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Sentiment</TableHead>
                  <TableHead className="text-right">Polarity</TableHead>
                  <TableHead>Profanity Level</TableHead>
                  <TableHead className="text-right">Profanity Count</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((result, index) => (
                  <TableRow key={`${result.video_name}-${index}`}>
                    <TableCell className="font-medium">
                      {result.video_name}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-4 h-4" />
                        <span>
                          {new Date(result.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span
                        className={`px-2 py-1 rounded-full text-sm font-medium ${getSentimentColor(
                          result.sentiment
                        )}`}
                      >
                        {result.sentiment}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      {result.overall_polarity?.toFixed(2)}
                    </TableCell>
                    <TableCell>{result.profanity_level}</TableCell>
                    <TableCell className="text-right">
                      {result.profanity_count}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisHistory;
