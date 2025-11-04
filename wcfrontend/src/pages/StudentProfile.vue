<template>
  <div class="profile-page-container">
    <div v-if="loading" class="status-card"><div class="spinner"></div>正在加载信息...</div>
    <div v-if="error" class="status-card error-card">{{ error }}</div>

    <div v-if="student" class="profile-card">
      <div class="card-header">
        <h2>个人信息</h2>
        <button v-if="!isEditing" @click="startEditing" class="btn btn-primary">
          <i class="icon edit"></i> 修改
        </button>
        <div v-else class="edit-actions">
          <button @click="cancelEditing" class="btn btn-secondary">取消</button>
          <button @click="saveProfile" class="btn btn-success" :disabled="isSaving">
            <i v-if="!isSaving" class="icon save"></i> {{ isSaving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>

      <div class="profile-body">
        <div class="profile-grid">
          <!-- 只读信息 -->
          <div class="info-item">
            <label>姓名</label>
            <span>{{ student.stu_name }}</span>
          </div>
          <div class="info-item">
            <label>学号</label>
            <span>{{ student.stu_no }}</span>
          </div>
          <div class="info-item">
            <label>年级</label>
            <span>{{ student.grade }}</span>
          </div>
          <div class="info-item">
            <label>专业</label>
            <span>{{ student.major || '未分配' }}</span>
          </div>

          <!-- 可编辑信息 -->
          <div class="info-item editable">
            <label for="phone">手机号</label>
            <input v-if="isEditing" v-model="editableStudent.phone" type="tel" id="phone" placeholder="请输入手机号" />
            <span v-else>{{ student.phone || '未填写' }}</span>
          </div>
          <div class="info-item editable">
            <label for="email">电子邮箱</label>
            <input v-if="isEditing" v-model="editableStudent.email" type="email" id="email" placeholder="请输入电子邮箱" />
            <span v-else>{{ student.email || '未填写' }}</span>
          </div>

          <!-- [新增] 密码修改区域 -->
          <template v-if="isEditing">
            <hr class="section-divider" />
            <div class="info-item editable">
              <label for="old_password">原密码</label>
              <input v-model="editableStudent.old_password" type="password" id="old_password" placeholder="如需修改密码，请填写" autocomplete="current-password" />
            </div>
             <div class="info-item editable">
              <label for="new_password">新密码</label>
              <input v-model="editableStudent.new_password" type="password" id="new_password" placeholder="留空则不修改" autocomplete="new-password" />
            </div>
            <div class="info-item editable">
              <label for="confirm_password">确认新密码</label>
              <input v-model="editableStudent.confirm_password" type="password" id="confirm_password" placeholder="再次输入新密码" autocomplete="new-password" />
            </div>
          </template>
        </div>

        <!-- [新增] 成功/失败消息提示 -->
        <div v-if="saveSuccess" class="success-message">{{ saveSuccess }}</div>
        <div v-if="saveError" class="error-message">{{ saveError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import api from '../services/api';

const student = ref(null);
const loading = ref(true);
const error = ref(null); // 用于加载时错误
const isEditing = ref(false);
const isSaving = ref(false);
const saveError = ref(null);
const saveSuccess = ref(null);

// [修改] 为 editableStudent 增加密码字段
const editableStudent = reactive({
  phone: '',
  email: '',
  old_password: '',
  new_password: '',
  confirm_password: '',
});

onMounted(async () => {
  try {
    const response = await api.getStudentProfile();
    student.value = response.data;
  } catch (err) {
    error.value = '无法加载个人信息，请刷新页面或稍后再试。';
  } finally {
    loading.value = false;
  }
});

// 进入编辑模式
const startEditing = () => {
  editableStudent.phone = student.value.phone || '';
  editableStudent.email = student.value.email || '';
  editableStudent.old_password = '';
  editableStudent.new_password = '';
  editableStudent.confirm_password = '';

  isEditing.value = true;
  saveError.value = null;
  saveSuccess.value = null;
};

// 取消编辑
const cancelEditing = () => {
  isEditing.value = false;
};

// 保存修改
const saveProfile = async () => {
  isSaving.value = true;
  saveError.value = null;
  saveSuccess.value = null;

  const dataToUpdate = { ...editableStudent };

  // 如果用户没有输入任何密码相关信息，则不发送密码字段
  if (!dataToUpdate.new_password && !dataToUpdate.old_password) {
    delete dataToUpdate.old_password;
    delete dataToUpdate.new_password;
    delete dataToUpdate.confirm_password;
  }

  try {
    const response = await api.updateStudentProfile(dataToUpdate);
    student.value = response.data;
    isEditing.value = false;
    saveSuccess.value = '个人信息更新成功！';
    // 2秒后清除成功消息
    setTimeout(() => { saveSuccess.value = null; }, 2000);
  } catch (err) {
    if (err.response && err.response.data) {
        const errorDetails = Object.values(err.response.data).flat().join('\n');
        saveError.value = `保存失败: ${errorDetails}`;
    } else {
        saveError.value = '保存个人信息失败，请检查网络或稍后再试。';
    }
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
/* 伪图标 */
.icon {
  font-family: 'icons' !important; speak: never; font-style: normal; font-weight: normal; font-variant: normal;
  text-transform: none; line-height: 1; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
  margin-right: 8px;
}
.icon.edit::before { content: '✏️'; }
.icon.save::before { content: '💾'; }

.profile-page-container {
  padding: 2rem;
  background-color: #F9FAFB;
  min-height: 100vh;
}

.profile-card {
  max-width: 800px; margin: 0 auto; background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1.5rem 2rem; border-bottom: 1px solid #E5E7EB;
}
.card-header h2 {
  font-size: 1.5em; font-weight: 700; color: #1F2937; margin: 0;
}

.profile-body { padding: 2rem; }
.profile-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem 2rem; }

.info-item { display: flex; flex-direction: column; }
.info-item label {
  font-size: 0.875em; font-weight: 600; color: #6B7280; margin-bottom: 0.5rem;
}
.info-item span {
  font-size: 1em; color: #374151; padding: 0.75rem;
  background-color: #F9FAFB; border-radius: 8px;
  min-height: 46px; display: flex; align-items: center;
}
.info-item input {
  padding: 0.75rem; border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 1em; transition: border-color 0.2s, box-shadow 0.2s;
}
.info-item input:focus {
  outline: none; border-color: #3B82F6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.btn {
  padding: 0.6rem 1.25rem; border: 1px solid transparent; border-radius: 8px;
  cursor: pointer; font-size: 0.9em; font-weight: 600;
  transition: all 0.2s ease; display: inline-flex; align-items: center; justify-content: center;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary { background-color: #3B82F6; color: white; }
.btn-primary:hover { background-color: #2563EB; }
.btn-secondary { background-color: #E5E7EB; color: #374151; }
.btn-secondary:hover { background-color: #D1D5DB; }
.btn-success { background-color: #10B981; color: white; }
.btn-success:hover { background-color: #059669; }

.edit-actions { display: flex; gap: 0.75rem; }

.status-card {
  text-align: center; padding: 3rem; border-radius: 12px;
  background-color: #fff; max-width: 800px; margin: 0 auto;
  display: flex; align-items: center; justify-content: center; gap: 1rem;
  font-size: 1.1em; font-weight: 500;
}
.error-card { background-color: #FEE2E2; color: #991B1B; }

.spinner {
  width: 24px; height: 24px; border: 3px solid currentColor;
  border-bottom-color: transparent; border-radius: 50%;
  display: inline-block; box-sizing: border-box;
  animation: rotation 1s linear infinite;
}
@keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.section-divider {
  grid-column: 1 / -1; border: none;
  border-top: 1px solid #E5E7EB; margin: 0.5rem 0;
}
.error-message, .success-message {
  grid-column: 1 / -1;
  text-align: left; margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 8px;
  font-size: 0.9em; white-space: pre-line;
}
.error-message { color: #991B1B; background-color: #FEE2E2; }
.success-message { color: #064E3B; background-color: #D1FAE5; }
</style>