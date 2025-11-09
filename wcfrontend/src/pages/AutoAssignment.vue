<template>
  <div class="page-container">
    <div class="page-header">
      <h2>自动分配管理</h2>
      <p class="page-description">选择已结束的活动进行师生自动匹配分配</p>
    </div>

    <!-- 活动选择卡片 -->
    <el-card class="select-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>选择活动</span>
        </div>
      </template>

      <el-select
        v-model="selectedEventId"
        placeholder="请选择已结束的活动"
        size="large"
        style="width: 100%"
        @change="handleEventChange"
      >
        <el-option
          v-for="event in finishedEvents"
          :key="event.event_id"
          :label="`${event.event_name} (结束于 ${formatDate(event.tea_end_time)})`"
          :value="event.event_id"
        />
      </el-select>

      <el-alert
        v-if="selectedEventId"
        :title="`已选择: ${selectedEvent?.event_name}`"
        type="success"
        :closable="false"
        style="margin-top: 16px;"
      />
    </el-card>

    <!-- 操作按钮 -->
    <div v-if="selectedEventId" class="button-group">
      <el-button
        type="primary"
        :icon="MagicStick"
        :loading="isAutoAssigning"
        @click="handleAutoAssign"
        size="large"
      >
        {{ isAutoAssigning ? '分配中...' : '执行自动分配' }}
      </el-button>

      <el-button
        :icon="DataAnalysis"
        @click="showMatchMatrix = true"
        size="large"
      >
        查看匹配矩阵
      </el-button>

      <el-button
        :icon="Refresh"
        @click="fetchAssignments"
        size="large"
      >
        刷新
      </el-button>

      <el-button
        type="success"
        :icon="Check"
        :disabled="!hasAssignments"
        @click="handlePublish"
        size="large"
      >
        发布结果
      </el-button>
    </div>

    <!-- 统计信息 -->
    <el-row v-if="assignmentStats" :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总团队数" :value="assignmentStats.total_groups">
            <template #prefix>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="已分配" :value="assignmentStats.assigned_count">
            <template #prefix>
              <el-icon color="#67c23a"><Select /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="志愿匹配" :value="assignmentStats.preference_matched">
            <template #prefix>
              <el-icon color="#409eff"><Star /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="随机分配" :value="assignmentStats.random_assigned">
            <template #prefix>
              <el-icon color="#e6a23c"><Refresh /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分配结果表格 -->
    <el-card v-if="selectedEventId" class="table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>分配结果</span>
          <el-tag v-if="assignments.length > 0" type="success">
            共 {{ assignments.length }} 条记录
          </el-tag>
        </div>
      </template>

      <el-table
        :data="assignments"
        v-loading="loading"
        stripe
        border
      >
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="group.group_name" label="团队名称" min-width="150" />
        <el-table-column label="队长" width="120">
          <template #default="{ row }">
            {{ row.group.captain?.stu_name || '无' }}
          </template>
        </el-table-column>
        <el-table-column label="成员数" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.group.member_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="teacher.teacher_name" label="指导教师" width="120" />
        <el-table-column label="匹配得分" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.score > 10 ? 'success' : row.score > 0 ? 'primary' : 'info'"
            >
              {{ row.score }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="explanation" label="匹配说明" min-width="200" />
        <el-table-column label="分配类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.assignment_type === 'manual' ? 'warning' : ''">
              {{ row.assignment_type === 'auto' ? '自动' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              :icon="View"
              @click="handleViewOptions(row.group)"
            >
              查看选项
            </el-button>
            <el-button
              size="small"
              type="primary"
              :icon="Edit"
              @click="handleManualAssign(row.group)"
            >
              调整
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && assignments.length === 0" description="暂无分配记录" />
    </el-card>

    <!-- 匹配选项对话框 -->
    <MatchOptionsDialog
      v-model="showMatchOptions"
      :event-id="selectedEventId"
      :group-id="currentGroupId"
      :group-name="currentGroupName"
      @select="handleTeacherSelected"
    />

    <!-- 匹配矩阵对话框 -->
    <MatchMatrixDialog
      v-model="showMatchMatrix"
      :event-id="selectedEventId"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick,
  DataAnalysis,
  Refresh,
  Check,
  UserFilled,
  Select,
  Star,
  View,
  Edit
} from '@element-plus/icons-vue'
import api from '../services/api'
import MatchOptionsDialog from '../components/MatchOptionsDialog.vue'
import MatchMatrixDialog from '../components/MatchMatrixDialog.vue'

const finishedEvents = ref([])
const selectedEventId = ref(null)
const assignments = ref([])
const loading = ref(false)
const isAutoAssigning = ref(false)
const assignmentStats = ref(null)
const showMatchOptions = ref(false)
const showMatchMatrix = ref(false)
const currentGroupId = ref(null)
const currentGroupName = ref('')

const selectedEvent = computed(() =>
  finishedEvents.value.find(e => e.event_id === selectedEventId.value)
)

const hasAssignments = computed(() => assignments.value.length > 0)

const fetchFinishedEvents = async () => {
  try {
    const response = await api.getMutualSelectionEvents()
    const now = new Date()
    finishedEvents.value = response.data.filter(event => {
      const stuEnd = new Date(event.stu_end_time)
      const teaEnd = new Date(event.tea_end_time)
      return stuEnd < now && teaEnd < now
    })
  } catch (error) {
    ElMessage.error('获取活动列表失败')
    console.error('Failed to fetch events:', error)
  }
}

const handleEventChange = () => {
  assignments.value = []
  assignmentStats.value = null
  fetchAssignments()
}

const fetchAssignments = async () => {
  if (!selectedEventId.value) return

  loading.value = true
  try {
    const response = await api.getAssignments(selectedEventId.value)
    assignments.value = response.data
  } catch (error) {
    ElMessage.error('获取分配结果失败')
    console.error('Failed to fetch assignments:', error)
  } finally {
    loading.value = false
  }
}

const handleAutoAssign = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要执行自动分配吗？这将根据双向志愿和匹配算法为所有团队分配导师。',
      '确认自动分配',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    isAutoAssigning.value = true
    const response = await api.autoAssign(selectedEventId.value)
    assignmentStats.value = response.data
    ElMessage.success(response.data.message || '自动分配完成')
    await fetchAssignments()
  } catch (error) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.error || '自动分配失败'
      ElMessage.error(errorMsg)
    }
  } finally {
    isAutoAssigning.value = false
  }
}

const handleViewOptions = (group) => {
  currentGroupId.value = group.group_id
  currentGroupName.value = group.group_name
  showMatchOptions.value = true
}

const handleManualAssign = (group) => {
  handleViewOptions(group)
}

const handleTeacherSelected = async (teacherId) => {
  try {
    await api.manualAssign(selectedEventId.value, currentGroupId.value, teacherId)
    ElMessage.success('调整成功')
    await fetchAssignments()
  } catch (error) {
    const errorMsg = error.response?.data?.error || '调整失败'
    ElMessage.error(errorMsg)
  }
}

const handlePublish = async () => {
  try {
    await ElMessageBox.confirm(
      '发布后将不能再修改分配结果，确定要发布吗？',
      '确认发布',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await api.publishAssignments(selectedEventId.value)
    ElMessage.success(response.data.message || '发布成功')
    await fetchAssignments()
  } catch (error) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.error || '发布失败'
      ElMessage.error(errorMsg)
    }
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchFinishedEvents()
})
</script>

<style scoped>
.page-container {
  max-width: 1600px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.select-card,
.table-card {
  border-radius: 8px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.button-group {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stats-row {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .button-group {
    flex-direction: column;
  }

  .button-group .el-button {
    width: 100%;
  }
}
</style>