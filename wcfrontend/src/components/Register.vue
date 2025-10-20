<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

const admin_name = ref('');
const admin_username = ref('');
const password = ref('');
const error = ref(null);
const successMessage = ref(null);
const router = useRouter();

const handleRegister = async () => {
  error.value = null;
  successMessage.value = null;

  if (!admin_name.value || !admin_username.value || !password.value) {
    error.value = '所有字段都必须填写。';
    return;
  }

  try {
    await api.register({
      admin_name: admin_name.value,
      admin_username: admin_username.value,
      admin_password: password.value
    });

    successMessage.value = '注册成功！正在跳转到登录页面...';

    setTimeout(() => {
      router.push('/login');
    }, 2000);

  } catch (err) {
    console.error("注册API返回的完整错误:", err);

    if (err.response && err.response.data) {
      const backendErrors = err.response.data;
      let errorMessage = '';

      for (const field in backendErrors) {
        errorMessage += `${field}: ${backendErrors[field].join(', ')} `;
      }

      error.value = errorMessage || '注册失败，请检查您填写的信息。';

    } else {
      error.value = '发生网络错误或未知问题，请稍后再试。';
    }
  }
};
</script>

<!-- <template> 和 <style> 部分保持不变 -->
<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>创建您的账户</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="name">名称</label>
          <input type="text" id="name" v-model="admin_name" required>
        </div>
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="admin_username" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
        <button type="submit" class="btn-submit">注册</button>
      </form>
      <div class="switch-auth">
        已经有账户了？ <router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 样式与登录组件共享，可以提取为公共样式 */
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
.auth-card {
  width: 360px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  background: #fff;
  border-radius: 8px;
}
h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #333;
}
.form-group {
  margin-bottom: 16px;
}
label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}
input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.btn-submit {
  width: 100%;
  padding: 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 10px;
}
.btn-submit:hover {
  background-color: #0056b3;
}
.switch-auth {
  text-align: center;
  margin-top: 20px;
}
.error-message {
  color: #dc3545;
  margin-bottom: 15px;
  text-align: center;
}
.success-message {
  color: #28a745;
  margin-bottom: 15px;
  text-align: center;
}
</style>