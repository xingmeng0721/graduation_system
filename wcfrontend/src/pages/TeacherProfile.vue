<template>
  <div class="profile-page-container">
    <div v-if="isLoading" class="status-card"><div class="spinner"></div>正在加载您的信息...</div>
    <div v-if="fetchError" class="status-card error-card">{{ fetchError }}</div>

    <div v-if="teacherData" class="profile-card">
      <div class="card-header">
        <h2>教师个人信息</h2>
        <button v-if="!isEditing" @click="startEditing" class="btn btn-primary">
          <i class="icon edit"></i> 修改信息
        </button>
        <div v-else class="edit-actions">
          <button @click="cancelEditing" class="btn btn-secondary">取消</button>
          <button @click="handleUpdateProfile" class="btn btn-success" :disabled="isUpdating">
            <i v-if="!isUpdating" class="icon save"></i>
            {{ isUpdating ? '保存中...' : '保存更改' }}
          </button>
        </div>
      </div>

      <div class="profile-body">
        <div class="profile-grid">
          <!-- 只读信息 -->
          <div class="info-item">
            <label>姓名</label>
            <span>{{ teacherData.teacher_name }}</span>
          </div>
          <div class="info-item">
            <label>工号</label>
            <span>{{ teacherData.teacher_no }}</span>
          </div>

          <!-- 可编辑信息 -->
          <div class="info-item editable">
            <label for="phone">手机号</label>
            <input v-if="isEditing" v-model="editableProfile.phone" type="tel" id="phone" placeholder="请输入手机号" />
            <span v-else>{{ teacherData.phone || '未填写' }}</span>
          </div>
          <div class="info-item editable">
            <label for="email">电子邮箱</label>
            <input v-if="isEditing" v-model="editableProfile.email" type="email" id="email" placeholder="请输入电子邮箱" />
            <span v-else>{{ teacherData.email || '未填写' }}</span>
          </div>

          <div class="info-item editable full-width">
            <label for="research_direction">研究方向</label>
            <input v-if="isEditing" v-model="editableProfile.research_direction" type="text" id="research_direction"
                   placeholder="多个方向请用逗号隔开"/>
            <span v-else>{{ teacherData.research_direction || '未填写' }}</span>
          </div>

          <div class="info-item editable full-width">
            <label for="introduction">个人简介</label>
            <textarea v-if="isEditing" v-model="editableProfile.introduction" id="introduction" rows="5"
                      placeholder="介绍一下您的学术背景和经历"></textarea>
            <span v-else class="pre-wrap">{{ teacherData.introduction || '未填写' }}</span>
          </div>

          <!-- [新增] 密码修改区域，只在编辑模式下显示 -->
          <template v-if="isEditing">
            <hr class="section-divider"/>
            <div class="info-item editable">
              <label for="old_password">原密码</label>
              <input v-model="editableProfile.old_password" type="password" id="old_password"
                     placeholder="如需修改密码，请填写原密码" autocomplete="current-password"/>
            </div>
            <div class="info-item editable">
              <label for="new_password">新密码</label>
              <input v-model="editableProfile.new_password" type="password" id="new_password" placeholder="留空则不修改"
                     autocomplete="new-password"/>
            </div>
            <div class="info-item editable">
              <label for="confirm_password">确认新密码</label>
              <input v-model="editableProfile.confirm_password" type="password" id="confirm_password"
                     placeholder="再次输入新密码" autocomplete="new-password"/>
            </div>
          </template>
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="success" class="success-message">{{ success }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, reactive} from 'vue';
import api from '../services/api';

const teacherData = ref(null);
// [修改] 为 editableProfile 增加密码字段
const editableProfile = reactive({
  phone: '',
  email: '',
  research_direction: '',
  introduction: '',
  old_password: '',
  new_password: '',
  confirm_password: ''
});

const isLoading = ref(true);
const isEditing = ref(false);
const isUpdating = ref(false);

const fetchError = ref(null);
const error = ref(null);
const success = ref(null);

const fetchProfile = async () => {
  isLoading.value = true;
  fetchError.value = null;
  try {
    const response = await api.getTeacherProfile();
    teacherData.value = response.data;
  } catch (err) {
    fetchError.value = "无法加载您的个人信息，请刷新页面或稍后再试。";
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchProfile);

const startEditing = () => {
  // 将当前数据填充到可编辑对象中
  editableProfile.phone = teacherData.value.phone || '';
  editableProfile.email = teacherData.value.email || '';
  editableProfile.research_direction = teacherData.value.research_direction || '';
  editableProfile.introduction = teacherData.value.introduction || '';
  // 重置密码字段
  editableProfile.old_password = '';
  editableProfile.new_password = '';
  editableProfile.confirm_password = '';

  isEditing.value = true;
  error.value = null;
  success.value = null;
};

const cancelEditing = () => {
  isEditing.value = false;
};

const handleUpdateProfile = async () => {
  error.value = null;
  success.value = null;
  isUpdating.value = true;

  // [修改] dataToUpdate 现在包含所有密码字段
  const dataToUpdate = {...editableProfile};

  // 如果用户没有输入任何密码相关信息，则不发送这些字段
  if (!dataToUpdate.new_password && !dataToUpdate.old_password) {
    delete dataToUpdate.old_password;
    delete dataToUpdate.new_password;
    delete dataToUpdate.confirm_password;
  }

  try {
    const response = await api.updateTeacherProfile(dataToUpdate);
    teacherData.value = response.data; // 更新视图
    isEditing.value = false;
    success.value = "您的个人信息已成功更新！";
  } catch (err) {
    if (err.response && err.response.data) {
      // 将后端返回的所有错误信息格式化并显示
      const errorDetails = Object.entries(err.response.data)
          .map(([key, value]) => `${value}`)
          .join('\n');
      error.value = `更新失败: ${errorDetails}`;
    } else {
      error.value = "更新失败，请检查网络或稍后重试。";
    }
  } finally {
    isUpdating.value = false;
  }
};
</script>

<style scoped>
/* ... (样式基本保持不变，只增加一个分隔线样式) ... */
.icon {
  font-family: 'icons' !important;
  speak: never;
  font-style: normal;
  font-weight: normal;
  font-variant: normal;
  text-transform: none;
  line-height: 1;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  margin-right: 8px;
}

.icon.edit::before {
  content: '✏️';
}

.icon.save::before {
  content: '💾';
}

.profile-page-container {
  padding: 2rem;
  background-color: #F9FAFB;
  min-height: 100vh;
}

.profile-card {
  max-width: 800px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #E5E7EB;
}

.card-header h2 {
  font-size: 1.5em;
  font-weight: 700;
  color: #1F2937;
  margin: 0;
}

.profile-body {
  padding: 2rem;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem 2rem;
}

.full-width {
  grid-column: 1 / -1;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item label {
  font-size: 0.875em;
  font-weight: 600;
  color: #6B7280;
  margin-bottom: 0.5rem;
}

.info-item span {
  font-size: 1em;
  color: #374151;
  padding: 0.75rem;
  background-color: #F9FAFB;
  border-radius: 8px;
  min-height: 46px;
  display: flex;
  align-items: center;
}

.info-item span.pre-wrap {
  white-space: pre-wrap;
  align-items: flex-start;
}

.info-item input, .info-item textarea {
  padding: 0.75rem;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  font-size: 1em;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.info-item input:focus, .info-item textarea:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

textarea {
  resize: vertical;
}

.btn {
  padding: 0.6rem 1.25rem;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #3B82F6;
  color: white;
}

.btn-primary:hover {
  background-color: #2563EB;
}

.btn-secondary {
  background-color: #E5E7EB;
  color: #374151;
}

.btn-secondary:hover {
  background-color: #D1D5DB;
}

.btn-success {
  background-color: #10B981;
  color: white;
}

.btn-success:hover {
  background-color: #059669;
}

.edit-actions {
  display: flex;
  gap: 0.75rem;
}

.status-card, .error-message, .success-message {
  text-align: center;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.9em;
}

.status-card {
  max-width: 800px;
  margin: 0 auto 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  font-size: 1.1em;
  font-weight: 500;
}

.error-message {
  color: #991B1B;
  background-color: #FEE2E2;
  margin-top: 1.5rem;
  white-space: pre-line;
}

.success-message {
  color: #064E3B;
  background-color: #D1FAE5;
  margin-top: 1.5rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid currentColor;
  border-bottom-color: transparent;
  border-radius: 50%;
  display: inline-block;
  box-sizing: border-box;
  animation: rotation 1s linear infinite;
}

@keyframes rotation {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* [新增] 分隔线样式 */
.section-divider {
  grid-column: 1 / -1;
  border: none;
  border-top: 1px solid #E5E7EB;
  margin: 0.5rem 0;
}
</style>