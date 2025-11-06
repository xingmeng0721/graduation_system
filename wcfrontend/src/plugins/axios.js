// src/plugins/axios.js

import axios from 'axios';
import router from '../router';
import { ElMessage } from 'element-plus';

const apiClient = axios.create({
  baseURL: '/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

let isRefreshing = false;
let failedQueue = [];

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

const getCurrentAuth = () => {
  const adminToken = localStorage.getItem('accessToken');
  const studentToken = localStorage.getItem('studentAccessToken');
  const teacherToken = localStorage.getItem('teacherAccessToken');

  if (adminToken) {
    return {
      token: adminToken,
      type: 'admin',
      refresh: localStorage.getItem('refreshToken')
    };
  }
  if (studentToken) {
    return {
      token: studentToken,
      type: 'student',
      refresh: localStorage.getItem('studentRefreshToken')
    };
  }
  if (teacherToken) {
    return {
      token: teacherToken,
      type: 'teacher',
      refresh: localStorage.getItem('teacherRefreshToken')
    };
  }

  return null;
};

const refreshAuthToken = async (userType, refreshToken) => {
  const endpoints = {
    admin: '/api/admin/token/refresh/',
    student: '/api/student/token/refresh/',
    teacher: '/api/teacher/token/refresh/'
  };

  try {
    const response = await axios.post(endpoints[userType], {
      refresh: refreshToken
    });

    const { access } = response.data;

    if (userType === 'admin') {
      localStorage.setItem('accessToken', access);
    } else if (userType === 'student') {
      localStorage.setItem('studentAccessToken', access);
    } else if (userType === 'teacher') {
      localStorage.setItem('teacherAccessToken', access);
    }

    return access;
  } catch (error) {
    throw error;
  }
};

const clearAllTokens = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('studentAccessToken');
  localStorage.removeItem('studentRefreshToken');
  localStorage.removeItem('teacherAccessToken');
  localStorage.removeItem('teacherRefreshToken');
  localStorage.removeItem('lastLoginType');
};

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

apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers['Authorization'] = 'Bearer ' + token;
            return apiClient(originalRequest);
          })
          .catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const auth = getCurrentAuth();

      if (!auth || !auth.refresh) {
        isRefreshing = false;
        clearAllTokens();
        ElMessage.error('登录已过期，请重新登录');
        router.push({ name: 'Login', query: { message: 'session-expired' } });
        return Promise.reject(error);
      }

      try {
        const newAccessToken = await refreshAuthToken(auth.type, auth.refresh);
        originalRequest.headers['Authorization'] = 'Bearer ' + newAccessToken;
        processQueue(null, newAccessToken);
        isRefreshing = false;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        clearAllTokens();
        ElMessage.error('登录已过期，请重新登录');
        router.push({ name: 'Login', query: { message: 'session-expired' } });
        return Promise.reject(refreshError);
      }
    }

    if (error.response?.status === 403) {
      ElMessage.error('您没有权限访问该资源');
    } else if (error.response?.status === 404) {
      ElMessage.error('请求的资源不存在');
    } else if (error.response?.status >= 500) {
      ElMessage.error('服务器错误，请稍后重试');
    }

    return Promise.reject(error);
  }
);

export default apiClient;