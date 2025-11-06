<template>
  <div class="page-container">
    <div class="page-header">
      <h2>互选活动管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openModal()">创建新活动</el-button>
        <el-button
          type="danger"
          :disabled="selectedEvents.length === 0"
          @click="handleBulkDelete"
        >
          批量删除 ({{ selectedEvents.length }})
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="events"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="event_name" label="活动名称" min-width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="学生互选时间" min-width="200">
          <template #default="{ row }">
            {{ formatDateTimeRange(row.stu_start_time, row.stu_end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="教师互选时间" min-width="200">
          <template #default="{ row }">
            {{ formatDateTimeRange(row.tea_start_time, row.tea_end_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="teacher_choice_limit" label="教师可选数" width="120" align="center" />
        <el-table-column prop="teacher_count" label="参与教师" width="100" align="center" />
        <el-table-column prop="student_count" label="参与学生" width="100" align="center" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="openModal(row)"
              :disabled="row.status === '已结束'"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDelete(row.event_id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && events.length === 0" description="暂无活动数据" />
    </el-card>

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="isModalVisible"
      :title="isEditing ? '编辑活动' : '创建新活动'"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-form
        :model="currentEvent"
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="活动名称">
          <el-input
            v-model="currentEvent.event_name"
            placeholder="请输入活动名称"
            clearable
          />
        </el-form-item>

        <el-divider content-position="left">时间设置</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学生开始时间">
              <el-input
                v-model="currentEvent.stu_start_time"
                type="datetime-local"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学生截止时间">
              <el-input
                v-model="currentEvent.stu_end_time"
                type="datetime-local"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="教师开始时间">
              <el-input
                v-model="currentEvent.tea_start_time"
                type="datetime-local"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教师截止时间">
              <el-input
                v-model="currentEvent.tea_end_time"
                type="datetime-local"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="教师可选小组数">
          <el-input-number
            v-model="currentEvent.teacher_choice_limit"
            :min="1"
            :max="100"
            style="width: 200px;"
          />
        </el-form-item>

        <el-divider content-position="left">参与人员</el-divider>

        <!-- 选择教师 -->
        <el-form-item label="选择教师">
          <div class="selection-toolbar">
            <el-button size="small" @click="selectAllTeachers">全选</el-button>
            <el-button size="small" @click="deselectAllTeachers">清空</el-button>
            <el-tag type="info">已选择 {{ currentEvent.teachers.length }} 人</el-tag>
          </div>
          <AdvancedMultiSelect v-model="currentEvent.teachers" :items="teacherOptions" />
        </el-form-item>

        <!-- 选择学生 -->
        <el-form-item label="选择学生">
          <div class="selection-toolbar">
            <el-select
              v-model="studentGradeFilter"
              placeholder="所有年级"
              clearable
              size="small"
              style="width: 150px;"
            >
              <el-option
                v-for="grade in uniqueGrades"
                :key="grade"
                :label="grade"
                :value="grade"
              />
            </el-select>
            <el-select
              v-model="studentMajorFilter"
              placeholder="所有专业"
              clearable
              size="small"
              style="width: 150px;"
            >
              <el-option
                v-for="major in allMajors"
                :key="major.major_id"
                :label="major.major_name"
                :value="major.major_name"
              />
            </el-select>
            <el-button size="small" @click="selectAllFilteredStudents">全选当前</el-button>
            <el-button size="small" @click="deselectAllStudents">清空</el-button>
            <el-tag type="info">已选择 {{ currentEvent.students.length }} 人</el-tag>
          </div>
          <AdvancedMultiSelect v-model="currentEvent.students" :items="studentOptions" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="closeModal">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../services/api'
import AdvancedMultiSelect from '../components/AdvancedMultiSelect.vue'

// --- 响应式状态 ---
const events = ref([])
const loading = ref(false)
const isModalVisible = ref(false)
const isEditing = ref(false)
const currentEvent = ref({})
const selectedEvents = ref([])
const allTeachers = ref([])
const allStudents = ref([])
const allMajors = ref([])
const studentGradeFilter = ref('')
const studentMajorFilter = ref('')

// --- 计算属性 ---
const busyTeacherIds = computed(() => {
  const busyIds = new Set()
  const eventIdToExclude = isEditing.value ? currentEvent.value.event_id : null
  events.value.forEach(event => {
    if (event.event_id !== eventIdToExclude && event.status !== '已结束') {
      event.teachers.forEach(t => busyIds.add(t.teacher_id))
    }
  })
  return busyIds
})

const busyStudentIds = computed(() => {
  const busyIds = new Set()
  const eventIdToExclude = isEditing.value ? currentEvent.value.event_id : null
  events.value.forEach(event => {
    if (event.event_id !== eventIdToExclude && event.status !== '已结束') {
      event.students.forEach(s => busyIds.add(s.stu_id))
    }
  })
  return busyIds
})

const teacherOptions = computed(() => {
  return allTeachers.value.map(teacher => ({
    value: teacher.teacher_id,
    label: `${teacher.teacher_name} (${teacher.teacher_no})`,
    disabled: isTeacherBusy(teacher.teacher_id)
  }))
})

const studentOptions = computed(() => {
  const filtered = allStudents.value.filter(student =>
    (!studentGradeFilter.value || student.grade === studentGradeFilter.value) &&
    (!studentMajorFilter.value || student.major_name === studentMajorFilter.value)
  )
  return filtered.map(student => ({
    value: student.stu_id,
    label: `${student.stu_name} (${student.stu_no}) - ${student.major_name || '无专业'}`,
    disabled: isStudentBusy(student.stu_id)
  }))
})

const uniqueGrades = computed(() => [...new Set(allStudents.value.map(s => s.grade))].sort())

// --- 数据获取 ---
const fetchAllData = async () => {
  loading.value = true
  try {
    const [eventRes, teacherRes, studentRes, majorRes] = await Promise.all([
      api.getMutualSelectionEvents(),
      api.getTeachers(),
      api.getStudents(),
      api.getMajors()
    ])
    events.value = eventRes.data
    allTeachers.value = teacherRes.data
    allStudents.value = studentRes.data
    allMajors.value = majorRes.data
  } catch (error) {
    console.error('获取初始数据失败:', error)
    ElMessage.error('获取数据失败！')
  } finally {
    loading.value = false
  }
}

onMounted(fetchAllData)

// --- 弹窗逻辑 ---
const openModal = (event = null) => {
  studentGradeFilter.value = ''
  studentMajorFilter.value = ''
  if (event) {
    isEditing.value = true
    currentEvent.value = {
      ...event,
      stu_start_time: formatForInputLocal(event.stu_start_time),
      stu_end_time: formatForInputLocal(event.stu_end_time),
      tea_start_time: formatForInputLocal(event.tea_start_time),
      tea_end_time: formatForInputLocal(event.tea_end_time),
      teacher_choice_limit: event.teacher_choice_limit || 5,
      teachers: event.teachers.map(t => t.teacher_id),
      students: event.students.map(s => s.stu_id)
    }
  } else {
    isEditing.value = false
    currentEvent.value = {
      event_name: '',
      stu_start_time: '',
      stu_end_time: '',
      tea_start_time: '',
      tea_end_time: '',
      teacher_choice_limit: 5,
      teachers: [],
      students: []
    }
  }
  isModalVisible.value = true
}

const closeModal = () => {
  isModalVisible.value = false
}

// --- CRUD 操作 ---
const handleSubmit = async () => {
  const toISOStringWithUTC = (localDateTime) => {
    if (!localDateTime) return null
    return new Date(localDateTime).toISOString()
  }

  const payload = {
    ...currentEvent.value,
    stu_start_time: toISOStringWithUTC(currentEvent.value.stu_start_time),
    stu_end_time: toISOStringWithUTC(currentEvent.value.stu_end_time),
    tea_start_time: toISOStringWithUTC(currentEvent.value.tea_start_time),
    tea_end_time: toISOStringWithUTC(currentEvent.value.tea_end_time)
  }

  try {
    if (isEditing.value) {
      await api.updateMutualSelectionEvent(currentEvent.value.event_id, payload)
      ElMessage.success('活动更新成功！')
    } else {
      await api.createMutualSelectionEvent(payload)
      ElMessage.success('活动创建成功！')
    }
    closeModal()
    await fetchAllData()
  } catch (error) {
    console.error('保存活动失败:', error)
    const errorData = error.response?.data
    let errorMsg = '请检查输入'
    if (typeof errorData === 'string') {
      errorMsg = errorData
    } else if (errorData) {
      errorMsg = Object.values(errorData).flat().join(' ')
    }
    ElMessage.error(`保存失败: ${errorMsg}`)
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个活动吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.deleteMutualSelectionEvent(id)
    ElMessage.success('删除成功！')
    selectedEvents.value = selectedEvents.value.filter(val => val !== id)
    await fetchAllData()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除失败:', err)
      ElMessage.error('删除失败！')
    }
  }
}

const handleBulkDelete = async () => {
  if (selectedEvents.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedEvents.value.length} 个活动吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.bulkDeleteMutualSelectionEvents({ ids: selectedEvents.value })
    ElMessage.success('批量删除成功！')
    selectedEvents.value = []
    await fetchAllData()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('批量删除失败:', err)
      ElMessage.error('批量删除失败！')
    }
  }
}

// 表格选择
const handleSelectionChange = (selection) => {
  selectedEvents.value = selection.map(item => item.event_id)
}

// --- 选择逻辑 ---
const selectAllTeachers = () => {
  currentEvent.value.teachers = teacherOptions.value
    .filter(opt => !opt.disabled)
    .map(opt => opt.value)
}

const deselectAllTeachers = () => {
  currentEvent.value.teachers = []
}

const selectAllFilteredStudents = () => {
  const currentSelected = new Set(currentEvent.value.students)
  studentOptions.value.forEach(opt => {
    if (!opt.disabled) {
      currentSelected.add(opt.value)
    }
  })
  currentEvent.value.students = Array.from(currentSelected)
}

const deselectAllStudents = () => {
  currentEvent.value.students = []
}

// --- 工具函数 ---
const isTeacherBusy = (id) => busyTeacherIds.value.has(id)
const isStudentBusy = (id) => busyStudentIds.value.has(id)
const formatDateTime = (dt) => dt ? new Date(dt).toLocaleString('zh-CN', { hour12: false }) : ''
const formatDateTimeRange = (start, end) => `${formatDateTime(start)} - ${formatDateTime(end)}`
const formatForInputLocal = (utcDateTime) => {
  if (!utcDateTime) return ''
  const date = new Date(utcDateTime)
  const userTimezoneOffset = date.getTimezoneOffset() * 60000
  const localDate = new Date(date.getTime() - userTimezoneOffset)
  return localDate.toISOString().slice(0, 16)
}

const getStatusType = (status) => {
  if (status === '进行中') return 'success'
  if (status === '已结束') return 'info'
  return 'warning'
}
</script>

<style scoped>
.page-container {
  max-width: 1600px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.table-card {
  border-radius: 8px;
}

.selection-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  align-items: center;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>