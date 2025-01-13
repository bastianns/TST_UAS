import axios from "axios";

// Load environment variables
const API_URL = "https://sensiwithme.my.id";

if (!API_URL) {
  console.error(
    "Error: REACT_APP_BACKEND_URL is not defined in environment variables. Check your .env file."
  );
}

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});

// Request Interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Attach API key if available
    if (config.url !== "/login" && config.url !== "/register") {
      const apiKey = localStorage.getItem("apiKey");
      if (apiKey) {
        config.headers["Authorization"] = `Bearer ${apiKey}`; // Use Authorization header
      }
    }
    return config;
  },
  (error) => {
    console.error("Request error:", error.message);
    return Promise.reject(error);
  }
);

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMessage = "An unexpected error occurred";

    if (error.response) {
      // Server responded with an error
      errorMessage =
        error.response.data?.error ||
        error.response.statusText ||
        "Server Error";
    } else if (error.request) {
      // Request was made but no response
      errorMessage =
        "No response from server. Please check your network connection.";
    } else {
      // Something went wrong during request setup
      errorMessage = error.message || "Request setup error";
    }

    return Promise.reject({
      error: errorMessage,
      status: error.response?.status,
    });
  }
);

// Utility Function: Validate Required Fields
const validateFields = (fields, values) => {
  for (const field of fields) {
    if (
      !values[field] ||
      (typeof values[field] === "string" && !values[field].trim())
    ) {
      throw new Error(`${field} is required.`);
    }
  }
};

// API Functions

// Register User
export const registerUser = async (username, email, password) => {
  try {
    validateFields(["username", "email", "password"], {
      username,
      email,
      password,
    });

    const response = await apiClient.post("/register", {
      username,
      email,
      password,
    });

    // Store API key on successful registration
    if (response.data.api_key) {
      localStorage.setItem("apiKey", response.data.api_key);
    }

    return response.data;
  } catch (error) {
    throw {
      error: error.error || error.message || "Registration failed",
      status: error.status,
    };
  }
};

// Login User
export const loginUser = async (username, password) => {
  try {
    validateFields(["username", "password"], { username, password });

    const response = await apiClient.post("/login", {
      username,
      password,
    });

    // Store API key on successful login
    if (response.data.api_key) {
      localStorage.setItem("apiKey", response.data.api_key);
    }

    return response.data;
  } catch (error) {
    throw {
      error: error.error || error.message || "Login failed",
      status: error.status,
    };
  }
};

// Upload Video
// Modify uploadVideo function in api.js
export const uploadVideo = async (file) => {
  try {
    // Validate file
    if (!file) {
      throw new Error("File is required");
    }

    const formData = new FormData();
    formData.append("file", file);

    // Add logging untuk debugging
    console.log("Uploading file:", file.name);
    console.log("File size:", file.size);
    console.log("File type:", file.type);

    const response = await apiClient.post("/api/upload_video", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      // Increase timeout for large files
      timeout: 120000, // 2 minutes
      // Add onUploadProgress untuk monitoring
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        console.log("Upload progress:", percentCompleted);
      },
    });

    return response.data;
  } catch (error) {
    console.error("Upload error details:", error);
    if (error.response) {
      console.error("Error response:", error.response.data);
    }
    throw {
      error: error.error || error.message || "Upload failed",
      status: error.status,
      details: error.response?.data,
    };
  }
};

// Dropbox Authorization
export const getDropboxAuthorizeUrl = async () => {
  try {
    const response = await apiClient.get("/dropbox/authorize");
    return response.data.authorize_url;
  } catch (error) {
    console.error("Dropbox authorization error:", error);
    throw {
      error:
        error.error || error.message || "Failed to get Dropbox authorize URL",
      status: error.status,
    };
  }
};

// Handle Dropbox Callback
export const handleDropboxCallback = async (code, redirectUri) => {
  try {
    const response = await apiClient.get("/dropbox/callback", {
      params: { code, redirect_uri: redirectUri },
    });

    return response.data;
  } catch (error) {
    throw {
      error:
        error.error || error.message || "Failed to handle Dropbox callback",
      status: error.status,
    };
  }
};

// Utility: Check if User is Authenticated
export const isAuthenticated = () => {
  return !!localStorage.getItem("apiKey");
};

// Utility: Logout
export const logout = () => {
  localStorage.removeItem("apiKey");
};

// Export Default Axios Instance
export default apiClient;
