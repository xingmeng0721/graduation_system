<template>
  <div class="page-container">
    <div class="page-header">
      <h2 v-if="resultData">{{ resultData.event_name }} - 分配结果</h2>
      <el-button @click="$router.back()">返回历史列表</el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在加载活动结果...</p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />

    <!-- 结果内容 -->
    <div v-if="resultData" class="results-container">
      <!-- 指导的小组列表 -->
      <div class="teams-section">
        <h3 class="section-title">最终指导的小组</h3>

        <div v-if="resultData.advised_groups && resultData.advised_groups.length > 0" class="teams-grid">
          <el-card
            v-for="group in resultData.advised_groups"
            :key="group.group_id"
            class="team-card"
            shadow="hover"
          >
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4>{{ group.group_name }}</h4>
                <!-- ✅ 查看完整信息按钮 -->
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="viewTeamDetail(group.group_id)"
                >
                  查看完整信息
                </el-button>
              </div>
            </template>

            <div class="team-section">
              <h5>项目信息</h5>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="项目标题">
                  {{ group.project_title || '未填写' }}
                </el-descriptions-item>
                <el-descriptions-item label="项目简介">
                  <div style="max-height: 100px; overflow-y: auto;">
                    {{ group.project_description_short || group.project_description || '未填写' }}
                  </div>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <el-divider />

            <!-- 使用表格显示成员信息 -->
            <div class="team-section">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h5 style="margin: 0;">小组成员 ({{ group.member_count }}人)</h5>
              </div>
              <el-table
                :data="group.members"
                border
                stripe
                size="small"
              >
                <el-table-column label="姓名" width="100">
                  <template #default="{ row }">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      {{ row.stu_name }}
                      <el-tag v-if="row.is_captain" type="warning" size="small">队长</el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="stu_no" label="学号" width="120" />
                <el-table-column prop="grade" label="年级" width="80" />
                <el-table-column prop="major_name" label="专业" min-width="120" />
              </el-table>
            </div>
          </el-card>
        </div>

        <el-empty v-else description="您在该活动中未指导任何小组" />
      </div>

      <!-- 志愿信息侧边栏 -->
      <el-card class="preference-card" shadow="never">
        <template #header>
          <h3>我当时的志愿</h3>
        </template>

        <div v-if="sortedPreferences.length > 0" class="preference-list">
          <div
            v-for="rank in sortedPreferences"
            :key="rank"
            class="preference-item"
          >
            <span class="preference-label">第{{ rank }}志愿</span>
            <span class="preference-value">
              {{ getGroupName(resultData.preferences[rank]) }}
            </span>
          </div>
        </div>

        <el-empty v-else description="您在该活动中未提交任何志愿" :image-size="60" />
      </el-card>
    </div>

    <!-- ✅ 团队详情对话框 -->
    <TeacherTeamDetailDialog
      v-model="showTeamDetail"
      :group-id="currentTeamId"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import api from '../services/api'
import TeacherTeamDetailDialog from '../components/TeacherTeamDetailDialog.vue'

const route = useRoute()
const isLoading = ref(true)
const error = ref(null)
const resultData = ref(null)

// 团队详情弹窗状态
const showTeamDetail = ref(false)
const currentTeamId = ref(null)

// 查看团队详情方法
const viewTeamDetail = (groupId) => {
  currentTeamId.value = groupId
  showTeamDetail.value = true
}

onMounted(async () => {
  const eventId = route.params.id
  if (!eventId) {
    error.value = '未提供活动ID'
    isLoading.value = false
    return
  }
  try {
    const response = await api.getTeacherHistoryDetail(eventId)
    resultData.value = response.data
  } catch (err) {
    error.value = '无法加载活动结果'
    console.error(err)
  } finally {
    isLoading.value = false
  }
})

const sortedPreferences = computed(() => {
  if (!resultData.value?.preferences) return []
  return Object.keys(resultData.value.preferences).sort((a, b) => parseInt(a) - parseInt(b))
})

const getGroupName = (groupId) => {
  if (!groupId || !resultData.value?.all_teams_in_event) return '未知小组'
  const team = resultData.value.all_teams_in_event.find(t => t.group_id === groupId)
  return team ? team.group_name : '小组已不存在'
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

.results-container {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 20px;
}

.teams-section {
  min-width: 0;
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.teams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 20px;
}

.team-card {
  border-radius: 8px;
}

.team-card h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}

.team-section {
  margin-bottom: 16px;
}

.team-section:last-child {
  margin-bottom: 0;
}

.team-section h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.preference-card {
  border-radius: 8px;
  height: fit-content;
  position: sticky;
  top: 20px;
}

.preference-card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.preference-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preference-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.preference-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.preference-label {
  font-size: 14px;
  color: #909399;
}

.preference-value {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

@media (max-width: 1400px) {
  .results-container {
    grid-template-columns: 1fr;
  }

  .preference-card {
    position: static;
  }

  .teams-grid {
    grid-template-columns: 1fr;
  }
}
</style>