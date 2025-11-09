<template>
  <div class="page-container">
    <div class="page-header">
      <h2>教师管理</h2>
    </div>

    <!-- 批量注册教师 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>批量注册教师</span>
        </div>
      </template>

      <div class="bulk-actions">
        <el-button @click="handleDownloadTemplate">下载模板</el-button>
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :show-file-list="false"
        >
          <el-button>选择文件</el-button>
        </el-upload>
        <el-button
          type="primary"
          @click="handleBulkUpload"
          :disabled="!selectedFile"
          :loading="isUploading"
        >
          {{ isUploading ? '上传中...' : '上传并注册' }}
        </el-button>
      </div>

      <div v-if="selectedFile" class="file-info">
        <el-tag type="info">已选择: {{ selectedFile.name }}</el-tag>
      </div>

      <!-- 批量注册结果 -->
      <div v-if="bulkResults" class="bulk-results">
        <el-divider />
        <h4>注册结果</h4>
        <el-row :gutter="20" class="result-summary">
          <el-col :span="12">
            <el-statistic title="成功" :value="bulkResults.success_count">
              <template #suffix>
                <el-icon style="color: #67c23a;"><SuccessFilled /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="12">
            <el-statistic title="失败" :value="bulkResults.failure_count">
              <template #suffix>
                <el-icon style="color: #f56c6c;"><CircleCloseFilled /></el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>

        <div v-if="bulkResults.failed_entries && bulkResults.failed_entries.length > 0" class="failed-details">
          <h5>失败详情:</h5>
          <el-scrollbar max-height="200px">
            <div v-for="(item, index) in bulkResults.failed_entries" :key="index" class="failed-item">
              <el-tag type="danger" size="small">行 {{ item.row }}</el-tag>
              <span class="failed-text">工号: {{ item.teacher_no || '未知' }} - {{ item.error }}</span>
            </div>
          </el-scrollbar>
        </div>
      </div>

      <el-alert
        v-if="bulkError"
        :title="bulkError"
        type="error"
        :closable="false"
        style="margin-top: 16px;"
      />
    </el-card>

    <!-- 添加新教师 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>添加新教师</span>
        </div>
      </template>

      <el-form
        ref="addFormRef"
        :model="newTeacher"
        label-width="100px"
        @submit.prevent="addTeacher"
      >
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="工号">
              <el-input v-model="newTeacher.teacher_no" placeholder="请输入工号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="姓名">
              <el-input v-model="newTeacher.teacher_name" placeholder="请输入姓名" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="初始密码">
              <el-input v-model="newTeacher.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="手机号">
              <el-input v-model="newTeacher.phone" placeholder="选填" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="电子邮箱">
              <el-input v-model="newTeacher.email" type="email" placeholder="选填" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="研究方向">
              <el-input v-model="newTeacher.research_direction" placeholder="选填" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="简介">
              <el-input
                v-model="newTeacher.introduction"
                type="textarea"
                :rows="3"
                placeholder="选填"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          v-if="addTeacherError"
          :title="addTeacherError"
          type="error"
          :closable="false"
          style="margin-bottom: 16px;"
        />

        <el-alert
          v-if="addTeacherSuccess"
          :title="addTeacherSuccess"
          type="success"
          :closable="false"
          style="margin-bottom: 16px;"
        />

        <el-form-item>
          <el-button type="primary" native-type="submit">确认添加</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 教师列表 -->
    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="card-header">教师列表</span>
          <div class="filters">
            <el-input
              v-model="searchQuery"
              placeholder="按工号或姓名搜索"
              clearable
              style="width: 250px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <el-alert
        v-if="listSuccess"
        :title="listSuccess"
        type="success"
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <el-alert
        v-if="listError"
        :title="listError"
        type="error"
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <div v-if="selectedTeacherIds.size > 0" class="bulk-actions-bar">
        <span>已选择 {{ selectedTeacherIds.size }} 名教师</span>
        <el-button type="danger" size="small" @click="handleDeleteSelected">
          删除选中
        </el-button>
      </div>

      <el-table
        :data="filteredTeachers"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="teacher_no" label="工号" min-width="120" />
        <el-table-column prop="teacher_name" label="姓名" min-width="100" />
        <el-table-column prop="research_direction" label="研究方向" min-width="150">
          <template #default="{ row }">
            {{ row.research_direction || '无' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="130">
          <template #default="{ row }">
            {{ row.phone || '无' }}
          </template>
        </el-table-column>
        <el-table-column prop="email" label="电子邮箱" min-width="180">
          <template #default="{ row }">
            {{ row.email || '无' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="openEditModal(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" link @click="handleDeleteSingle(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredTeachers.length === 0" description="没有找到符合条件的教师" />
    </el-card>

    <!-- 编辑教师对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑教师信息"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        v-if="editingTeacher"
        ref="editFormRef"
        :model="editingTeacher"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号">
              <el-input v-model="editingTeacher.teacher_no" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="editingTeacher.teacher_name" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="editingTeacher.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电子邮箱">
              <el-input v-model="editingTeacher.email" type="email" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="研究方向">
              <el-input v-model="editingTeacher.research_direction" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="新密码">
              <el-input
                v-model="editingTeacher.password"
                type="password"
                placeholder="留空则不修改"
                show-password
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="简介">
          <el-input
            v-model="editingTeacher.introduction"
            type="textarea"
            :rows="3"
          />
        </el-form-item>

        <el-alert
          v-if="editError"
          :title="editError"
          type="error"
          :closable="false"
        />
      </el-form>

      <template #footer>
        <el-button @click="closeEditModal">取消</el-button>
        <el-button type="primary" @click="handleUpdateTeacher">保存更改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import api from '../services/api'

// 状态定义
const teachers = ref([])
const searchQuery = ref('')
const selectedTeacherIds = ref(new Set())
const editDialogVisible = ref(false)
const editingTeacher = ref(null)

const newTeacher = ref({
  teacher_no: '',
  teacher_name: '',
  password: '',
  phone: '',
  email: '',
  research_direction: '',
  introduction: ''
})

// 批量注册
const selectedFile = ref(null)
const isUploading = ref(false)
const bulkResults = ref(null)
const bulkError = ref(null)

// 消息
const addTeacherError = ref(null)
const addTeacherSuccess = ref(null)
const listError = ref(null)
const listSuccess = ref(null)
const editError = ref(null)

// 数据获取
const fetchData = async () => {
  listError.value = null
  try {
    const response = await api.getTeachers()
    teachers.value = response.data
  } catch (err) {
    console.error('Failed to fetch teachers:', err)
    listError.value = '加载教师列表失败'
  }
}

onMounted(fetchData)

// 计算属性
const filteredTeachers = computed(() => {
  let result = teachers.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      t.teacher_name.toLowerCase().includes(query) ||
      t.teacher_no.toLowerCase().includes(query)
    )
  }

  return result
})

// 监听搜索变化
watch(searchQuery, () => {
  selectedTeacherIds.value.clear()
})

// 清空消息
const clearMessages = () => {
  addTeacherError.value = null
  addTeacherSuccess.value = null
  listError.value = null
  listSuccess.value = null
  editError.value = null
  bulkError.value = null
}

// 添加教师
const addTeacher = async () => {
  clearMessages()

  if (!newTeacher.value.teacher_no || !newTeacher.value.teacher_name || !newTeacher.value.password) {
    addTeacherError.value = '请填写必填项'
    return
  }

  try {
    const response = await api.createTeacher(newTeacher.value)
    addTeacherSuccess.value = `教师 ${response.data.teacher_name} 添加成功！`
    ElMessage.success(addTeacherSuccess.value)

    // 清空表单
    Object.keys(newTeacher.value).forEach(key => newTeacher.value[key] = '')
    await fetchData()
  } catch (err) {
    const errorData = err.response?.data
    let errorMessage = '添加失败：'
    if (typeof errorData === 'object' && errorData !== null) {
      errorMessage += Object.values(errorData).flat().join(' ')
    } else {
      errorMessage += '请检查输入'
    }
    addTeacherError.value = errorMessage
    ElMessage.error(addTeacherError.value)
  }
}

// 编辑教师
const openEditModal = (teacher) => {
  editingTeacher.value = { ...teacher, password: '' }
  editError.value = null
  editDialogVisible.value = true
}

const closeEditModal = () => {
  editDialogVisible.value = false
  editingTeacher.value = null
}

const handleUpdateTeacher = async () => {
  clearMessages()

  if (!editingTeacher.value) return

  const teacherData = { ...editingTeacher.value }
  if (!teacherData.password) {
    delete teacherData.password
  }

  try {
    await api.updateTeacher(teacherData.teacher_id, teacherData)
    listSuccess.value = `教师 ${teacherData.teacher_name} 的信息已更新`
    ElMessage.success(listSuccess.value)
    closeEditModal()
    await fetchData()
  } catch (err) {
    const errorData = err.response?.data
    let errorMessage = '更新失败：'
    if (typeof errorData === 'object' && errorData !== null) {
      errorMessage += Object.values(errorData).flat().join(' ')
    } else {
      errorMessage += '请检查输入'
    }
    editError.value = errorMessage
  }
}

// 删除教师
const handleDeleteSingle = async (teacher) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除教师 ${teacher.teacher_name} (工号: ${teacher.teacher_no}) 吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )

    await api.deleteTeacher(teacher.teacher_id)
    listSuccess.value = `教师 ${teacher.teacher_name} 已删除`
    ElMessage.success(listSuccess.value)
    await fetchData()
  } catch (err) {
    if (err !== 'cancel') {
      listError.value = `删除失败: ${err.response?.data?.detail || '服务器错误'}`
      ElMessage.error(listError.value)
    }
  }
}

// 表格选择
const handleSelectionChange = (selection) => {
  selectedTeacherIds.value = new Set(selection.map(t => t.teacher_id))
}

const handleDeleteSelected = async () => {
  if (selectedTeacherIds.value.size === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTeacherIds.value.size} 名教师吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )

    const idsToDelete = Array.from(selectedTeacherIds.value)
    await api.bulkDeleteTeachers(idsToDelete)
    listSuccess.value = `成功删除 ${idsToDelete.length} 名教师`
    ElMessage.success(listSuccess.value)
    selectedTeacherIds.value.clear()
    await fetchData()
  } catch (err) {
    if (err !== 'cancel') {
      listError.value = `批量删除失败: ${err.response?.data?.error || '服务器错误'}`
      ElMessage.error(listError.value)
    }
  }
}

// 批量注册
const handleDownloadTemplate = async () => {
  try {
    const response = await api.downloadTeacherTemplate()
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'teacher_registration_template.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    ElMessage.success('模板下载成功')
  } catch (err) {
    bulkError.value = '下载模板失败'
    ElMessage.error(bulkError.value)
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file
  bulkResults.value = null
  bulkError.value = null
}

const handleBulkUpload = async () => {
  if (!selectedFile.value) {
    bulkError.value = '请先选择文件'
    return
  }

  isUploading.value = true
  bulkError.value = null
  bulkResults.value = null

  try {
    const response = await api.bulkRegisterTeachers(selectedFile.value.raw)
    bulkResults.value = response.data
    ElMessage.success('批量注册完成')
  } catch (err) {
    console.error('Failed to bulk register:', err)
    bulkError.value = '上传失败：' + (err.response?.data?.error || '服务器发生未知错误')
  } finally {
    isUploading.value = false
    selectedFile.value = null
    await fetchData()
  }
}
</script>

<style scoped>
.page-container {
  max-width: 1600px;
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

.form-card,
.list-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.bulk-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.file-info {
  margin-top: 16px;
}

.bulk-results {
  margin-top: 20px;
}

.bulk-results h4,
.bulk-results h5 {
  margin: 16px 0;
  font-weight: 600;
  color: #303133;
}

.result-summary {
  margin: 20px 0;
}

.failed-details {
  margin-top: 20px;
}

.failed-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.failed-text {
  flex: 1;
  color: #606266;
  font-size: 14px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.bulk-actions-bar {
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  padding: 12px 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bulk-actions-bar span {
  font-weight: 600;
  color: #409eff;
}

@media (max-width: 1200px) {
  .list-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>