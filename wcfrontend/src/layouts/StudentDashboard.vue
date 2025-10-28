<template>
  <div class="student-dashboard-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h3>学生管理系统</h3>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/student/dashboard/profile" v-if="isStudent">个人信息管理</router-link>
        <router-link to="/student/dashboard/team" v-if="isStudent">团队管理</router-link>
<!--        <router-link to="/student/dashboard/mentor" v-if="isStudent">导师选择</router-link>-->
<!--        <router-link to="/student/dashboard/results" v-if="isStudent">结果查看</router-link>-->
      </nav>
      <div class="sidebar-footer">
        <button @click="handleLogout" class="btn-logout">退出登录</button>
      </div>
    </aside>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

// 判断是否为学生
const isStudent = !!localStorage.getItem('studentAccessToken');
const router = useRouter();

const handleLogout = () => {
  localStorage.removeItem('studentAccessToken');  // 清除学生登录令牌
  localStorage.removeItem('studentRefreshToken'); // 清除学生刷新令牌
  router.push('/login');  // 跳转到登录页面
};
</script>

<style scoped>
.student-dashboard-layout {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 250px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #34495e;
}
.sidebar-nav {
  flex-grow: 1;
  padding: 20px 0;
}
.sidebar-nav a {
  display: block;
  padding: 15px 20px;
  color: #bdc3c7;
  text-decoration: none;
  transition: background-color 0.3s;
}
.sidebar-nav a:hover,
.sidebar-nav a.router-link-active {
  background-color: #34495e;
  color: white;
}
.sidebar-footer {
  padding: 20px;
  border-top: 1px solid #34495e;
}
.btn-logout {
  width: 100%;
  padding: 10px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-logout:hover {
  background-color: #c0392b;
}
.main-content {
  flex-grow: 1;
  padding: 40px;
  background-color: #f4f6f9;
  overflow-y: auto;
}
</style>
