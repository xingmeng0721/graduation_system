<template>
  <div class="page-container">
    <div class="page-header">
      <h2>选择指导团队</h2>
      <el-tag v-if="activeEvent" type="primary" size="large">
        {{ activeEvent.event_name }} - 截止: {{ formatDate(activeEvent.end_time) }}
      </el-tag>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在加载数据...</p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />

    <!-- 主要内容 -->
    <template v-if="!isLoading && activeEvent">
      <!-- 志愿选择面板 -->
      <el-card class="selection-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>我的志愿小组 (最多可选择 {{ activeEvent.teacher_choice_limit }} 个)</span>
            <el-button type="primary" @click="savePreferences">
              保存我的志愿
            </el-button>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col
            v-for="rank in choiceLimitRange"
            :key="rank"
            :span="24 / Math.min(choiceLimitRange.length, 3)"
          >
            <el-form-item :label="getPreferenceText(rank)" label-width="100px">
              <el-select
                v-model="preferences[rank]"
                placeholder="请选择团队"
                clearable
                style="width: 100%;"
              >
                <el-option
                  v-for="team in teams"
                  :key="team.group_id"
                  :label="team.group_name"
                  :value="team.group_id"
                  :disabled="isTeamSelectedInOtherPreferences(team.group_id, rank)"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 团队信息列表 -->
      <div class="teams-grid">
        <el-card
          v-for="team in teams"
          :key="team.group_id"
          :class="['team-card', { 'is-selected': getRankForTeam(team.group_id) }]"
          shadow="hover"
        >
          <template #header>
            <div class="team-card-header">
              <h3>{{ team.group_name }}</h3>
              <div class="team-tags">
                <el-tag
                  v-if="getRankForTeam(team.group_id)"
                  :type="getPreferenceTagType(getRankForTeam(team.group_id))"
                  size="small"
                >
                  {{ getPreferenceText(getRankForTeam(team.group_id)) }}
                </el-tag>
                <el-tag v-else-if="team.my_preference_rank" type="info" size="small">
                  学生志愿
                </el-tag>
                <!-- ✅ 优化：查看完整信息按钮放在标签旁边 -->
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="viewTeamDetail(team.group_id)"
                >
                  查看完整信息
                </el-button>
              </div>
            </div>
          </template>

          <!-- 项目信息 -->
          <div class="team-section">
            <h4>{{ team.project_title || '未填写项目标题' }}</h4>
            <p class="project-description">
              {{ team.project_description_short || team.project_description || '该团队尚未填写项目简介。' }}
            </p>
          </div>

          <el-divider />

          <!-- 团队成员 -->
          <div class="team-section">
            <div class="section-title">
              <span>团队成员</span>
              <el-tag size="small" type="info">{{ team.member_count }}人</el-tag>
            </div>
            <div class="members-list">
              <div
                v-for="member in team.members"
                :key="member.stu_id"
                class="member-item"
              >
                <div class="member-info">
                  <span class="member-name">{{ member.stu_name }}</span>
                  <span class="member-id">{{ member.stu_no }}</span>
                </div>
                <el-tag v-if="member.is_captain" size="small" type="warning">
                  队长
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </template>

    <!-- 无活动状态 -->
    <el-card v-if="!isLoading && !activeEvent" class="no-activity-card" shadow="never">
      <el-empty description="当前没有正在进行的互选活动">
        <template #image>
          <el-icon :size="80" color="#909399"><InfoFilled /></el-icon>
        </template>
        <p style="margin: 20px 0;">请耐心等待管理员开启新的活动</p>
      </el-empty>
    </el-card>

    <!-- ✅ 团队详情对话框 -->
    <TeacherTeamDetailDialog
      v-model="showTeamDetail"
      :group-id="currentTeamId"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, InfoFilled } from '@element-plus/icons-vue'
import api from '../services/api'
import TeacherTeamDetailDialog from '../components/TeacherTeamDetailDialog.vue'

const teams = ref([])
const activeEvent = ref(null)
const isLoading = ref(true)
const error = ref(null)
const preferences = reactive({})

// ✅ 团队详情弹窗状态
const showTeamDetail = ref(false)
const currentTeamId = ref(null)

const choiceLimitRange = computed(() => {
  if (!activeEvent.value) return []
  const limit = activeEvent.value.teacher_choice_limit || 5
  return Array.from({ length: limit }, (_, i) => i + 1)
})

const fetchDashboard = async () => {
  isLoading.value = true
  error.value = null
  try {
    const response = await api.getTeacherDashboard()
    teams.value = response.data.teams
    activeEvent.value = response.data.active_event
    Object.assign(preferences, response.data.preferences)
  } catch (err) {
    error.value = '加载数据失败，请刷新页面重试'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchDashboard)

// ✅ 查看团队详情方法
const viewTeamDetail = (groupId) => {
  currentTeamId.value = groupId
  showTeamDetail.value = true
}

const savePreferences = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要保存当前的志愿选择吗？这将覆盖您之前的选择。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    const preferencesToSubmit = {}
    for (const rank in preferences) {
      if (preferences[rank]) {
        preferencesToSubmit[rank] = preferences[rank]
      }
    }

    await api.setTeacherPreferences(preferencesToSubmit)
    ElMessage.success('志愿保存成功！')
    await fetchDashboard()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`保存失败: ${err.response?.data?.error || '未知错误'}`)
    }
  }
}

const isTeamSelectedInOtherPreferences = (teamId, currentRank) => {
  if (!teamId) return false
  for (const rank in preferences) {
    if (parseInt(rank) !== currentRank && preferences[rank] === teamId) {
      return true
    }
  }
  return false
}

const getRankForTeam = (teamId) => {
  for (const rank in preferences) {
    if (preferences[rank] === teamId) {
      return parseInt(rank)
    }
  }
  return null
}

const getPreferenceText = (rank) => {
  const numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
  return `第${numbers[rank - 1] || rank}志愿`
}

const getPreferenceTagType = (rank) => {
  const types = ['danger', 'warning', 'success', 'primary', 'info']
  return types[rank - 1] || 'info'
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
</script>

<style scoped>
.page-container {
  max-width: 1600px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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

.selection-card {
  border-radius: 8px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.teams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
}

.team-card {
  border-radius: 8px;
  transition: all 0.3s;
}

.team-card.is-selected {
  border: 2px solid #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.team-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.team-card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.team-tags {
  display: flex;
  gap: 8px;
  align-items: center;
}

.team-section {
  margin-bottom: 16px;
}

.team-section:last-child {
  margin-bottom: 0;
}

.team-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.project-description {
  color: #606266;
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  color: #606266;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.member-id {
  font-size: 12px;
  color: #909399;
}

.no-activity-card {
  border-radius: 8px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .teams-grid {
    grid-template-columns: 1fr;
  }
}
</style>