<template>
  <div class="auth-container">
    <div class="auth-card">
      <!-- 切换用户类型的Tabs -->
      <div class="user-type-switcher">
        <button
          :class="{ active: userType === 'admin' }"
          @click="switchUserType('admin')">
          管理员登录
        </button>
        <button
          :class="{ active: userType === 'student' }"
          @click="switchUserType('student')">
          学生登录
        </button>
      </div>

      <h2 class="form-title">{{ formTitle }}</h2>

      <div v-if="notification" class="notification-message">{{ notification }}</div>

      <form @submit.prevent="handleLogin">
        <!-- 动态表单内容 -->
        <div class="form-group">
          <label :for="usernameFieldId">{{ usernameLabel }}</label>
          <input type="text" :id="usernameFieldId" v-model="credentials.username" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="credentials.password" required>
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <button type="submit" class="btn-submit">登录</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../services/api';

// 核心状态：当前用户类型 ('admin' 或 'student')
const userType = ref('admin'); // 默认是管理员

const credentials = ref({
  username: '',
  password: ''
});
const error = ref(null);
const notification = ref(null);

const router = useRouter();
const route = useRoute();

// --- 动态计算属性，根据 userType 改变UI ---
const formTitle = computed(() => userType.value === 'admin' ? '管理员登录' : '学生登录');
const usernameLabel = computed(() => userType.value === 'admin' ? '用户名' : '学号');
const usernameFieldId = computed(() => userType.value === 'admin' ? 'admin_username' : 'stu_no');

// --- 切换用户类型的函数 ---
const switchUserType = (type) => {
  userType.value = type;
  // 将用户的选择存入 localStorage
  localStorage.setItem('lastLoginType', type);
  // 清空错误信息和表单
  error.value = null;
  credentials.value.username = '';
  credentials.value.password = '';
};

// --- 统一的登录处理函数 ---
const handleLogin = async () => {
  error.value = null;
  notification.value = null;

  try {
    let response;
    if (userType.value === 'admin') {
      // 调用管理员登录API
      response = await api.login({
        admin_username: credentials.value.username,
        password: credentials.value.password
      });
      localStorage.setItem('accessToken', response.data.access);
      localStorage.setItem('refreshToken', response.data.refresh);
      router.push('/dashboard');
    } else {
      // 调用学生登录API
      response = await api.studentLogin({
        stu_no: credentials.value.username,
        password: credentials.value.password
      });
      localStorage.setItem('studentAccessToken', response.data.access);
      localStorage.setItem('studentRefreshToken', response.data.refresh);
      router.push('/student/dashboard');
    }
  } catch (err) {
    error.value = '登录失败，请检查您的凭据。';
    console.error('Login failed:', err);
  }
};

// --- 组件挂载时的逻辑 ---
onMounted(() => {
  // 检查是否有路由跳转来的未授权信息
  if (route.query.message === 'unauthorized') {
    notification.value = '您需要先登录才能访问该页面。';
  }

  // 检查 localStorage 中记住的上次登录类型
  const lastType = localStorage.getItem('lastLoginType');
  if (lastType && ['admin', 'student'].includes(lastType)) {
    userType.value = lastType;
  }
});
</script>

<style scoped>
/* 样式已更新，加入了Tab切换的样式 */
.auth-container { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; }
.auth-card { width: 380px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); background: #fff; border-radius: 8px; }

.user-type-switcher { display: flex; margin-bottom: 24px; border-radius: 6px; overflow: hidden; border: 1px solid #007bff; }
.user-type-switcher button { flex: 1; padding: 12px; border: none; background-color: #fff; color: #007bff; font-size: 16px; cursor: pointer; transition: background-color 0.3s, color 0.3s; }
.user-type-switcher button.active { background-color: #007bff; color: #fff; }

.form-title { text-align: center; margin-bottom: 24px; color: #333; }
.form-group { margin-bottom: 16px; }
label { display: block; margin-bottom: 8px; font-weight: 600; }
input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.btn-submit { width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 10px; }
.error-message { color: #dc3545; margin-bottom: 15px; text-align: center; }
.notification-message { color: #007bff; background-color: #e7f3ff; border: 1px solid #b3d7ff; padding: 10px; border-radius: 4px; margin-bottom: 15px; text-align: center; }
</style>