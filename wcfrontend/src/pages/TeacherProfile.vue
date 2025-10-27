<template>
  <div>
    <h1>个人信息管理</h1>
    <div v-if="isLoading" class="loading-message">正在加载您的信息...</div>

    <div v-if="teacherData" class="profile-card">
      <form @submit.prevent="handleUpdateProfile">
        <div class="form-grid">
          <div class="form-group">
            <label>工号</label>
            <input :value="teacherData.teacher_no" type="text" disabled />
          </div>
          <div class="form-group">
            <label>姓名</label>
            <input v-model="editableProfile.teacher_name" type="text" required />
          </div>
          <div class="form-group">
            <label>手机号</label>
            <input v-model="editableProfile.phone" type="text" />
          </div>
          <div class="form-group">
            <label>电子邮箱</label>
            <input v-model="editableProfile.email" type="email" />
          </div>
          <div class="form-group">
            <label>研究方向</label>
            <input v-model="editableProfile.research_direction" type="text" />
          </div>
          <div class="form-group">
            <label>新密码 (留空则不修改)</label>
            <input v-model="editableProfile.password" type="password" placeholder="输入新密码以更新" />
          </div>
          <div class="form-group form-group-full">
            <label>简介</label>
            <textarea v-model="editableProfile.introduction"></textarea>
          </div>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="success" class="success-message">{{ success }}</div>

        <button type="submit" class="btn-submit" :disabled="isUpdating">
          {{ isUpdating ? '更新中...' : '保存更改' }}
        </button>
      </form>
    </div>

    <div v-if="fetchError" class="error-message">
      {{ fetchError }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const teacherData = ref(null);
const editableProfile = ref({});
const isLoading = ref(true);
const isUpdating = ref(false);

const fetchError = ref(null);
const error = ref(null);
const success = ref(null);

const fetchProfile = async () => {
  try {
    const response = await api.getTeacherProfile();
    teacherData.value = response.data;
    // 创建一个可编辑的副本，用于表单绑定
    editableProfile.value = { ...response.data, password: '' };
  } catch (err) {
    console.error("Failed to fetch profile:", err);
    fetchError.value = "无法加载您的个人信息，请稍后重试。";
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchProfile);

const handleUpdateProfile = async () => {
  error.value = null;
  success.value = null;
  isUpdating.value = true;

  // 准备要发送的数据
  const dataToUpdate = { ...editableProfile.value };
  // 如果密码字段为空，则从要发送的数据中删除它
  if (!dataToUpdate.password) {
    delete dataToUpdate.password;
  }

  try {
    await api.updateTeacherProfile(dataToUpdate);
    success.value = "您的个人信息已成功更新！";
    // 重新获取最新信息以同步显示
    await fetchProfile();
  } catch (err) {
    console.error("Failed to update profile:", err);
    error.value = "更新失败：" + (err.response?.data?.detail || "服务器错误，请重试。");
  } finally {
    isUpdating.value = false;
  }
};
</script>

<style scoped>
/* 复用并调整通用样式 */
.profile-card { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
.form-group { display: flex; flex-direction: column; }
.form-group-full { grid-column: 1 / -1; }
label { margin-bottom: 8px; font-weight: 600; }
input, textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-family: inherit; }
input[disabled] { background-color: #e9ecef; cursor: not-allowed; }
textarea { resize: vertical; min-height: 100px; }
.btn-submit { margin-top: 20px; padding: 12px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-submit:disabled { background-color: #a0cffc; }
.error-message, .success-message, .loading-message { text-align: center; margin-top: 15px; padding: 10px; border-radius: 4px; }
.error-message { color: #dc3545; background-color: #f8d7da; }
.success-message { color: #155724; background-color: #d4edda; }
.loading-message { color: #004085; background-color: #cce5ff; }
</style>