<template>
  <div class="page-container">
    <header class="page-header">
      <h1>历史活动结果</h1>
      <p>在这里查看您参与过的所有已结束的互选活动及其最终结果。</p>
    </header>
    <div v-if="isLoading" class="status-card"><div class="spinner"></div>正在加载历史活动...</div>
    <div v-if="error" class="status-card error-card">{{ error }}</div>
    <main v-if="!isLoading && pastEvents.length > 0" class="history-list">
      <div v-for="event in pastEvents" :key="event.event_id" class="card history-card">
        <div class="card-header">
          <h2>{{ event.event_name }}</h2>
          <span class="tag status-tag">已结束</span>
        </div>
        <div class="card-section">
          <p><strong>活动结束于:</strong> {{ formatDate(event.end_time) }}</p>
        </div>
        <div class="card-actions">
          <button @click="viewEventDetails(event.event_id)" class="btn btn-primary">查看我的结果</button>
        </div>
      </div>
    </main>
    <div v-if="!isLoading && pastEvents.length === 0" class="status-card info-card-bg">
      <h3>暂无已结束的活动记录</h3>
      <p>您尚未参与任何已结束的互选活动。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

const router = useRouter();
const pastEvents = ref([]);
const isLoading = ref(true);
const error = ref(null);

onMounted(async () => {
  isLoading.value = true;
  try {
    const response = await api.getStudentHistory();
    pastEvents.value = response.data;
  } catch (err) {
    error.value = "加载历史活动失败，请稍后重试。";
    console.error(err);
  } finally {
    isLoading.value = false;
  }
});

const viewEventDetails = (eventId) => {
  router.push({ name: 'StudentResultDetail', params: { id: eventId } });
};

const formatDate = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : 'N/A';
</script>

<style scoped>
/* (此处省略与教师历史页面完全相同的样式) */
</style>