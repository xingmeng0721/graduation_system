<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>学生登录</h2>
      <div v-if="notification" class="notification-message">{{ notification }}</div>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="stu_no">学号</label>
          <input type="text" id="stu_no" v-model="stu_no" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <button type="submit" class="btn-submit">登录</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../services/api';

const stu_no = ref('');
const password = ref('');
const error = ref(null);
const notification = ref(null);

const router = useRouter();
const route = useRoute();

onMounted(() => {
  if (route.query.message === 'unauthorized') {
    notification.value = '您需要先登录才能访问。';
  }
});

const handleLogin = async () => {
  error.value = null;
  try {
    const response = await api.studentLogin({
      stu_no: stu_no.value,
      password: password.value
    });
    // 使用不同的 key 存储学生 token
    localStorage.setItem('studentAccessToken', response.data.access);
    localStorage.setItem('studentRefreshToken', response.data.refresh);
    router.push('/student/dashboard');
  } catch (err) {
    error.value = '学号或密码错误。';
  }
};
</script>

<style scoped>
.auth-container { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; }
.auth-card { width: 360px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); background: #fff; border-radius: 8px; }
h2 { text-align: center; margin-bottom: 24px; color: #333; }
.form-group { margin-bottom: 16px; }
label { display: block; margin-bottom: 8px; font-weight: 600; }
input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.btn-submit { width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
.error-message { color: #dc3545; margin-bottom: 15px; text-align: center; }
.notification-message { color: #007bff; background-color: #e7f3ff; border: 1px solid #b3d7ff; padding: 10px; border-radius: 4px; margin-bottom: 15px; text-align: center; }
</style>