<template>
  <div class="dashboard-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h3>教师仪表盘</h3>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/teacher/profile" class="nav-item">个人信息</router-link>
        <!-- 未来可以添加更多导航项 -->
        <!-- <router-link to="/teacher/courses" class="nav-item">我的课程</router-link> -->
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
  // 清除教师相关的 token
  localStorage.removeItem('teacherAccessToken');
  localStorage.removeItem('teacherRefreshToken');
  // 跳转到登录页面
  router.push('/login');
};
</script>

<style scoped>
.dashboard-layout { display: flex; height: 100vh; background-color: #f7f8fc; }
.sidebar { width: 240px; background-color: #343a40; color: #fff; display: flex; flex-direction: column; }
.sidebar-header { padding: 20px; text-align: center; border-bottom: 1px solid #495057; }
.sidebar-nav { flex-grow: 1; padding: 20px 0; }
.nav-item { display: block; padding: 12px 20px; color: #ced4da; text-decoration: none; transition: background-color 0.2s, color 0.2s; }
.nav-item:hover, .router-link-exact-active { background-color: #495057; color: #fff; }
.sidebar-footer { padding: 20px; border-top: 1px solid #495057; }
.logout-button { width: 100%; padding: 10px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; }
.main-content { flex-grow: 1; padding: 40px; overflow-y: auto; }
</style>