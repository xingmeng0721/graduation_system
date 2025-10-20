<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>学生个人主页</h1>
      <button @click="handleLogout" class="logout-btn">退出登录</button>
    </header>

    <main class="dashboard-content">
      <div v-if="loading" class="loading-spinner">正在加载...</div>
      <div v-if="error" class="error-message">{{ error }}</div>

      <div v-if="student" class="profile-card">
        <h2>欢迎您，{{ student.stu_name }}！</h2>
        <div class="profile-details">
          <p><strong>学号:</strong> {{ student.stu_no }}</p>
          <p><strong>姓名:</strong> {{ student.stu_name }}</p>
          <p><strong>年级:</strong> {{ student.grade }}</p>
          <p><strong>专业:</strong> {{ student.major ? student.major.major_name : '未分配' }}</p>
          <p><strong>分组:</strong> {{ student.group ? student.group.group_name : '未分配' }}</p>
          <p><strong>手机号:</strong> {{ student.phone || '未提供' }}</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import {useRouter} from 'vue-router';
import api from '../services/api';

const student = ref(null);
const loading = ref(true);
const error = ref(null);
const router = useRouter();

const handleLogout = () => {
  localStorage.removeItem('studentAccessToken');
  localStorage.removeItem('studentRefreshToken');


  router.push({name: 'Login'});
};

onMounted(async () => {
  try {
    const response = await api.getStudentProfile();
    student.value = response.data;
  } catch (err) {
    console.error('Failed to fetch student profile:', err);
    error.value = '无法加载个人信息，请重新登录。';
    if (err.response && err.response.status === 401) {
      handleLogout();
    }
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.dashboard-container {
  font-family: sans-serif;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background-color: #007bff;
  color: white;
}

.logout-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

.dashboard-content {
  padding: 40px;
}

.profile-card {
  background: #fff;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  margin: auto;
}

.profile-details p {
  line-height: 1.8;
  font-size: 16px;
}

.error-message {
  color: red;
  text-align: center;
}

.loading-spinner {
  text-align: center;
  padding: 50px;
}
</style>