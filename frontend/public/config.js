export const getConfig = () => {
  // Get the current hostname
  const hostname = window.location.hostname;

  // Determine if we're in development
  const isDevelopment =
    process.env.NODE_ENV === "development" || hostname === "localhost";

  // Set backend URL based on environment
  const backendUrl = isDevelopment
    ? "http://localhost:5000"
    : "https://sensiwithme.my.id";

  return {
    BACKEND_URL: window.ENV?.REACT_APP_BACKEND_URL || backendUrl,
    ENV:
      window.ENV?.REACT_APP_ENV ||
      (isDevelopment ? "development" : "production"),
    ALLOWED_FILE_TYPES:
      window.ENV?.REACT_APP_ALLOWED_FILE_TYPES || "mp4,avi,mov",
    MAX_UPLOAD_SIZE: window.ENV?.REACT_APP_MAX_UPLOAD_SIZE || "100MB",
    API_TIMEOUT: 30000, // 30 seconds timeout
  };
};

export default getConfig;
