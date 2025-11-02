import { createRouter, createWebHistory } from 'vue-router';

import Login from '../components/Login.vue';
import DashboardLayout from '../layouts/DashboardLayout.vue';
import UserList from '../pages/UserList.vue';
import RegisterUser from '../pages/RegisterUser.vue';
import StudentManagement from '../pages/StudentManagement.vue';
import StudentDashboard from '../layouts/StudentDashboard.vue';
import TeacherManagement from '../pages/TeacherManagement.vue';

import TeacherDashboard from '../layouts/TeacherDashboard.vue';
import TeacherProfile from "../pages/TeacherProfile.vue";


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
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

// --- 路由守卫更新 ---
// 现在，任何未授权的访问都会被重定向到唯一的 'Login' 路由
router.beforeEach((to, from, next) => {
  const adminToken = localStorage.getItem('accessToken');
  const studentToken = localStorage.getItem('studentAccessToken');
  const teacherToken = localStorage.getItem('teacherAccessToken');
  const requiresTeacherAuth = to.matched.some(record => record.meta.requiresTeacherAuth);

  const requiresAdminAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresStudentAuth = to.matched.some(record => record.meta.requiresStudentAuth);

  if (requiresAdminAuth && !adminToken) {
    next({ name: 'Login', query: { message: 'unauthorized' } });
  } else if (requiresStudentAuth && !studentToken) {
    next({ name: 'Login', query: { message: 'unauthorized' } });
  } else if (requiresTeacherAuth && !teacherToken) {
    next({ name: 'Login', query: { message: 'unauthorized' } });
  }else {
    next();
  }
});

export default router;