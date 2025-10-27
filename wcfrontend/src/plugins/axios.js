import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: '/api/', // API的基础URL
  timeout: 10000, // 请求超时时间
});

apiClient.interceptors.request.use(
  (config) => {
    const url = config.url || '';
    let token = null;

    if (url.startsWith('student/')) {
      // 如果是请求学生API, 就使用学生Token
      token = localStorage.getItem('studentAccessToken');
    } else if (url.startsWith('teacher/')) {
      token = localStorage.getItem('teacherAccessToken');
    }else {
      // 否则，默认使用管理员Token (适用于 'admin/' 开头的URL)
      token = localStorage.getItem('accessToken');
    }

    // 如果找到了对应的Token，就将其添加到请求头中
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- 改进的响应拦截器，能处理所有用户的登出 ---
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      // 如果是 401 错误，则清除所有可能的Token
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('studentAccessToken');
      localStorage.removeItem('studentRefreshToken');
      localStorage.removeItem('teacherAccessToken');
      localStorage.removeItem('teacherRefreshToken');

      // 动态导入 router 以避免循环依赖
      const router = (await import('../router')).default;

      // 跳转到统一的登录页
      router.push({ name: 'Login', query: { message: 'session-expired' } });
    }
    return Promise.reject(error);
  }
);

export default apiClient;