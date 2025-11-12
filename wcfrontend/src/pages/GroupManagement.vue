<template>
  <div class="page-container">
    <div class="page-header">
      <h2>活动监控与小组管理</h2>
      <p class="page-description">在此页面监控所有活动，管理学生分组并对活动进行预分配模拟。</p>
    </div>

    <el-card class="select-card" shadow="never">
      <template #header>
        <div class="card-header"><span>选择一个活动进行管理</span></div>
      </template>
      <el-select
        v-model="selectedEventId"
        placeholder="请选择一个活动"
        size="large"
        style="width: 100%"
        filterable
        @change="handleEventChange"
      >
        <el-option
          v-for="event in allEvents"
          :key="event.event_id"
          :label="`${event.event_name} (状态: ${getEventStatus(event)})`"
          :value="event.event_id"
        />
      </el-select>
    </el-card>

    <div v-if="loading" class="loading-container" v-loading="loading">加载活动数据中...</div>

    <div v-if="selectedEventId && eventData" class="management-content">
      <!-- ✅ 统计卡片 -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="总参与学生" :value="eventData.stats.total_students" /></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="已组队学生" :value="eventData.stats.grouped_students" /></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="未组队学生" :value="eventData.stats.ungrouped_students" /></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="已创建团队" :value="eventData.stats.total_groups" /></el-card></el-col>
      </el-row>

      <!-- ✅ 三个主要操作按钮（移到上面） -->
      <div class="action-header">
        <el-button
          type="primary"
          :icon="MagicStick"
          :loading="isAutoAssigning"
          @click="handleAutoAssign"
          size="large"
        >
          {{ isAutoAssigning ? '预分配中...' : '运行预分配模拟' }}
        </el-button>
        <el-button :icon="View" @click="showAssignmentDialog = true" size="large">
          查看（预）分配结果
        </el-button>
        <el-button :icon="DataAnalysis" @click="showMatchMatrix = true" size="large">
          查看完整匹配矩阵
        </el-button>
      </div>

      <!-- ✅ 管理布局 -->
      <div class="management-layout">
        <!-- 已创建团队 -->
        <div class="panel">
          <el-card shadow="never" class="full-height-card">
            <template #header>
              <div class="card-header">
                <span>已创建团队 ({{ eventData.groups_list.length }})</span>
                <div>
                  <el-button type="primary" :icon="Plus" @click="handleCreateGroup" size="small">新建团队</el-button>
                  <el-button link type="primary" size="small" @click="showGroupDialog = true">查看全部</el-button>
                </div>
              </div>
            </template>

            <el-table :data="eventData.groups_list.slice(0, 5)" stripe>
              <el-table-column prop="group_name" label="团队名称" show-overflow-tooltip />
              <el-table-column label="队长" prop="captain.stu_name" />
              <el-table-column label="人数" prop="member_count" align="center" />
            </el-table>
            <div v-if="eventData.groups_list.length > 5" class="table-hint">
              仅显示前5个团队，点击“查看全部”以查看更多...
            </div>
          </el-card>
        </div>

        <!-- 未组队学生 -->
        <div class="panel">
          <el-card shadow="never" class="full-height-card">
            <template #header>
              <div class="card-header">
                <span>未组队学生 ({{ eventData.stats.ungrouped_students }})</span>
                <el-button link type="primary" size="small" @click="showStudentDialog = true">查看全部</el-button>
              </div>
            </template>

            <el-table :data="eventData.ungrouped_students_list.slice(0, 6)" stripe>
              <el-table-column prop="stu_name" label="姓名" />
              <el-table-column prop="stu_no" label="学号" />
              <el-table-column prop="major_name" label="专业" />
            </el-table>
            <div v-if="eventData.ungrouped_students_list.length > 6" class="table-hint">
              仅显示部分学生，点击“查看全部”以查看更多...
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- ✅ 弹窗：团队 -->
    <el-dialog v-model="showGroupDialog" title="已创建团队" width="800px" destroy-on-close>
      <div class="dialog-scroll">
        <el-table :data="eventData.groups_list" stripe>
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="group_name" label="团队名称" />
          <el-table-column label="队长" prop="captain.stu_name" />
          <el-table-column label="人数" prop="member_count" align="center" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditGroup(row)">编辑</el-button>
              <el-popconfirm title="确定删除此团队？" @confirm="handleDeleteGroup(row)">
                <template #reference><el-button size="small" type="danger" link>删除</el-button></template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- ✅ 弹窗：未组队学生 -->
    <el-dialog v-model="showStudentDialog" title="未组队学生" width="600px" destroy-on-close>
      <el-input
        v-model="studentSearchQuery"
        placeholder="搜索姓名或学号"
        clearable
        size="small"
        :prefix-icon="Search"
        style="width: 220px; margin-bottom: 10px"
      />
      <div class="dialog-scroll">
        <el-table :data="filteredStudents" stripe>
          <el-table-column prop="stu_name" label="姓名" />
          <el-table-column prop="stu_no" label="学号" />
          <el-table-column prop="major_name" label="专业" />
        </el-table>
      </div>
    </el-dialog>

    <GroupEditDialog v-if="eventData" v-model="isGroupDialogVisible" :group-data="editingGroup" :event-data="eventData" @submitted="refreshEventData" />
    <MatchMatrixDialog v-model="showMatchMatrix" :event-id="selectedEventId" />
    <AssignmentResultsDialog v-model="showAssignmentDialog" :event-id="selectedEventId" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, DataAnalysis, Plus, View, Search } from '@element-plus/icons-vue'
import api from '../services/api'
import GroupEditDialog from '../components/GroupEditDialog.vue'
import MatchMatrixDialog from '../components/MatchMatrixDialog.vue'
import AssignmentResultsDialog from '../components/AssignmentResultsDialog.vue'

const allEvents = ref([])
const selectedEventId = ref(null)
const eventData = ref(null)
const loading = ref(false)
const isAutoAssigning = ref(false)
const showMatchMatrix = ref(false)
const isGroupDialogVisible = ref(false)
const editingGroup = ref(null)
const showAssignmentDialog = ref(false)
const showGroupDialog = ref(false)
const showStudentDialog = ref(false)
const studentSearchQuery = ref('')

const filteredStudents = computed(() => {
  if (!eventData.value) return []
  const q = studentSearchQuery.value?.toLowerCase?.() || ''
  return eventData.value.ungrouped_students_list.filter(
    s => s.stu_name.toLowerCase().includes(q) || s.stu_no.includes(q)
  )
})

const fetchAllEvents = async () => {
  try {
    const res = await api.getMutualSelectionEvents()
    allEvents.value = res.data
  } catch {
    ElMessage.error('获取活动列表失败')
  }
}

const handleEventChange = async id => {
  if (!id) {
    eventData.value = null
    return
  }
  loading.value = true
  try {
    const res = await api.getEventManagementInfo(id)
    eventData.value = res.data
  } catch {
    ElMessage.error('获取活动详情失败')
  } finally {
    loading.value = false
  }
}

const refreshEventData = async () => {
  if (selectedEventId.value) await handleEventChange(selectedEventId.value)
}

const handleCreateGroup = () => {
  editingGroup.value = null
  isGroupDialogVisible.value = true
}
const handleEditGroup = g => {
  editingGroup.value = g
  isGroupDialogVisible.value = true
}
const handleDeleteGroup = async g => {
  try {
    await api.adminDeleteGroup(g.group_id)
    ElMessage.success('团队删除成功！')
    await refreshEventData()
  } catch (e) {
    ElMessage.error(`删除失败: ${e.response?.data?.error || '未知错误'}`)
  }
}

const handleAutoAssign = async () => {
  try {
    await ElMessageBox.confirm('这将执行一次预分配模拟，结果将以弹窗形式展示。确定吗？', '确认预分配', { type: 'info' })
    isAutoAssigning.value = true
    const res = await api.autoAssign(selectedEventId.value)
    ElMessage.success(res.data.message || '预分配完成！')
    showAssignmentDialog.value = true
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '预分配失败')
  } finally {
    isAutoAssigning.value = false
  }
}

const getEventStatus = e => {
  const now = new Date()
  const s = new Date(e.stu_start_time)
  const end1 = new Date(e.stu_end_time)
  const end2 = new Date(e.tea_end_time)
  if (now > end1 && now > end2) return '已结束'
  if (now >= s) return '进行中'
  return '未开始'
}

onMounted(fetchAllEvents)
</script>

<style scoped>
.page-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
  font-size: 16px;
}

.page-header h2 {
  font-size: 26px;
  font-weight: 600;
}

.page-description {
  font-size: 16px;
  color: #666;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
}

.action-header {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.table-hint {
  text-align: center;
  color: #909399;
  font-size: 14px;
  padding: 6px 0;
}

.dialog-scroll {
  max-height: 60vh;
  overflow-y: auto;
}

.dialog-scroll::-webkit-scrollbar {
  width: 6px;
}

.dialog-scroll::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}
</style>
