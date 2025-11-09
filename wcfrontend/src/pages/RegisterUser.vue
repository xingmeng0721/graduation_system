<template>
  <div class="page-container">
    <div class="page-header">
      <h2>注册新用户</h2>
    </div>

    <div class="register-container">
      <!-- 单用户注册 -->
      <el-card class="register-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>手动添加用户</span>
          </div>
        </template>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          label-width="80px"
          @submit.prevent="handleRegister"
        >
          <el-form-item label="名称">
            <el-input
              v-model="registerForm.admin_name"
              placeholder="请输入管理员名称"
              clearable
            />
          </el-form-item>

          <el-form-item label="用户名">
            <el-input
              v-model="registerForm.admin_username"
              placeholder="请输入用户名"
              clearable
            />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>

          <el-alert
            v-if="error"
            :title="error"
            type="error"
            :closable="false"
            class="form-alert"
          />

          <el-alert
            v-if="successMessage"
            :title="successMessage"
            type="success"
            :closable="false"
            class="form-alert"
          />

          <el-button
            type="primary"
            native-type="submit"
            :loading="isSubmitting"
            style="width: 100%"
          >
            添加用户
          </el-button>
        </el-form>
      </el-card>

      <!-- 批量注册 -->
      <el-card class="register-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>通过 Excel 批量添加</span>
          </div>
        </template>

        <div class="bulk-register-content">
          <p class="description">下载模板，填写后上传</p>

          <el-button
            @click="handleDownloadTemplate"
            style="width: 100%; margin-bottom: 20px"
          >
            下载模板
          </el-button>

          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            :file-list="fileList"
          >
            <el-icon class="upload-icon">
              <Upload />
            </el-icon>
            <div class="upload-text">
              <p>点击或拖拽文件到此处上传</p>
              <p class="upload-hint">支持 .xlsx, .xls 格式</p>
            </div>
          </el-upload>

          <el-alert
            v-if="bulkError"
            :title="bulkError"
            type="error"
            :closable="false"
            class="form-alert"
          />

          <el-alert
            v-if="bulkSuccessMessage"
            :title="bulkSuccessMessage"
            type="success"
            :closable="false"
            class="form-alert"
          />

          <el-button
            type="primary"
            @click="handleBulkRegister"
            :disabled="fileList.length === 0"
            :loading="isUploading"
            style="width: 100%"
          >
            上传并注册
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import api from '../services/api'

// 单用户注册
const registerFormRef = ref(null)
const registerForm = reactive({
  admin_name: '',
  admin_username: '',
  password: ''
})
const error = ref(null)
const successMessage = ref(null)
const isSubmitting = ref(false)

const handleRegister = async () => {
  if (!registerForm.admin_name || !registerForm.admin_username || !registerForm.password) {
    error.value = '请填写完整信息'
    return
  }

  error.value = null
  successMessage.value = null
  isSubmitting.value = true

  try {
    await api.register({
      admin_name: registerForm.admin_name,
      admin_username: registerForm.admin_username,
      admin_password: registerForm.password
    })

    successMessage.value = '用户添加成功！'
    ElMessage.success('用户添加成功！')

    // 清空表单
    registerForm.admin_name = ''
    registerForm.admin_username = ''
    registerForm.password = ''
  } catch (err) {
    successMessage.value = null
    if (err.response && err.response.data) {
      const backendErrors = err.response.data
      let errorMessage = ''
      for (const field in backendErrors) {
        errorMessage += `${field}: ${backendErrors[field].join(', ')} `
      }
      error.value = errorMessage || '添加失败，请检查输入'
    } else {
      error.value = '发生网络错误或未知问题'
    }
    console.error('Register failed:', err)
  } finally {
    isSubmitting.value = false
  }
}

// 批量注册
const uploadRef = ref(null)
const fileList = ref([])
const bulkError = ref(null)
const bulkSuccessMessage = ref(null)
const isUploading = ref(false)

const handleDownloadTemplate = async () => {
  bulkError.value = null
  bulkSuccessMessage.value = null

  try {
    const response = await api.downloadTemplate()
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url

    const contentDisposition = response.headers['content-disposition']
    let filename = 'bulk_register_template.xlsx'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/)
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1]
      }
    }
    link.setAttribute('download', filename)

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('模板下载成功')
  } catch (error) {
    console.error('Failed to download template:', error)
    bulkError.value = '模板下载失败，请稍后重试'
    ElMessage.error('模板下载失败')
  }
}

const handleFileChange = (file, files) => {
  fileList.value = files
  bulkError.value = null
  bulkSuccessMessage.value = null
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const handleBulkRegister = async () => {
  if (fileList.value.length === 0) {
    bulkError.value = '请先选择一个文件'
    return
  }

  bulkError.value = null
  bulkSuccessMessage.value = null
  isUploading.value = true

  try {
    const response = await api.bulkRegister(fileList.value[0].raw)
    bulkSuccessMessage.value = response.data.message
    ElMessage.success(response.data.message)

    // 清空文件列表
    fileList.value = []
    uploadRef.value.clearFiles()
  } catch (err) {
    if (err.response && err.response.data && err.response.data.error) {
      bulkError.value = err.response.data.error
    } else {
      bulkError.value = '上传失败，发生未知错误'
    }
    ElMessage.error(bulkError.value)
    console.error('Bulk register failed:', err)
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.page-container {
  max-width: 1400px;
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

.register-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 20px;
}

.register-card {
  border-radius: 8px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.bulk-register-content {
  display: flex;
  flex-direction: column;
}

.description {
  text-align: center;
  color: #606266;
  margin-bottom: 20px;
  font-size: 14px;
}

.upload-area {
  margin-bottom: 20px;
}

.upload-icon {
  font-size: 60px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  color: #606266;
}

.upload-text p {
  margin: 0;
  line-height: 1.8;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.form-alert {
  margin-bottom: 16px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .register-container {
    grid-template-columns: 1fr;
  }
}
</style>