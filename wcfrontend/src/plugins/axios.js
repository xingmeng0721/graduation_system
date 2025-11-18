import axios from 'axios';
import router from '../router';
import { ElMessage } from 'element-plus';

const TOKEN_KEYS = {
  admin: { access: 'accessToken', refresh: 'refreshToken' },
  student: { access: 'studentAccessToken', refresh: 'studentRefreshToken' },
  teacher: { access: 'teacherAccessToken', refresh: 'teacherRefreshToken' },
};

const apiClient = axios.create({
  baseURL: '/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue = [];

/**
 * Queue pending requests during token refresh
 */
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

/**
 * Get currently authenticated user's token and refresh token from localStorage
 */
const getCurrentAuth = () => {
  for (const type in TOKEN_KEYS) {
    const { access, refresh } = TOKEN_KEYS[type];
    const accessToken = localStorage.getItem(access);
    if (accessToken) {
      return {
        token: accessToken,
        type,
        refresh: localStorage.getItem(refresh),
      };
    }
  }
  return null;
};

/**
 * Handle token refresh for a specific user type
 */
const refreshAuthToken = async (userType, refreshToken) => {
  const endpoints = {
    admin: '/api/admin/token/refresh/',
    student: '/api/student/token/refresh/',
    teacher: '/api/teacher/token/refresh/',
  };

  try {
    const response = await axios.post(endpoints[userType], { refresh: refreshToken });
    const { access } = response.data;

    // Update the access token in localStorage
    const { access: accessKey } = TOKEN_KEYS[userType];
    localStorage.setItem(accessKey, access);
    return access;
  } catch (error) {
    throw error;
  }
};

/**
 * Clear all tokens for all roles from localStorage
 */
const clearAllTokens = () => {
  Object.values(TOKEN_KEYS).forEach(({ access, refresh }) => {
    localStorage.removeItem(access);
    localStorage.removeItem(refresh);
  });
};

/**
 * Handle error response statuses
 */
const handleErrorResponse = (status, defaultMessage) => {
  const messages = {
    401: '登录已过期，请重新登录',
    403: '您没有权限访问该资源',
    404: '请求的资源不存在',
    500: '服务器错误，请稍后再试',
  };

  const message = messages[status] || defaultMessage || '发生了未知错误';
  ElMessage.error(message);

  // Additional handling for specific codes
  if (status === 401 || status === 403) {
    clearAllTokens();
    router.push({ name: 'Login', query: { message: 'session-expired' } });
  }
};

/**
 * Request interceptor to add Authorization header
 */
apiClient.interceptors.request.use(
  config => {
    const auth = getCurrentAuth();
    if (auth && auth.token) {
      config.headers.Authorization = `Bearer ${auth.token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

/**
 * Response interceptor for error handling and token refresh logic
 */
apiClient.interceptors.response.use(
  response => response, // For successful responses
  async error => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      // If request is unauthorized and token needs a refresh
      if (isRefreshing) {
        // Queue subsequent requests
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const auth = getCurrentAuth();
      if (!auth || !auth.refresh) {
        // If no refresh token, clear auth and redirect to login
        isRefreshing = false;
        handleErrorResponse(401, '会话已过期，请重新登录');
        return Promise.reject(error);
      }

      try {
        // Refresh Token
        const newAccessToken = await refreshAuthToken(auth.type, auth.refresh);
        processQueue(null, newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null); // Notify queued requests of failure
        handleErrorResponse(401, '会话已过期，请重新登录');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle other response errors
    if ([403, 404, 500].includes(error.response?.status)) {
      handleErrorResponse(error.response.status);
    }

    return Promise.reject(error);
  }
);

export default apiClient;