<template>
  <div class="page-container">
    <div class="page-header">
      <h2>历史活动结果</h2>
      <p class="page-description">在这里查看您参与过的所有已结束的互选活动及其最终结果</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在加载历史活动...</p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />

    <!-- 活动列表 -->
    <div v-if="!isLoading && pastEvents.length > 0" class="events-grid">
      <el-card
        v-for="event in pastEvents"
        :key="event.event_id"
        class="event-card"
        shadow="hover"
      >
        <template #header>
          <div class="event-header">
            <h3>{{ event.event_name }}</h3>
            <el-tag type="info" size="small">已结束</el-tag>
          </div>
        </template>

        <div class="event-info">
          <div class="info-item">
            <el-icon><Calendar /></el-icon>
            <span>活动结束于: {{ formatDate(event.end_time) }}</span>
          </div>
        </div>

        <template #footer>
          <el-button type="primary" @click="viewEventDetails(event.event_id)">
            查看我的结果
          </el-button>
        </template>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-card v-if="!isLoading && pastEvents.length === 0" class="empty-card" shadow="never">
      <el-empty description="暂无已结束的活动记录">
        <template #image>
          <el-icon :size="80" color="#909399"><Document /></el-icon>
        </template>
        <p>您尚未参与任何已结束的互选活动</p>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {Loading, Calendar, Document} from '@element-plus/icons-vue'
import api from '../services/api'

const router = useRouter()
const pastEvents = ref([])
const isLoading = ref(true)
const error = ref(null)

onMounted(async () => {
  isLoading.value = true
  try {
    const response = await api.getStudentHistory()
    pastEvents.value = response.data
  } catch (err) {
    error.value = '加载历史活动失败，请稍后重试'
    console.error(err)
  } finally {
    isLoading.value = false
  }
})

const viewEventDetails = (eventId) => {
  router.push({name: 'StudentResultDetail', params: {id: eventId}})
}

const formatDate = (dt) => {
  if (!dt) return 'N/A'
  return new Date(dt).toLocaleString('zh-CN', {
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
  max-width: 1400px;
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

.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.event-card {
  border-radius: 8px;
  transition: all 0.3s;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.event-info {
  padding: 8px 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.empty-card {
  border-radius: 8px;
}

@media (max-width: 768px) {
  .events-grid {
    grid-template-columns: 1fr;
  }
}
</style>