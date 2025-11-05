<template>
  <div class="page-container">
    <header class="page-header">
      <h1>历史活动结果</h1>
      <p>在这里查看您参与过的所有已结束的互选活动及其最终分配结果。</p>
    </header>

    <div v-if="isLoading" class="status-card">
      <div class="spinner"></div>正在加载历史活动...
    </div>
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
          <button @click="viewEventDetails(event.event_id)" class="btn btn-primary">
            查看分配结果
          </button>
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
    const response = await api.getTeacherHistory();
    pastEvents.value = response.data;
  } catch (err) {
    error.value = "加载历史活动失败，请稍后重试。";
    console.error(err);
  } finally {
    isLoading.value = false;
  }
});

const viewEventDetails = (eventId) => {
  router.push({ name: 'TeacherHistoryDetail', params: { id: eventId } });
};

const formatDate = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : 'N/A';
</script>

<style scoped>
.page-container { padding: 2rem; background-color: #F9FAFB; min-height: 100vh; }
.page-header { margin-bottom: 2rem; }
.page-header h1 { font-size: 2em; font-weight: 700; }
.page-header p { color: #6B7280; }
.history-list { display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); }
.card { background: #FFFFFF; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; border-bottom: 1px solid #E5E7EB; }
.card-header h2 { font-size: 1.25em; margin: 0; }
.card-section { padding: 1.5rem; }
.card-actions { padding: 1.5rem; border-top: 1px solid #E5E7EB; text-align: right; }
.btn-primary { background-color: #3B82F6; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; font-weight: 600; }
.tag { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8em; font-weight: 600; background-color: #6B7280; color: white; }
.status-card { text-align: center; padding: 3rem; border-radius: 12px; background-color: #FFFFFF; max-width: 800px; margin: 2rem auto; display: flex; align-items: center; justify-content: center; gap: 1rem; font-size: 1.1em; font-weight: 500; }
.info-card-bg { background-color: #DBEAFE; color: #1E40AF; }
.error-card { background-color: #FEE2E2; color: #991B1B; }
.spinner { width: 24px; height: 24px; border: 3px solid currentColor; border-bottom-color: transparent; border-radius: 50%; display: inline-block; animation: rotation 1s linear infinite; }
@keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>