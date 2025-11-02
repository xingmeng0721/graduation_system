<template>
  <div class="dashboard-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h3>教师仪表盘</h3>
      </div>
      <nav class="sidebar-nav">
        <!-- [修复] 将 to 的路径修改为正确的嵌套路由路径 -->
        <router-link to="/teacher/dashboard/profile" class="nav-item">个人信息</router-link>
        <router-link to="/teacher/dashboard/select-team" class="nav-item">选择指导团队</router-link>
      </nav>
      <div class="sidebar-footer">
        <button @click="logout" class="logout-button">退出登录</button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const logout = () => {
  // 清除教师相关的 token 和其他可能的用户信息
  localStorage.removeItem('teacherAccessToken');
  localStorage.removeItem('teacherRefreshToken');
  // 跳转到登录页面
  router.push('/login');
};
</script>

<style scoped>
.dashboard-layout { display: flex; height: 100vh; background-color: #f7f8fc; }
.sidebar { width: 240px; background-color: #2c3e50; color: #fff; display: flex; flex-direction: column; box-shadow: 2px 0 5px rgba(0,0,0,0.1); }
.sidebar-header { padding: 20px; text-align: center; border-bottom: 1px solid #34495e; font-size: 1.2em; }
.sidebar-nav { flex-grow: 1; padding: 20px 0; }
.nav-item { display: block; padding: 15px 25px; color: #bdc3c7; text-decoration: none; transition: background-color 0.2s, color 0.2s; border-left: 3px solid transparent; }
.nav-item:hover { background-color: #34495e; color: #fff; }
/* .router-link-exact-active 已被 .router-link-active 取代，后者更常用 */
.router-link-active { background-color: #34495e; color: #fff; border-left-color: #3498db; }
.sidebar-footer { padding: 20px; border-top: 1px solid #34495e; }
.logout-button { width: 100%; padding: 10px; background-color: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
.logout-button:hover { background-color: #c0392b; }
.main-content { flex-grow: 1; padding: 40px; overflow-y: auto; }
</style>