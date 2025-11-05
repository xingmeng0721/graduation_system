<template>
  <div class="page-container">
    <header class="page-header">
      <h1>选择指导团队</h1>
      <p v-if="activeEvent" class="event-info">
        <i class="icon clock"></i>
        当前活动: <strong>{{ activeEvent.event_name }}</strong> (选择截止: {{ formatDate(activeEvent.end_time) }})
      </p>
    </header>

    <div v-if="isLoading" class="status-card"><div class="spinner"></div>正在加载数据...</div>
    <div v-if="error" class="status-card error-card">{{ error }}</div>

    <main v-if="!isLoading && activeEvent">
      <!-- 志愿选择核心区域 -->
      <div class="selection-panel">
        <h3>我的志愿小组 (最多可选择 {{ activeEvent.teacher_choice_limit }} 个)</h3>
        <div class="form-grid">
          <div class="form-group" v-for="rank in choiceLimitRange" :key="rank">
            <label>{{ getPreferenceText(rank) }}</label>
            <select v-model="preferences[rank]">
              <option :value="null">-- 清除选择 --</option>
              <option v-for="team in teams" :key="team.group_id" :value="team.group_id" :disabled="isTeamSelectedInOtherPreferences(team.group_id, rank)">
                {{ team.group_name }}
              </option>
            </select>
          </div>
        </div>
        <div class="actions-bar">
          <button @click="savePreferences" class="btn btn-primary">保存我的志愿</button>
        </div>
      </div>

      <!-- 团队信息参考列表 -->
      <div class="teams-grid">
        <div v-for="team in teams" :key="team.group_id" :class="['card', 'team-card', { 'is-selected': getRankForTeam(team.group_id) }]">
          <div class="card-header">
            <h2>{{ team.group_name }}</h2>
            <span v-if="getRankForTeam(team.group_id)" :class="getPreferenceTagClass(getRankForTeam(team.group_id))">
              {{ getPreferenceText(getRankForTeam(team.group_id)) }}
            </span>
            <span v-else-if="team.my_preference_rank" class="tag preference-tag-faded">
              学生志愿
            </span>
          </div>
          <section class="card-section">
            <h3>{{ team.project_title || '未填写项目标题' }}</h3>
            <p class="project-description">{{ team.project_description || '该团队尚未填写项目简介。' }}</p>
          </section>
          <section class="card-section">
            <h3>团队成员 ({{ team.member_count }})</h3>
            <ul class="member-list">
              <li v-for="member in team.members" :key="member.stu_id">
                <div class="member-info">
                  <span class="member-name">{{ member.stu_name }}</span>
                  <span class="member-id">{{ member.stu_no }}</span>
                </div>
                <span v-if="member.is_captain" class="tag member-tag">队长</span>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </main>

    <div v-if="!isLoading && !activeEvent" class="status-card info-card-bg">
      <h3>当前没有正在进行的互选活动</h3>
      <p>请耐心等待管理员开启新的活动。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue';
import api from '../services/api';

const teams = ref([]);
const activeEvent = ref(null);
const isLoading = ref(true);
const error = ref(null);
const preferences = reactive({});

const choiceLimitRange = computed(() => {
  if (!activeEvent.value) return [];
  const limit = activeEvent.value.teacher_choice_limit || 5;
  return Array.from({ length: limit }, (_, i) => i + 1);
});

const fetchDashboard = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const response = await api.getTeacherDashboard();
    teams.value = response.data.teams;
    activeEvent.value = response.data.active_event;
    // 使用后端返回的已有志愿填充响应式对象
    Object.assign(preferences, response.data.preferences);
  } catch (err) {
    error.value = "加载数据失败，请刷新页面重试。";
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchDashboard);

const savePreferences = async () => {
  if (!confirm("确定要保存当前的志愿选择吗？这将覆盖您之前的选择。")) return;

  try {
    // 清理数据，只提交非空的志愿
    const preferencesToSubmit = {};
    for (const rank in preferences) {
      if (preferences[rank]) {
        preferencesToSubmit[rank] = preferences[rank];
      }
    }
    await api.setTeacherPreferences(preferencesToSubmit);
    alert("志愿保存成功！");
    await fetchDashboard(); // 重新加载数据以确认
  } catch (err) {
    alert(`保存失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const isTeamSelectedInOtherPreferences = (teamId, currentRank) => {
  if (!teamId) return false;
  for (const rank in preferences) {
    if (parseInt(rank) !== currentRank && preferences[rank] === teamId) {
      return true;
    }
  }
  return false;
};

const getRankForTeam = (teamId) => {
  for (const rank in preferences) {
    if (preferences[rank] === teamId) {
      return parseInt(rank);
    }
  }
  return null;
};

const getPreferenceText = (rank) => {
  const numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
  return `第${numbers[rank-1] || rank}志愿`;
};

const getPreferenceTagClass = (rank) => `tag preference-tag rank-${rank}`;

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};
</script>

<style scoped>
.icon { font-family: 'icons' !important; speak: never; font-style: normal; font-weight: normal; font-variant: normal; text-transform: none; line-height: 1; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; margin-right: 8px; }
.icon.clock::before { content: '🕒'; }
.page-container { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color: #1F2937; background-color: #F9FAFB; min-height: 100%; padding: 2rem; }
.page-header { margin-bottom: 2.5rem; }
.page-header h1 { font-size: 2.25em; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.page-header .event-info { color: #6B7280; font-size: 1em; display: flex; align-items: center; }

/* 新增的志愿选择面板 */
.selection-panel {
  background: #fff;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  margin-bottom: 2.5rem;
}
.selection-panel h3 { margin-top: 0; font-size: 1.5em; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; }
.form-group label { display: block; margin-bottom: 8px; font-weight: 600; }
.form-group select { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 8px; }
.actions-bar { margin-top: 2rem; }

.teams-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 2rem; }

.card { background: #FFFFFF; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.07); transition: all 0.3s ease; display: flex; flex-direction: column; }
.card.is-selected { border: 2px solid #3B82F6; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.2), 0 4px 6px -4px rgba(59, 130, 246, 0.2); }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 1.5rem; border-bottom: 1px solid #E5E7EB; }
.card-header h2 { margin: 0; font-size: 1.5em; color: #3B82F6; font-weight: 700; }

.card-section { padding: 1.5rem; }
.card-section h3 { font-size: 1.1em; margin-bottom: 1rem; font-weight: 600; }
.project-description { line-height: 1.6; color: #6B7280; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

.member-list { list-style: none; padding: 0; max-height: 150px; overflow-y: auto; }
.member-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #E5E7EB; }
.member-list li:last-child { border-bottom: none; }
.member-info { display: flex; flex-direction: column; }
.member-name { font-weight: 600; }
.member-id { font-size: 0.85em; color: #6B7280; }

.tag { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.member-tag { background-color: #E5E7EB; color: #4B5563; }
.preference-tag { color: white; }
.preference-tag-faded { background-color: #D1D5DB; color: #4B5563; }
.rank-1 { background-color: #EF4444; }
.rank-2 { background-color: #F59E0B; }
.rank-3 { background-color: #10B981; }
/* 更多志愿颜色 */
.rank-4 { background-color: #6366F1; }
.rank-5 { background-color: #8B5CF6; }

.btn { padding: 0.75rem 1.25rem; border: 1px solid transparent; border-radius: 8px; cursor: pointer; font-size: 0.95em; font-weight: 600; transition: all 0.2s ease; }
.btn-primary { background-color: #3B82F6; color: white; }
.btn-primary:hover:not(:disabled) { background-color: #2563EB; }

.status-card { text-align: center; padding: 3rem; border-radius: 12px; background-color: #FFFFFF; max-width: 800px; margin: 2rem auto; display: flex; align-items: center; justify-content: center; gap: 1rem; font-size: 1.1em; font-weight: 500; }
.info-card-bg { background-color: #DBEAFE; color: #1E40AF; }
.error-card { background-color: #FEE2E2; color: #991B1B; }

.spinner { width: 24px; height: 24px; border: 3px solid currentColor; border-bottom-color: transparent; border-radius: 50%; display: inline-block; box-sizing: border-box; animation: rotation 1s linear infinite; }
@keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>