<template>
  <div class="page-container">
    <div v-if="isLoading" class="status-card"><div class="spinner"></div>正在加载活动结果...</div>
    <div v-if="error" class="status-card error-card">{{ error }}</div>

    <div v-if="resultData">
      <header class="page-header">
        <h1>"{{ resultData.event_name }}" - 分配结果</h1>
        <button @click="$router.back()" class="btn btn-secondary">返回历史列表</button>
      </header>

      <div class="results-container">
        <!-- 左侧：最终指导的小组 -->
        <div class="main-panel">
          <h2>最终指导的小组</h2>
          <div v-if="resultData.advised_groups.length > 0">
            <div v-for="group in resultData.advised_groups" :key="group.group_id" class="card group-card">
              <div class="card-header">
                <h3>{{ group.group_name }}</h3>
              </div>
              <div class="card-section">
                <h4>项目信息</h4>
                <p><strong>标题:</strong> {{ group.project_title || '未填写' }}</p>
                <p><strong>简介:</strong> {{ group.project_description || '未填写' }}</p>
              </div>
              <div class="card-section">
                <h4>小组成员 ({{ group.member_count }})</h4>
                <ul class="member-list">
                  <li v-for="member in group.members" :key="member.stu_id">
                    {{ member.stu_name }} ({{ member.stu_no }})
                    <span v-if="member.is_captain" class="tag member-tag">队长</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <p v-else>您在该活动中未指导任何小组。</p>
        </div>

        <!-- 右侧：我当时的志愿 -->
        <aside class="sidebar-panel">
          <div class="card">
            <h3>我当时的志愿</h3>
            <ul v-if="sortedPreferences.length > 0" class="preference-list">
              <li v-for="rank in sortedPreferences" :key="rank">
                <span>第{{ rank }}志愿:</span>
                <strong>{{ getGroupName(resultData.preferences[rank]) }}</strong>
              </li>
            </ul>
            <p v-else>您在该活动中未提交任何志愿。</p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import api from '../services/api';

const route = useRoute();
const isLoading = ref(true);
const error = ref(null);
const resultData = ref(null);

onMounted(async () => {
  const eventId = route.params.id;
  if (!eventId) {
    error.value = "未提供活动ID。";
    isLoading.value = false;
    return;
  }
  try {
    const response = await api.getTeacherHistoryDetail(eventId);
    resultData.value = response.data;
  } catch (err) {
    error.value = "无法加载活动结果。";
    console.error(err);
  } finally {
    isLoading.value = false;
  }
});

const sortedPreferences = computed(() => {
  if (!resultData.value?.preferences) return [];
  return Object.keys(resultData.value.preferences).sort((a, b) => parseInt(a) - parseInt(b));
});

const getGroupName = (groupId) => {
  if (!groupId || !resultData.value?.all_teams_in_event) return '未知小组';
  const team = resultData.value.all_teams_in_event.find(t => t.group_id === groupId);
  return team ? team.group_name : '小组已不存在';
};
</script>

<style scoped>
.page-container { padding: 2rem; background-color: #F9FAFB; min-height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid #E5E7EB; padding-bottom: 1rem; }
.page-header h1 { font-size: 1.8em; font-weight: 700; margin: 0; }
.results-container { display: grid; grid-template-columns: 3fr 1fr; gap: 2rem; }
.card { background: #FFFFFF; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); }
.card-header { padding: 1.5rem; border-bottom: 1px solid #E5E7EB; }
.card-header h3 { font-size: 1.25em; margin: 0; }
.card-section { padding: 1.5rem; }
.card-section h4 { font-size: 1.1em; margin-top: 0; margin-bottom: 1rem; }
.card-section p { margin: 0 0 0.5rem; }
.member-list, .preference-list { list-style: none; padding: 0; }
.member-list li, .preference-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #E5E7EB; }
.member-list li:last-child, .preference-list li:last-child { border-bottom: none; }
.tag { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75em; font-weight: 600; }
.member-tag { background-color: #E5E7EB; color: #4B5563; }
.btn { padding: 0.75rem 1.5rem; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; }
.btn-secondary { background-color: #6c757d; color: white; }
.status-card { text-align: center; padding: 3rem; border-radius: 12px; background-color: #FFFFFF; display: flex; align-items: center; justify-content: center; gap: 1rem; }
.error-card { background-color: #FEE2E2; color: #991B1B; }
.spinner { width: 24px; height: 24px; border: 3px solid currentColor; border-bottom-color: transparent; border-radius: 50%; display: inline-block; animation: rotation 1s linear infinite; }
@keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>