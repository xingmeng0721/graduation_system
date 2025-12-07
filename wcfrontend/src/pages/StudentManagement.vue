<template>
  <div class="page-container">
    <div class="page-header">
      <h2>学生管理</h2>
    </div>

    <!-- 批量注册学生 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>批量注册学生</span>
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
              <span class="failed-text">学号: {{ item.stu_no || '未知' }} - {{ item.error }}</span>
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

    <!-- 添加新学生 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>添加新学生</span>
        </div>
      </template>

      <el-form
        ref="addFormRef"
        :model="newStudent"
        label-width="100px"
        @submit.prevent="addStudent"
      >
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="学号">
              <el-input v-model="newStudent.stu_no" placeholder="请输入学号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="姓名">
              <el-input v-model="newStudent.stu_name" placeholder="请输入姓名" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="初始密码">
              <el-input v-model="newStudent.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="年级">
              <el-input v-model="newStudent.grade" placeholder="如: 2021" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="专业">
              <el-input v-model="newStudent.major" placeholder="请输入专业名称" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="手机号">
              <el-input v-model="newStudent.phone" placeholder="选填" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="newStudent.email" type="email" placeholder="选填" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="实习地点">
            <el-input v-model="newStudent.internship_location" placeholder="选填" clearable />
          </el-form-item>
        </el-col>
        </el-row>

        <el-alert
          v-if="addStudentError"
          :title="addStudentError"
          type="error"
          :closable="false"
          style="margin-bottom: 16px;"
        />

        <el-alert
          v-if="addStudentSuccess"
          :title="addStudentSuccess"
          type="success"
          :closable="false"
          style="margin-bottom: 16px;"
        />

        <el-form-item>
          <el-button type="primary" native-type="submit">确认添加</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 学生列表 -->
    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="card-header">学生列表</span>
          <div class="filters">
            <el-input
              v-model="searchQuery"
              placeholder="按学号或姓名搜索"
              clearable
              style="width: 200px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select v-model="selectedGrade" placeholder="选择年级" clearable style="width: 150px;">
              <el-option
                v-for="grade in uniqueGrades"
                :key="grade"
                :label="grade"
                :value="grade"
              />
            </el-select>
            <el-select v-model="selectedMajor" placeholder="选择专业" clearable style="width: 150px;">
              <el-option
                v-for="major in majors"
                :key="major.major_id"
                :label="major.major_name"
                :value="major.major_name"
              />
            </el-select>
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

      <div v-if="selectedStudentIds.size > 0" class="bulk-actions-bar">
        <span>已选择 {{ selectedStudentIds.size }} 名学生</span>
        <el-button type="danger" size="small" @click="handleDeleteSelected">
          删除选中
        </el-button>
      </div>

      <el-table
        :data="filteredStudents"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="stu_no" label="学号" min-width="120" />
        <el-table-column prop="stu_name" label="姓名" min-width="100" />
        <el-table-column prop="grade" label="年级" width="100" />
        <el-table-column prop="major_name" label="专业" min-width="120">
          <template #default="{ row }">
            {{ row.major_name || '无' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="130">
          <template #default="{ row }">
            {{ row.phone || '无' }}
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180">
          <template #default="{ row }">
            {{ row.email || '无' }}
          </template>
        </el-table-column>

        <el-table-column prop="internship_location" label="实习地点" min-width="150">
        <template #default="{ row }">
          {{ row.internship_location || '无' }}
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

      <el-empty v-if="filteredStudents.length === 0" description="没有找到符合条件的学生" />
    </el-card>

    <!-- 编辑学生对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑学生信息"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        v-if="editingStudent"
        ref="editFormRef"
        :model="editingStudent"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学号">
              <el-input v-model="editingStudent.stu_no" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="editingStudent.stu_name" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="年级">
              <el-input v-model="editingStudent.grade" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="专业">
              <el-select v-model="editingStudent.major" placeholder="选择专业" style="width: 100%;">
                <el-option
                  v-for="major in majors"
                  :key="major.major_id"
                  :label="major.major_name"
                  :value="major.major_name"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="editingStudent.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="editingStudent.email" type="email" />
            </el-form-item>
          </el-col>
        </el-row>


        <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="实习地点">
            <el-input v-model="editingStudent.internship_location" />
          </el-form-item>
        </el-col>
        </el-row>

        <el-form-item label="新密码">
          <el-input
            v-model="editingStudent.password"
            type="password"
            placeholder="留空则不修改"
            show-password
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
        <el-button type="primary" @click="handleUpdateStudent">保存更改</el-button>
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
const students = ref([])
const majors = ref([])
const searchQuery = ref('')
const selectedGrade = ref('')
const selectedMajor = ref('')
const selectedStudentIds = ref(new Set())
const editDialogVisible = ref(false)
const editingStudent = ref(null)

const newStudent = ref({
  stu_no: '',
  stu_name: '',
  password: '',
  grade: '',
  phone: '',
  major: '',
  email: '',
  internship_location: ''
})

// 批量注册
const selectedFile = ref(null)
const isUploading = ref(false)
const bulkResults = ref(null)
const bulkError = ref(null)

// 消息
const addStudentError = ref(null)
const addStudentSuccess = ref(null)
const listError = ref(null)
const listSuccess = ref(null)
const editError = ref(null)

// 数据获取
const fetchData = async () => {
  try {
    const [studentsRes, majorsRes] = await Promise.all([
      api.getStudents(),
      api.getMajors()
    ])
    students.value = studentsRes.data
    majors.value = majorsRes.data
  } catch (err) {
    console.error('Failed to fetch data:', err)
    listError.value = '加载数据失败，请刷新页面'
  }
}

onMounted(fetchData)

// 计算属性
const filteredStudents = computed(() => {
  let result = students.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(s =>
      s.stu_name.toLowerCase().includes(query) ||
      s.stu_no.toLowerCase().includes(query)
    )
  }

  if (selectedGrade.value) {
    result = result.filter(s => s.grade === selectedGrade.value)
  }

  if (selectedMajor.value) {
    result = result.filter(s => s.major_name === selectedMajor.value)
  }

  return result
})

const uniqueGrades = computed(() => {
  const grades = students.value.map(s => s.grade)
  return [...new Set(grades)].sort()
})

// 监听筛选变化
watch([selectedGrade, selectedMajor], () => {
  selectedStudentIds.value.clear()
})

// 清空消息
const clearMessages = () => {
  addStudentError.value = null
  addStudentSuccess.value = null
  listError.value = null
  listSuccess.value = null
  editError.value = null
  bulkError.value = null
}

// 添加学生
const addStudent = async () => {
  clearMessages()

  if (!newStudent.value.stu_no || !newStudent.value.stu_name || !newStudent.value.password) {
    addStudentError.value = '请填写必填项'
    return
  }

  try {
    const response = await api.createStudent(newStudent.value)
    addStudentSuccess.value = `学生 ${response.data.stu_name} 添加成功！`
    ElMessage.success(addStudentSuccess.value)

    // 清空表单
    Object.keys(newStudent.value).forEach(key => newStudent.value[key] = '')
    await fetchData()
  } catch (err) {
    addStudentError.value = '添加失败：' + (err.response?.data?.detail || '请检查输入')
    ElMessage.error(addStudentError.value)
  }
}

// 编辑学生
const openEditModal = (student) => {
  editingStudent.value = { ...student, major: student.major_name, password: '',internship_location: student.internship_location || '' }
  editError.value = null
  editDialogVisible.value = true
}

const closeEditModal = () => {
  editDialogVisible.value = false
  editingStudent.value = null
}

const handleUpdateStudent = async () => {
  clearMessages()

  if (!editingStudent.value) return

  const studentData = { ...editingStudent.value }
  if (!studentData.password) {
    delete studentData.password
  }

  try {
    await api.updateStudent(studentData.stu_id, studentData)
    listSuccess.value = `学生 ${studentData.stu_name} 的信息已更新`
    ElMessage.success(listSuccess.value)
    closeEditModal()
    await fetchData()
  } catch (err) {
    editError.value = '更新失败：' + (err.response?.data?.detail || '请检查输入')
  }
}

// 删除学生
const handleDeleteSingle = async (student) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生 ${student.stu_name} (学号: ${student.stu_no}) 吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )

    await api.deleteStudent(student.stu_id)
    listSuccess.value = `学生 ${student.stu_name} 已删除`
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
  selectedStudentIds.value = new Set(selection.map(s => s.stu_id))
}

const handleDeleteSelected = async () => {
  if (selectedStudentIds.value.size === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedStudentIds.value.size} 名学生吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )

    const idsToDelete = Array.from(selectedStudentIds.value)
    await api.bulkDeleteStudents(idsToDelete)
    listSuccess.value = `成功删除 ${idsToDelete.length} 名学生`
    ElMessage.success(listSuccess.value)
    selectedStudentIds.value.clear()
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
    const response = await api.downloadStudentTemplate()
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'student_registration_template.xlsx')
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
    const response = await api.bulkRegisterStudents(selectedFile.value.raw)
    bulkResults.value = response.data
    ElMessage.success('批量注册完成')
  } catch (err) {
    console.error('Failed to bulk register:', err)
    if (err.response && err.response.data) {
      bulkResults.value = err.response.data
      bulkError.value = `上传处理完成，但有 ${err.response.data.failure_count || 0} 个条目失败`
    } else {
      bulkError.value = '上传失败：' + (err.message || '服务器发生未知错误')
    }
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