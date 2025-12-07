<template>
  <div class="page-container">
    <div class="page-header">
      <h2>个人信息</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在加载信息...</p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />

    <!-- 个人信息卡片 -->
    <el-card v-if="student" class="profile-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>基本信息</span>
          <el-button v-if="!isEditing" type="primary" @click="startEditing">
            修改信息
          </el-button>
          <div v-else class="edit-actions">
            <el-button @click="cancelEditing">取消</el-button>
            <el-button type="primary" @click="saveProfile" :loading="isSaving">
              保存
            </el-button>
          </div>
        </div>
      </template>

      <el-form label-width="100px" class="profile-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="student.stu_name" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学号">
              <el-input v-model="student.stu_no" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="年级">
              <el-input
                v-if="isEditing"
                v-model="editableStudent.grade"
                placeholder="请输入年级"
              />
              <el-input v-else :value="student.grade" disabled />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="专业">
              <el-input
                v-if="isEditing"
                v-model="editableStudent.major"
                placeholder="请输入专业"
              />
              <el-input v-else :value="student.major || '未分配'" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input
                v-if="isEditing"
                v-model="editableStudent.phone"
                placeholder="请输入手机号"
                clearable
              />
              <el-input v-else :value="student.phone || '未填写'" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
          <el-form-item label="电子邮箱">
            <div v-if="isEditing" class="email-wrapper">
              <el-autocomplete
                v-model="editableStudent.email"
                :fetch-suggestions="querySearchEmail"
                placeholder="请输入邮箱，例如 zhangsan@qq.com"
                class="email-input"
                clearable
                :trigger-on-focus="false"
              />
            </div>
            <el-input v-else :value="student.email || '未填写'" disabled />
          </el-form-item>
        </el-col>
        </el-row>

        <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="实习地点">
            <el-input
              v-if="isEditing"
              v-model="editableStudent.internship_location"
              placeholder="请输入实习地点"
              clearable
            />
            <el-input v-else :value="student.internship_location || '未填写'" disabled />
          </el-form-item>
        </el-col>
      </el-row>

        <!-- 密码修改区域 -->
        <template v-if="isEditing">
          <el-divider content-position="left">修改密码（选填）</el-divider>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="原密码">
                <el-input
                  v-model="editableStudent.old_password"
                  type="password"
                  placeholder="如需修改密码，请填写"
                  show-password
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="新密码">
                <el-input
                  v-model="editableStudent.new_password"
                  type="password"
                  placeholder="留空则不修改"
                  show-password
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="确认新密码">
                <el-input
                  v-model="editableStudent.confirm_password"
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
          v-if="saveError"
          :title="saveError"
          type="error"
          :closable="false"
          show-icon
          style="margin-top: 16px;"
        />

        <el-alert
          v-if="saveSuccess"
          :title="saveSuccess"
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

const student = ref(null)
const loading = ref(true)
const error = ref(null)
const isEditing = ref(false)
const isSaving = ref(false)
const saveError = ref(null)
const saveSuccess = ref(null)

const editableStudent = reactive({
  grade: '',
  major: '',
  phone: '',
  email: '',
  internship_location: '',
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const emailSuffixes = [
  '@qq.com',
  '@163.com',
  '@gmail.com',
  '@outlook.com',
  '@126.com',
  '@stu.edu.cn',
  '@hotmail.com'
]

const querySearchEmail = (queryString, cb) => {
  const val = (queryString || '').trim()
  if (!val) { cb([]); return }
  if (val.includes('@')) {
    const [prefix, maybeDomain] = val.split('@')
    const suggestions = emailSuffixes
      .filter(s => !maybeDomain || s.slice(1).startsWith(maybeDomain))
      .map(s => ({ value: `${prefix}${s}` }))
    cb(suggestions.length ? suggestions : [])
    return
  }
  const suggestions = emailSuffixes.map(s => ({ value: `${val}${s}` }))
  cb(suggestions)
}

onMounted(async () => {
  try {
    const response = await api.getStudentProfile()
    student.value = response.data
  } catch {
    error.value = '无法加载个人信息，请刷新页面或稍后再试'
  } finally {
    loading.value = false
  }
})

const startEditing = () => {
  editableStudent.grade = student.value.grade
  editableStudent.major = student.value.major
  editableStudent.phone = student.value.phone || ''
  editableStudent.email = student.value.email || ''
  editableStudent.internship_location = student.value.internship_location || ''
  editableStudent.old_password = ''
  editableStudent.new_password = ''
  editableStudent.confirm_password = ''
  isEditing.value = true
  saveError.value = null
  saveSuccess.value = null
}

const cancelEditing = () => { isEditing.value = false }

const validateInputs = () => {
  const phoneRegex = /^1\d{10}$/
  const emailRegex = /^[A-Za-z0-9](?:[A-Za-z0-9._%+-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z]{2,63})+$/
  const passwordRegex = /^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]+$/

  if (editableStudent.phone && !phoneRegex.test(editableStudent.phone)) {
    ElMessage.error('请输入有效的手机号（11位数字）'); return false
  }
  if (editableStudent.email && !emailRegex.test(editableStudent.email)) {
    ElMessage.error('请输入正确的电子邮箱格式'); return false
  }
  if (editableStudent.new_password) {
    if (!passwordRegex.test(editableStudent.new_password)) {
      ElMessage.error('密码包含非法字符，请勿使用空格或中文'); return false
    }
    if (editableStudent.new_password !== editableStudent.confirm_password) {
      ElMessage.error('两次输入的新密码不一致'); return false
    }
  }
  return true
}

const saveProfile = async () => {
  if (!validateInputs()) return
  isSaving.value = true
  saveError.value = null
  saveSuccess.value = null
  const dataToUpdate = { ...editableStudent }
  if (!dataToUpdate.new_password && !dataToUpdate.old_password) {
    delete dataToUpdate.old_password
    delete dataToUpdate.new_password
    delete dataToUpdate.confirm_password
  }
  try {
    const response = await api.updateStudentProfile(dataToUpdate)
    student.value = response.data
    isEditing.value = false
    saveSuccess.value = '个人信息更新成功！'
    ElMessage.success('个人信息更新成功！')
    setTimeout(() => { saveSuccess.value = null }, 2000)
  } catch (err) {
    if (err.response && err.response.data) {
      saveError.value = `保存失败: ${Object.values(err.response.data).flat().join('\n')}`
    } else {
      saveError.value = '保存个人信息失败，请检查网络或稍后再试'
    }
    ElMessage.error(saveError.value)
  } finally { isSaving.value = false }
}
</script>

<style scoped>
.page-container { max-width: 900px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin:0; font-size:24px; font-weight:600; color:#303133; }
.loading-container { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:60px; color:#909399; }
.loading-container p { margin-top:16px; }
.profile-card { border-radius:8px; }
.card-header { display:flex; justify-content:space-between; align-items:center; font-size:16px; font-weight:600; color:#303133; }
.edit-actions { display:flex; gap:12px; }
.profile-form { margin-top:24px; }

.email-wrapper {
  width: 100%;
}
.email-input {
  width: 100%;
}
.email-input :deep(.el-input__inner) {
  height: 38px;
  line-height: 38px;
  font-size: 14px;
  padding: 0 12px;
  border-radius: 6px;
  box-sizing: border-box;
}

</style>
