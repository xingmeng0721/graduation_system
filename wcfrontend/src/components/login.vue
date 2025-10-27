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
          :class="{ active: userType === 'teacher' }"
          @click="switchUserType('teacher')">
          教师
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

        <!-- 忘记密码链接 (仅学生可见) -->
        <div class="extra-links">
          <a v-if="userType === 'student'" @click.prevent="openForgotPasswordModal" href="#">忘记密码?</a>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>
        <button type="submit" class="btn-submit" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>

    <!-- 忘记密码弹窗 -->
    <div v-if="isForgotPasswordModalVisible" class="modal-overlay" @click.self="closeForgotPasswordModal">
      <div class="modal-content">
        <h2 class="form-title">重置学生密码</h2>

        <!-- 步骤一：发送验证码 -->
        <form v-if="resetStep === 1" @submit.prevent="handleSendCode">
          <p class="form-description">请输入您的姓名和注册时使用的邮箱以接收验证码。</p>
          <div class="form-group">
            <label for="reset-stu-name">姓名</label>
            <input type="text" id="reset-stu-name" v-model="resetInfo.stu_name" required>
          </div>
          <div class="form-group">
            <label for="reset-email">邮箱</label>
            <input type="email" id="reset-email" v-model="resetInfo.email" required>
          </div>
          <div v-if="resetError" class="error-message">{{ resetError }}</div>
          <div class="modal-actions">
            <button type="button" @click="closeForgotPasswordModal" class="btn-secondary">取消</button>
            <button type="submit" class="btn-submit" :disabled="isSendingCode">
              {{ isSendingCode ? '发送中...' : '发送验证码' }}
            </button>
          </div>
        </form>

        <!-- 步骤二：重置密码 -->
        <form v-if="resetStep === 2" @submit.prevent="handleResetPassword">
          <p class="form-description">验证码已发送至 {{ resetInfo.email }}。请输入验证码和您的新密码。</p>
          <div class="form-group">
            <label for="reset-code">验证码</label>
            <input type="text" id="reset-code" v-model="resetInfo.code" required>
          </div>
          <div class="form-group">
            <label for="reset-password">新密码</label>
            <input type="password" id="reset-password" v-model="resetInfo.password" required>
          </div>
          <div v-if="resetError" class="error-message">{{ resetError }}</div>
          <div class="modal-actions">
            <button type="button" @click="closeForgotPasswordModal" class="btn-secondary">取消</button>
            <button type="submit" class="btn-submit" :disabled="isResettingPassword">
              {{ isResettingPassword ? '重置中...' : '确认重置' }}
            </button>
          </div>
        </form>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../services/api';

// 核心状态
const userType = ref('admin');
const credentials = ref({ username: '', password: '' });
const error = ref(null);
const notification = ref(null);
const isLoading = ref(false);

// 忘记密码弹窗状态
const isForgotPasswordModalVisible = ref(false);
const resetStep = ref(1); // 1: 发送验证码, 2: 重置密码
const resetInfo = ref({ stu_name: '', email: '', code: '', password: '' });
const resetError = ref(null);
const isSendingCode = ref(false);
const isResettingPassword = ref(false);

const router = useRouter();
const route = useRoute();

// --- 动态计算属性 ---
const formTitle = computed(() => {
  if (userType.value === 'admin') return '管理员登录';
  if (userType.value === 'teacher') return '教师登录';
  return '学生登录';
});
const usernameLabel = computed(() => {
  if (userType.value === 'admin') return '用户名';
  if (userType.value === 'teacher') return '工号';
  return '学号';
});
const usernameFieldId = computed(() => {
  if (userType.value === 'admin') return 'admin_username';
  if (userType.value === 'teacher') return 'teacher_no';
  return 'stu_no';
});

// --- 方法 ---
const switchUserType = (type) => {
  userType.value = type;
  localStorage.setItem('lastLoginType', type);
  error.value = null;
  notification.value = null;
  credentials.value = { username: '', password: '' };
};

const handleLogin = async () => {
  error.value = null;
  notification.value = null;
  isLoading.value = true;
  try {
    let response;
    let payload = { password: credentials.value.password };

    if (userType.value === 'admin') {
      payload.admin_username = credentials.value.username;
      response = await api.login(payload);
      localStorage.setItem('accessToken', response.data.access);
      localStorage.setItem('refreshToken', response.data.refresh);
      router.push('/dashboard');
    } else if (userType.value === 'teacher') {
      payload.teacher_no = credentials.value.username;
      response = await api.teacherLogin(payload);
      localStorage.setItem('teacherAccessToken', response.data.access);
      localStorage.setItem('teacherRefreshToken', response.data.refresh);
      router.push('/teacher/dashboard');
    } else {
      payload.stu_no = credentials.value.username;
      response = await api.studentLogin(payload);
      localStorage.setItem('studentAccessToken', response.data.access);
      localStorage.setItem('studentRefreshToken', response.data.refresh);
      router.push('/student/dashboard');
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查您的凭据。';
    console.error('Login failed:', err);
  } finally {
    isLoading.value = false;
  }
};

// --- 忘记密码相关方法 ---
const openForgotPasswordModal = () => {
  isForgotPasswordModalVisible.value = true;
  resetStep.value = 1;
  resetInfo.value = { stu_name: '', email: '', code: '', password: '' };
  resetError.value = null;
};

const closeForgotPasswordModal = () => {
  isForgotPasswordModalVisible.value = false;
};

const handleSendCode = async () => {
  resetError.value = null;
  isSendingCode.value = true;
  try {
    // API调用现在放在try块中
    const response = await api.sendStudentResetCode({
      stu_name: resetInfo.value.stu_name,
      email: resetInfo.value.email
    });

    // 只有当请求成功 (HTTP状态码 2xx) 时，才会执行到这里
    resetStep.value = 2; // 切换到第二步

  } catch (err) {
    // 如果API返回错误 (HTTP状态码 4xx, 5xx), 会被这里捕获
    resetError.value = err.response?.data?.error || '发送失败，请检查姓名和邮箱是否正确。';
    console.error("Send code failed:", err);
  } finally {
    isSendingCode.value = false;
  }
};

const handleResetPassword = async () => {
  resetError.value = null;
  isResettingPassword.value = true;
  try {
    const response = await api.resetStudentPasswordByCode(resetInfo.value);
    closeForgotPasswordModal();
    notification.value = response.data.message || '密码重置成功！现在您可以使用新密码登录。';
  } catch (err) {
    resetError.value = err.response?.data?.error || '重置失败，请检查验证码是否正确。';
    console.error("Reset password failed:", err);
  } finally {
    isResettingPassword.value = false;
  }
};

// --- 组件挂载 ---
onMounted(() => {
  if (route.query.message === 'unauthorized') {
    notification.value = '您需要先登录才能访问该页面。';
  }
  const lastType = localStorage.getItem('lastLoginType');
  if (lastType && ['admin', 'student', 'teacher'].includes(lastType)) {
    userType.value = lastType;
  }
});
</script>

<style scoped>
.auth-container { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; }
.auth-card { width: 380px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); background: #fff; border-radius: 8px; }

.user-type-switcher { display: flex; margin-bottom: 24px; border-radius: 6px; overflow: hidden; border: 1px solid #007bff; }
.user-type-switcher button { flex: 1; padding: 12px; border: none; background-color: #fff; color: #007bff; font-size: 16px; cursor: pointer; transition: background-color 0.3s, color 0.3s; }
.user-type-switcher button.active { background-color: #007bff; color: #fff; }

.form-title { text-align: center; margin-bottom: 24px; color: #333; }
.form-description { text-align: center; margin-bottom: 20px; color: #666; }
.form-group { margin-bottom: 16px; }
label { display: block; margin-bottom: 8px; font-weight: 600; }
input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.btn-submit { width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 10px; }
.btn-submit:disabled { background-color: #a0cffc; cursor: not-allowed; }
.error-message { color: #dc3545; margin-bottom: 15px; text-align: center; }
.notification-message { color: #007bff; background-color: #e7f3ff; border: 1px solid #b3d7ff; padding: 10px; border-radius: 4px; margin-bottom: 15px; text-align: center; }
.extra-links { text-align: right; margin-top: -10px; margin-bottom: 15px; }
.extra-links a { color: #007bff; text-decoration: none; font-size: 0.9em; cursor: pointer; }

/* 弹窗样式 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background: white; padding: 30px 40px; border-radius: 8px; width: 90%; max-width: 420px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 30px; }
.btn-secondary { padding: 12px 20px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; }
</style>