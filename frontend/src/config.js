const getEnvironmentValue = (key, defaultValue) => {
  // Check environment variable in process.env
  if (process.env[`REACT_APP_${key}`]) {
    return process.env[`REACT_APP_${key}`];
  }

  // Check window.ENV for runtime config in browser
  if (window.ENV && window.ENV[`REACT_APP_${key}`]) {
    return window.ENV[`REACT_APP_${key}`];
  }

  // Use default value if not found
  return defaultValue;
};

export const getConfig = () => ({
  BACKEND_URL: getEnvironmentValue("BACKEND_URL", "https://sensiwithme.my.id/api"),
  ENV: getEnvironmentValue("ENV", "development"),
  ALLOWED_FILE_TYPES: getEnvironmentValue("ALLOWED_FILE_TYPES", "mp4,avi,mov"),
  MAX_UPLOAD_SIZE: getEnvironmentValue("MAX_UPLOAD_SIZE", "100MB"),
  API_TIMEOUT: 30000,
});

export default getConfig;
