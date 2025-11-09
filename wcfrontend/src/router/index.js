import { createRouter, createWebHistory } from 'vue-router';
// ✅ 1. 导入 ElMessage 组件本身
import { ElMessage } from 'element-plus';
// ✅ 2. 导入 ElMessage 的样式，否则弹窗会很丑
import 'element-plus/es/components/message/style/css';

import Login from '../components/login.vue';
import DashboardLayout from '../layouts/DashboardLayout.vue';
import UserList from '../pages/UserList.vue';
import RegisterUser from '../pages/RegisterUser.vue';
import StudentManagement from '../pages/StudentManagement.vue';
import StudentDashboard from '../layouts/StudentDashboard.vue';
import TeacherManagement from '../pages/TeacherManagement.vue';

import TeacherDashboard from '../layouts/TeacherDashboard.vue';
import TeacherProfile from "../pages/TeacherProfile.vue";
import AdminProfile from "../pages/AdminProfile.vue";


const routes = [
  // 默认路径重定向到统一登录页
  { path: '/', redirect: '/login' },

  // --- 统一登录路由 ---
  { path: '/login', name: 'Login', component: Login },

  // --- 管理员仪表盘 ---
  {
    path: '/dashboard',
    component: DashboardLayout,
    meta: { requiresAuth: true }, // 需要管理员权限
    children: [
      //{ path: '', name: 'DashboardWelcome', component: Welcome },
      { path: 'users', name: 'UserList', component: UserList },
        { path: 'profile', name: 'AdminProfile', component: AdminProfile },
      { path: 'register', name: 'RegisterUser', component: RegisterUser },
      { path: 'students', name: 'StudentManagement', component: StudentManagement },
      { path: 'teachers', name: 'TeacherManagement', component: TeacherManagement },
      {
        path: 'mutual-selection',
        name: 'MutualSelectionManagement',
        // 使用动态导入（懒加载）
        component: () => import('../pages/MutualSelectionManagement.vue'),
      },
      {
        path: 'auto-assignment',
        name: 'AutoAssignment',
        component: () => import('../pages/AutoAssignment.vue'),
      },
    ]
  },

  // --- 学生个人主页 ---
  {
    path: '/student/dashboard',
    name: 'StudentDashboard',
    component: StudentDashboard,
    meta: { requiresStudentAuth: true }, // 需要学生权限
    children: [
    {
      path: 'profile',  // 子路由，路径为 '/student/dashboard/profile'
      name: 'StudentProfile',
      component: () => import('../pages/StudentProfile.vue'),  // 渲染个人信息管理页面
    },
    {
      path: 'team',
      name: 'StudentTeam',
      component: () => import('../pages/StudentTeam.vue'),
    },
        {
        path: 'history',
        name: 'StudentHistory',
        component: () => import('../pages/StudentHistory.vue'),
      },
      {
        path: 'history/:id',
        name: 'StudentResultDetail',
        component: () => import('../pages/StudentResultDetail.vue'),
        props: true
      },
  ]
  },
  {
    path: '/teacher/dashboard',
    component: TeacherDashboard,
    meta: { requiresTeacherAuth: true }, // 需要教师权限
    children: [
      { path: '', redirect: '/teacher/dashboard/profile' }, // 默认子路由，直接显示个人信息
      { path: 'profile', name: 'TeacherProfile', component: TeacherProfile },
      {
        path: 'select-team',
        name: 'TeacherTeamSelection',
        component: () => import('../pages/TeacherTeamSelection.vue'), // 使用懒加载
      },
      {
        path: 'history',
        name: 'TeacherHistory',
        component: () => import('../pages/TeacherHistory.vue'),
      },
      {
        path: 'history/:id',
        name: 'TeacherHistoryDetail',
        component: () => import('../pages/TeacherHistoryDetail.vue'),
        props: true // 将路由参数 :id 作为 props 传递给组件
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

const isTokenExpired = (token) => {
  if (!token) return true;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // 转换为毫秒
    const now = Date.now();

    // 提前30秒判断为过期（给刷新留出时间）
    return now >= (exp - 30000);
  } catch (e) {
    console.error('Token解析失败:', e);
    return true;
  }
};

router.beforeEach(async (to, from, next) => {
  console.log(`🔀 路由跳转: ${from.path} -> ${to.path}`);

  const adminToken = localStorage.getItem('accessToken');
  const studentToken = localStorage.getItem('studentAccessToken');
  const teacherToken = localStorage.getItem('teacherAccessToken');

  const requiresAdminAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresStudentAuth = to.matched.some(record => record.meta.requiresStudentAuth);
  const requiresTeacherAuth = to.matched.some(record => record.meta.requiresTeacherAuth);

  // 管理员路由检查
  if (requiresAdminAuth) {
    if (!adminToken) {
      console.log('❌ 管理员未登录，跳转到登录页');
      ElMessage.warning('请先登录');
      next({ name: 'Login', query: { message: 'unauthorized' } });
      return;
    }

    if (isTokenExpired(adminToken)) {
      console.log('⚠️ 管理员Token已过期');
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        console.log('❌ 没有refresh token，跳转登录');
        ElMessage.warning('登录已过期，请重新登录');
        next({ name: 'Login', query: { message: 'session-expired' } });
        return;
      }
      // 有refresh token，让axios拦截器自动刷新
      console.log('✅ 有refresh token，继续访问（将自动刷新）');
    }
  }

  // 学生路由检查
  else if (requiresStudentAuth) {
    if (!studentToken) {
      console.log('❌ 学生未登录，跳转到登录页');
      ElMessage.warning('请先登录');
      next({ name: 'Login', query: { message: 'unauthorized' } });
      return;
    }

    if (isTokenExpired(studentToken)) {
      console.log('⚠️ 学生Token已过期');
      const refreshToken = localStorage.getItem('studentRefreshToken');
      if (!refreshToken) {
        console.log('❌ 没有refresh token，跳转登录');
        ElMessage.warning('登录已过期，请重新登录');
        next({ name: 'Login', query: { message: 'session-expired' } });
        return;
      }
      console.log('✅ 有refresh token，继续访问（将自动刷新）');
    }
  }

  // 教师路由检查
  else if (requiresTeacherAuth) {
    if (!teacherToken) {
      console.log('❌ 教师未登录，跳转到登录页');
      ElMessage.warning('请先登录');
      next({ name: 'Login', query: { message: 'unauthorized' } });
      return;
    }

    if (isTokenExpired(teacherToken)) {
      console.log('⚠️ 教师Token已过期');
      const refreshToken = localStorage.getItem('teacherRefreshToken');
      if (!refreshToken) {
        console.log('❌ 没有refresh token，跳转登录');
        ElMessage.warning('登录已过期，请重新登录');
        next({ name: 'Login', query: { message: 'session-expired' } });
        return;
      }
      console.log('✅ 有refresh token，继续访问（将自动刷新）');
    }
  }

  next();
});

export default router;