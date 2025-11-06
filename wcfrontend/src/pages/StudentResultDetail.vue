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
          <el-card v-if="resultData.my_team_info.advisor" shadow="never" style="background-color: #f5f7fa;">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="姓名">
                {{ resultData.my_team_info.advisor.teacher_name }}
              </el-descriptions-item>
              <el-descriptions-item label="工号">
                {{ resultData.my_team_info.advisor.teacher_no }}
              </el-descriptions-item>
              <el-descriptions-item label="联系电话">
                <el-text v-if="resultData.my_team_info.advisor.phone" copyable>
                  {{ resultData.my_team_info.advisor.phone }}
                </el-text>
                <span v-else>未填写</span>
              </el-descriptions-item>
              <el-descriptions-item label="电子邮箱">
                <el-text v-if="resultData.my_team_info.advisor.email" copyable>
                  {{ resultData.my_team_info.advisor.email }}
                </el-text>
                <span v-else>未填写</span>
              </el-descriptions-item>
              <el-descriptions-item label="研究方向" :span="2">
                {{ resultData.my_team_info.advisor.research_direction || '未填写' }}
              </el-descriptions-item>
              <el-descriptions-item label="个人简介" :span="2">
                <div style="max-height: 150px; overflow-y: auto; white-space: pre-wrap;">
                  {{ resultData.my_team_info.advisor.introduction || '未填写' }}
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
          <el-empty v-else description="未分配指导老师" :image-size="60" />
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
              <div style="max-height: 200px; overflow-y: auto; white-space: pre-wrap;">
                {{ resultData.my_team_info.project_description || '未填写' }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <el-divider />

        <!-- 团队成员 -->
        <div class="info-section">
          <h4>团队成员 ({{ resultData.my_team_info.member_count }}人)</h4>
          <el-table
            v-if="resultData.my_team_info.members && resultData.my_team_info.members.length > 0"
            :data="resultData.my_team_info.members"
            border
            stripe
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
            <el-table-column label="联系电话" width="120">
              <template #default="{ row }">
                <el-text v-if="row.phone" copyable size="small">
                  {{ row.phone }}
                </el-text>
                <span v-else style="color: #909399;">未填写</span>
              </template>
            </el-table-column>
            <el-table-column label="电子邮箱" min-width="150">
              <template #default="{ row }">
                <el-text v-if="row.email" copyable size="small">
                  {{ row.email }}
                </el-text>
                <span v-else style="color: #909399;">未填写</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无成员信息" :image-size="60" />
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
import { ElMessage } from 'element-plus'
import api from '../services/api'

const route = useRoute()
const isLoading = ref(true)
const error = ref(null)
const resultData = ref(null)  // ✅ 确保这一行存在

onMounted(async () => {
  const eventId = route.params.id
  console.log('正在加载活动详情，eventId:', eventId)

  try {
    const response = await api.getStudentHistoryDetail(eventId)
    console.log('API 响应数据:', response.data)
    resultData.value = response.data

    // 调试日志
    if (resultData.value) {
      console.log('活动名称:', resultData.value.event_name)
      if (resultData.value.my_team_info) {
        console.log('团队信息:', resultData.value.my_team_info.group_name)
        console.log('成员数量:', resultData.value.my_team_info.members?.length)
        console.log('导师信息:', resultData.value.my_team_info.advisor)
      }
    }
  } catch (err) {
    console.error('加载活动结果失败:', err)
    console.error('错误响应:', err.response?.data)
    error.value = '无法加载活动结果'
    ElMessage.error('加载失败: ' + (err.response?.data?.error || err.message))
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