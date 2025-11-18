<template>
  <div class="login-container">
    <el-card class="login-card" shadow="hover">
      <!-- 标题 -->
      <div class="login-header">
        <h2 class="system-title">师生双选系统</h2>
      </div>

      <!-- 用户类型切换 - 使用 el-radio-group 替代 el-segmented -->
      <el-radio-group
        v-model="userType"
        size="large"
        class="user-type-selector"
        @change="handleUserTypeChange"
      >
        <el-radio-button value="admin">管理员</el-radio-button>
        <el-radio-button value="teacher">教师</el-radio-button>
        <el-radio-button value="student">学生</el-radio-button>
      </el-radio-group>

      <!-- 消息提示 -->
      <el-alert
        v-if="notification"
        :title="notification"
        type="info"
        :closable="false"
        center
        class="message-alert"
      />

      <!-- 登录表单 -->
      <el-form
        ref="loginFormRef"
        :model="credentials"
        label-position="top"
        size="large"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item :label="usernameLabel">
          <el-input
            v-model="credentials.username"
            :placeholder="`请输入${usernameLabel}`"
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="credentials.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <!-- 忘记密码 -->
        <div v-if="userType === 'student'" class="extra-options">
          <el-link type="primary" :underline="false" @click="openForgotPasswordModal">
            忘记密码？
          </el-link>
        </div>

        <!-- 错误提示 -->
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          center
          class="message-alert"
        />

        <el-button
          type="primary"
          size="large"
          :loading="isLoading"
          native-type="submit"
          class="login-button"
        >
          {{ isLoading ? '登录中...' : '登 录' }}
        </el-button>
      </el-form>
    </el-card>

    <!-- 忘记密码对话框 -->
    <el-dialog
      v-model="isForgotPasswordModalVisible"
      :title="resetStep === 1 ? '重置密码' : '设置新密码'"
      width="420px"
      center
    >
      <!-- 步骤一：发送验证码 -->
      <el-form
        v-if="resetStep === 1"
        ref="sendCodeFormRef"
        :model="resetInfo"
        label-width="80px"
        class="reset-form"
        @submit.prevent="handleSendCode"
      >
        <el-form-item label="学号">
          <el-input
            v-model="resetInfo.stu_no"
            placeholder="请输入您的学号"
            clearable
          />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input
            v-model="resetInfo.email"
            placeholder="请输入注册邮箱"
            clearable
          />
        </el-form-item>

        <el-alert
          v-if="resetError"
          :title="resetError"
          type="error"
          :closable="false"
          class="reset-error-alert"
        />
      </el-form>

      <!-- 步骤二：重置密码 -->
      <el-form
        v-if="resetStep === 2"
        ref="resetPasswordFormRef"
        :model="resetInfo"
        label-width="80px"
        class="reset-form"
        @submit.prevent="handleResetPassword"
      >
        <el-alert
          title="验证码已发送"
          :description="`验证码已发送至 ${resetInfo.email}`"
          type="success"
          :closable="false"
          class="reset-success-alert"
        />

        <el-form-item label="验证码">
          <el-input
            v-model="resetInfo.code"
            placeholder="请输入验证码"
            clearable
          />
        </el-form-item>

        <el-form-item label="新密码">
          <el-input
            v-model="resetInfo.password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>

        <el-alert
          v-if="resetError"
          :title="resetError"
          type="error"
          :closable="false"
          class="reset-error-alert"
        />
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeForgotPasswordModal">取消</el-button>
          <el-button
            v-if="resetStep === 1"
            type="primary"
            @click="handleSendCode"
            :loading="isSendingCode"
          >
            发送验证码
          </el-button>
          <el-button
            v-if="resetStep === 2"
            type="primary"
            @click="handleResetPassword"
            :loading="isResettingPassword"
          >
            确认重置
          </el-button>
        </div>
      </template>
    </el-dialog>

        <div class="beian-footer">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">
        粤ICP备2025495465号-1
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../services/api'

// 核心状态
const userType = ref('admin')
const credentials = ref({ username: '', password: '' })
const error = ref(null)
const notification = ref(null)
const isLoading = ref(false)

// 忘记密码弹窗状态
const isForgotPasswordModalVisible = ref(false)
const resetStep = ref(1)
const resetInfo = ref({ stu_no: '', email: '', code: '', password: '' })
const resetError = ref(null)
const isSendingCode = ref(false)
const isResettingPassword = ref(false)

const router = useRouter()
const route = useRoute()

// 表单引用
const loginFormRef = ref(null)
const sendCodeFormRef = ref(null)
const resetPasswordFormRef = ref(null)

// 动态计算属性
const usernameLabel = computed(() => {
  const labels = {
    admin: '用户名',
    teacher: '工号',
    student: '学号'
  }
  return labels[userType.value]
})

// ✅ 新增：监听用户类型变化，保存到 localStorage
watch(userType, (newType) => {
  console.log('用户类型切换为:', newType)
  localStorage.setItem('lastLoginType', newType)
  // 清除错误信息
  error.value = null
})

// ✅ 新增：处理用户类型变化
const handleUserTypeChange = (value) => {
  console.log('handleUserTypeChange:', value)
  userType.value = value
}

// 登录处理
const handleLogin = async () => {
  // 简单验证
  if (!credentials.value.username || !credentials.value.password) {
    error.value = '请输入完整的登录信息'
    return
  }

  error.value = null
  notification.value = null
  isLoading.value = true

  try {
    let response
    let payload = { password: credentials.value.password }

    // ✅ 保存当前登录类型
    localStorage.setItem('lastLoginType', userType.value)

    if (userType.value === 'admin') {
      payload.admin_username = credentials.value.username
      response = await api.login(payload)
      localStorage.setItem('accessToken', response.data.access)
      localStorage.setItem('refreshToken', response.data.refresh)
      ElMessage.success('登录成功')
      router.push('/dashboard')
    } else if (userType.value === 'teacher') {
      payload.teacher_no = credentials.value.username
      response = await api.teacherLogin(payload)
      localStorage.setItem('teacherAccessToken', response.data.access)
      localStorage.setItem('teacherRefreshToken', response.data.refresh)
      ElMessage.success('登录成功')
      router.push('/teacher/dashboard')
    } else {
      payload.stu_no = credentials.value.username
      response = await api.studentLogin(payload)
      localStorage.setItem('studentAccessToken', response.data.access)
      localStorage.setItem('studentRefreshToken', response.data.refresh)
      ElMessage.success('登录成功')
      router.push('/student/dashboard')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查您的凭据'
    console.error('Login failed:', err)
  } finally {
    isLoading.value = false
  }
}

// 打开忘记密码弹窗
const openForgotPasswordModal = () => {
  isForgotPasswordModalVisible.value = true
  resetStep.value = 1
  resetInfo.value = { stu_no: '', email: '', code: '', password: '' }
  resetError.value = null
}

// 关闭忘记密码弹窗
const closeForgotPasswordModal = () => {
  isForgotPasswordModalVisible.value = false
  resetError.value = null
}

// 发送验证码
const handleSendCode = async () => {
  if (!resetInfo.value.stu_no || !resetInfo.value.email) {
    resetError.value = '请输入学号和邮箱'
    return
  }

  resetError.value = null
  isSendingCode.value = true

  try {
    await api.sendStudentResetCode({
      stu_no: resetInfo.value.stu_no,
      email: resetInfo.value.email
    })

    ElMessage.success('验证码已发送')
    resetStep.value = 2

  } catch (err) {
    resetError.value = err.response?.data?.error || '发送失败，请检查学号和邮箱'
    console.error('Send code failed:', err)
  } finally {
    isSendingCode.value = false
  }
}

// 重置密码
const handleResetPassword = async () => {
  if (!resetInfo.value.code || !resetInfo.value.password) {
    resetError.value = '请输入验证码和新密码'
    return
  }

  resetError.value = null
  isResettingPassword.value = true

  try {
    await api.resetStudentPasswordByCode(resetInfo.value)

    ElMessage.success('密码重置成功')
    closeForgotPasswordModal()
    resetInfo.value = {stu_no: '', email: '', code: '', password: ''}

  } catch (err) {
    resetError.value = err.response?.data?.error || '重置失败，请检查验证码'
    console.error('Reset password failed:', err)
  } finally {
    isResettingPassword.value = false
  }
}

// 组件挂载
onMounted(() => {
  console.log('Login component mounted')

  // 显示通知消息
  if (route.query.message === 'unauthorized') {
    notification.value = '您需要先登录才能访问该页面'
  } else if (route.query.message === 'session-expired') {
    notification.value = '登录已过期，请重新登录'
  }

  // ✅ 从 localStorage 读取上次的登录类型
  const lastType = localStorage.getItem('lastLoginType')
  console.log('上次登录类型:', lastType)

  if (lastType && ['admin', 'student', 'teacher'].includes(lastType)) {
    userType.value = lastType
  } else {
    // 如果没有记录，默认设置为 admin
    userType.value = 'admin'
    localStorage.setItem('lastLoginType', 'admin')
  }

  console.log('当前用户类型:', userType.value)
})
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.login-card {
  width: 420px;
  max-width: 90%;
  padding: 40px;
  border-radius: 8px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.system-title {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  color: #303133;
}

.user-type-selector {
  width: 100%;
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.user-type-selector :deep(.el-radio-button) {
  flex: 1;
}

.user-type-selector :deep(.el-radio-button__inner) {
  width: 100%;
}

.login-form {
  margin-top: 24px;
}

.extra-options {
  text-align: right;
  margin-top: -10px;
  margin-bottom: 16px;
}

.message-alert {
  margin-bottom: 16px;
}

.login-button {
  width: 100%;
  margin-top: 10px;
}

.reset-form {
  margin-top: 20px;
}

.reset-success-alert {
  margin-bottom: 20px;
}

.reset-error-alert {
  margin-top: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-card {
    width: 100%;
    margin: 16px;
    padding: 24px;
  }
}

.beian-footer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 12px;
  text-align: center;
  font-size: 0.95em;
  color: #999;
  background: transparent;
  z-index: 10;
  pointer-events: none;
  /* 适应深色模式：你可再根据主题变更颜色 */
}
.beian-footer a {
  pointer-events: auto;
  color: #999;
  text-decoration: none;
  transition: color 0.2s;
  opacity: 0.85;
}
.beian-footer a:hover {
  color: #188aec;
  text-decoration: underline;
  opacity: 1;
}

/* 如果登录框高度不够，手机版可以微调 */
@media (max-width: 768px) {
  .beian-footer {
    font-size: 0.9em;
    bottom: 8px;
  }
}
</style>