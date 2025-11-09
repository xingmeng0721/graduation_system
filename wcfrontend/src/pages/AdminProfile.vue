<template>
  <div class="page-container">
    <div class="page-header">
      <h2>个人信息管理</h2>
    </div>

    <el-card class="profile-card" shadow="never">
      <el-form
        ref="profileFormRef"
        :model="profile"
        label-width="120px"
        size="large"
      >
        <el-form-item label="用户名">
          <el-input v-model="profile.admin_username" disabled />
          <span style="color: #909399; font-size: 12px;">用户名不可修改</span>
        </el-form-item>

        <el-form-item label="姓名">
          <el-input v-model="profile.admin_name" placeholder="请输入姓名" />
        </el-form-item>

        <el-divider />

        <el-form-item label="旧密码">
          <el-input
            v-model="profile.old_password"
            type="password"
            placeholder="修改密码时需要输入旧密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码">
          <el-input
            v-model="profile.new_password"
            type="password"
            placeholder="不修改密码可留空"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleUpdateProfile" :loading="loading">
            保存修改
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api'

const profileFormRef = ref(null)
const loading = ref(false)
const profile = ref({
  admin_username: '',
  admin_name: '',
  old_password: '',
  new_password: ''
})

const fetchProfile = async () => {
  try {
    const response = await api.getAdminProfile()
    profile.value.admin_username = response.data.admin_username
    profile.value.admin_name = response.data.admin_name
  } catch (error) {
    ElMessage.error('获取个人信息失败')
    console.error(error)
  }
}

const handleUpdateProfile = async () => {
  loading.value = true
  try {
    const updateData = {
      admin_name: profile.value.admin_name
    }

    if (profile.value.new_password) {
      if (!profile.value.old_password) {
        ElMessage.warning('修改密码需要输入旧密码')
        loading.value = false
        return
      }
      updateData.old_password = profile.value.old_password
      updateData.new_password = profile.value.new_password
    }

    await api.updateAdminProfile(updateData)
    ElMessage.success('信息更新成功')

    profile.value.old_password = ''
    profile.value.new_password = ''

    await fetchProfile()
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '更新失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchProfile)
</script>

<style scoped>
.page-container {
  max-width: 800px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.profile-card {
  border-radius: 8px;
}
</style>