const getEnvironmentConfig = () => {
  // Check if running in browser
  const isClient = typeof window !== "undefined";
  
  // Helper function to safely get environment variable
  const getEnvVar = (key, defaultValue) => {
    return process.env[key] || 
           (isClient && window._env && window._env[key]) || 
           defaultValue;
  };

  // Base configuration
  const baseConfig = {
    BACKEND_URL: "https://sensiwithme.my.id",
    FRONTEND_URL: "https://sensiwithme.my.id",
    API_TIMEOUT: 30000,
    ALLOWED_FILE_TYPES: ["mp4", "avi", "mov"],
    MAX_UPLOAD_SIZE: 50 * 1024 * 1024, // 50MB in bytes
    IS_DEVELOPMENT: process.env.NODE_ENV === "development"
  };

  // If running in browser, attempt to override with environment variables
  if (isClient) {
    return {
      ...baseConfig,
      BACKEND_URL: getEnvVar('REACT_APP_BACKEND_URL', baseConfig.BACKEND_URL),
      FRONTEND_URL: getEnvVar('REACT_APP_FRONTEND_URL', baseConfig.FRONTEND_URL),
      ALLOWED_FILE_TYPES: (getEnvVar('REACT_APP_ALLOWED_FILE_TYPES', 'mp4,avi,mov'))
        .split(',')
        .map(type => type.trim()),
      MAX_UPLOAD_SIZE: parseInt(getEnvVar('REACT_APP_MAX_UPLOAD_SIZE', '50')) * 1024 * 1024,
      IS_DEVELOPMENT: process.env.NODE_ENV === "development"
    };
  }

  // Return base config for server-side rendering
  return baseConfig;
};

export const config = getEnvironmentConfig();