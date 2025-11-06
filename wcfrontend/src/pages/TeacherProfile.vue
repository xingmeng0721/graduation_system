<template>
  <div class="page-container">
    <div class="page-header">
      <h2>教师个人信息</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在加载您的信息...</p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="fetchError"
      :title="fetchError"
      type="error"
      :closable="false"
      show-icon
    />

    <!-- 个人信息卡片 -->
    <el-card v-if="teacherData" class="profile-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>基本信息</span>
          <el-button
            v-if="!isEditing"
            type="primary"
            @click="startEditing"
          >
            修改信息
          </el-button>
          <div v-else class="edit-actions">
            <el-button @click="cancelEditing">取消</el-button>
            <el-button
              type="primary"
              @click="handleUpdateProfile"
              :loading="isUpdating"
            >
              保存更改
            </el-button>
          </div>
        </div>
      </template>

      <el-form label-width="120px" class="profile-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="teacherData.teacher_name" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工号">
              <el-input v-model="teacherData.teacher_no" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input
                v-if="isEditing"
                v-model="editableProfile.phone"
                placeholder="请输入手机号"
                clearable
              />
              <el-input v-else :value="teacherData.phone || '未填写'" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电子邮箱">
              <el-input
                v-if="isEditing"
                v-model="editableProfile.email"
                placeholder="请输入电子邮箱"
                clearable
              />
              <el-input v-else :value="teacherData.email || '未填写'" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="研究方向">
          <el-input
            v-if="isEditing"
            v-model="editableProfile.research_direction"
            placeholder="多个方向请用逗号隔开"
            clearable
          />
          <el-input v-else :value="teacherData.research_direction || '未填写'" disabled />
        </el-form-item>

        <el-form-item label="个人简介">
          <el-input
            v-if="isEditing"
            v-model="editableProfile.introduction"
            type="textarea"
            :rows="5"
            placeholder="介绍一下您的学术背景和经历"
          />
          <el-input
            v-else
            :value="teacherData.introduction || '未填写'"
            type="textarea"
            :rows="5"
            disabled
          />
        </el-form-item>

        <!-- 密码修改区域 -->
        <template v-if="isEditing">
          <el-divider content-position="left">修改密码（选填）</el-divider>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="原密码">
                <el-input
                  v-model="editableProfile.old_password"
                  type="password"
                  placeholder="如需修改密码，请填写"
                  show-password
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="新密码">
                <el-input
                  v-model="editableProfile.new_password"
                  type="password"
                  placeholder="留空则不修改"
                  show-password
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="确认新密码">
                <el-input
                  v-model="editableProfile.confirm_password"
                  type="password"
                  placeholder="再次输入新密码"
                  show-password
                />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- 消息提示 -->
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          show-icon
          style="margin-top: 16px;"
        />

        <el-alert
          v-if="success"
          :title="success"
          type="success"
          :closable="false"
          show-icon
          style="margin-top: 16px;"
        />
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '../services/api'

const teacherData = ref(null)
const editableProfile = reactive({
  phone: '',
  email: '',
  research_direction: '',
  introduction: '',
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const isLoading = ref(true)
const isEditing = ref(false)
const isUpdating = ref(false)

const fetchError = ref(null)
const error = ref(null)
const success = ref(null)

const fetchProfile = async () => {
  isLoading.value = true
  fetchError.value = null
  try {
    const response = await api.getTeacherProfile()
    teacherData.value = response.data
  } catch (err) {
    fetchError.value = '无法加载您的个人信息，请刷新页面或稍后再试'
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchProfile)

const startEditing = () => {
  editableProfile.phone = teacherData.value.phone || ''
  editableProfile.email = teacherData.value.email || ''
  editableProfile.research_direction = teacherData.value.research_direction || ''
  editableProfile.introduction = teacherData.value.introduction || ''
  editableProfile.old_password = ''
  editableProfile.new_password = ''
  editableProfile.confirm_password = ''

  isEditing.value = true
  error.value = null
  success.value = null
}

const cancelEditing = () => {
  isEditing.value = false
}

const handleUpdateProfile = async () => {
  error.value = null
  success.value = null
  isUpdating.value = true

  const dataToUpdate = { ...editableProfile }

  // 如果没有输入密码相关信息，则不发送
  if (!dataToUpdate.new_password && !dataToUpdate.old_password) {
    delete dataToUpdate.old_password
    delete dataToUpdate.new_password
    delete dataToUpdate.confirm_password
  }

  try {
    const response = await api.updateTeacherProfile(dataToUpdate)
    teacherData.value = response.data
    isEditing.value = false
    success.value = '您的个人信息已成功更新！'
    ElMessage.success('个人信息更新成功！')
  } catch (err) {
    if (err.response && err.response.data) {
      const errorDetails = Object.entries(err.response.data)
        .map(([key, value]) => `${value}`)
        .join('\n')
      error.value = `更新失败: ${errorDetails}`
    } else {
      error.value = '更新失败，请检查网络或稍后重试'
    }
    ElMessage.error(error.value)
  } finally {
    isUpdating.value = false
  }
}
</script>

<style scoped>
.page-container {
  max-width: 1000px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #909399;
}

.loading-container p {
  margin-top: 16px;
}

.profile-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.edit-actions {
  display: flex;
  gap: 12px;
}

.profile-form {
  margin-top: 24px;
}
</style>