import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: '/api/', // API的基础URL
  timeout: 10000, // 请求超时时间
});

apiClient.interceptors.request.use(
  (config) => {
    // 尝试获取当前活跃的学生或教师Token
    const studentToken = localStorage.getItem('studentAccessToken');
    const teacherToken = localStorage.getItem('teacherAccessToken');
    let token = null;

    // 逻辑调整：
    // 1. 如果有学生Token，就用学生Token。
    //    这覆盖了 'student/' 和 'teams/' (在学生登录时) 的场景。
    if (studentToken) {
      token = studentToken;
    }
    // 2. 如果没有学生Token，但有教师Token，就用教师Token。
    //    这覆盖了 'teacher/' 和 'teams/' (在教师登录时) 的场景。
    else if (teacherToken) {
      token = teacherToken;
    }
    // 3. 如果两者都没有，才使用管理员Token。
    else {
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