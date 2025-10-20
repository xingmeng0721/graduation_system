<template>
  <div class="dashboard-container">
    <h1>仪表盘</h1>
    <p>欢迎！您已成功登录。</p>
    <button @click="handleLogout" class="btn-logout">退出登录</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const handleLogout = () => {
  // 清除 localStorage 中的 token
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');

  // 跳转回登录页面
  router.push('/login');
};
</script>

<style scoped>
.dashboard-container {
  padding: 40px;
  text-align: center;
}
.btn-logout {
  padding: 10px 20px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
}
.btn-logout:hover {
  background-color: #c82333;
}
</style>