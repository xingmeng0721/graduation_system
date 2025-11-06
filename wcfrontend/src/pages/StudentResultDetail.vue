<template>
  <div class="page-container">
    <div class="page-header">
      <h2 v-if="resultData">{{ resultData.event_name }} - 活动结果</h2>
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
    <div v-if="resultData && resultData.my_team_info" class="results-container">
      <!-- 团队信息卡片 -->
      <el-card class="team-card" shadow="never">
        <template #header>
          <div class="card-header">
            <h3>{{ resultData.my_team_info.group_name }}</h3>
          </div>
        </template>

        <!-- 最终指导老师 -->
        <div class="info-section">
          <h4>最终指导老师</h4>
          <el-tag
            v-if="resultData.my_team_info.advisor"
            type="success"
            size="large"
            effect="plain"
          >
            {{ resultData.my_team_info.advisor.teacher_name }}
          </el-tag>
          <el-tag v-else type="info" size="large" effect="plain">
            未分配
          </el-tag>
        </div>

        <el-divider />

        <!-- 项目信息 -->
        <div class="info-section">
          <h4>项目信息</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="项目标题">
              {{ resultData.my_team_info.project_title || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="项目简介">
              {{ resultData.my_team_info.project_description || '未填写' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <el-divider />

        <!-- 团队成员 -->
        <div class="info-section">
          <h4>团队成员</h4>
          <div class="members-list">
            <div
              v-for="member in resultData.my_team_info.members"
              :key="member.stu_id"
              class="member-item"
            >
              <div class="member-info">
                <span class="member-name">{{ member.stu_name }}</span>
                <span class="member-no">{{ member.stu_no }}</span>
              </div>
              <el-tag v-if="member.is_captain" type="warning" size="small">
                队长
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 志愿信息卡片 -->
      <el-card class="preference-card" shadow="never">
        <template #header>
          <h3>我当时的志愿</h3>
        </template>

        <div class="preference-list">
          <div class="preference-item">
            <span class="preference-label">第一志愿</span>
            <span class="preference-value">
              {{ resultData.my_team_info.preferred_advisor_1?.teacher_name || '未选择' }}
            </span>
          </div>
          <div class="preference-item">
            <span class="preference-label">第二志愿</span>
            <span class="preference-value">
              {{ resultData.my_team_info.preferred_advisor_2?.teacher_name || '未选择' }}
            </span>
          </div>
          <div class="preference-item">
            <span class="preference-label">第三志愿</span>
            <span class="preference-value">
              {{ resultData.my_team_info.preferred_advisor_3?.teacher_name || '未选择' }}
            </span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 未参与提示 -->
    <el-card v-if="resultData && !resultData.my_team_info" class="no-team-card" shadow="never">
      <el-empty description="您在该活动中未加入任何团队" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import api from '../services/api'

const route = useRoute()
const isLoading = ref(true)
const error = ref(null)
const resultData = ref(null)

onMounted(async () => {
  const eventId = route.params.id
  try {
    const response = await api.getStudentHistoryDetail(eventId)
    resultData.value = response.data
  } catch (err) {
    error.value = '无法加载活动结果'
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.page-container {
  max-width: 1200px;
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
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.team-card,
.preference-card,
.no-team-card {
  border-radius: 8px;
}

.card-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.info-section {
  margin-bottom: 24px;
}

.info-section:last-child {
  margin-bottom: 0;
}

.info-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.member-no {
  font-size: 13px;
  color: #909399;
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
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

@media (max-width: 1024px) {
  .results-container {
    grid-template-columns: 1fr;
  }
}
</style>