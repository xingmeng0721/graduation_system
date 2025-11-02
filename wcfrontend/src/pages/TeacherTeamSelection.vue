<template>
  <div class="page-container">
    <header class="page-header">
      <h1>选择指导团队</h1>
      <p v-if="activeEvent" class="event-info">
        <i class="icon clock"></i>
        当前活动: <strong>{{ activeEvent.event_name }}</strong> (选择截止: {{ formatDate(activeEvent.end_time) }})
      </p>
    </header>

    <div v-if="isLoading" class="status-card"><div class="spinner"></div>正在加载团队列表...</div>
    <div v-if="error" class="status-card error-card">{{ error }}</div>

    <main v-if="!isLoading && teams.length > 0" class="teams-grid">
      <div v-for="team in teams" :key="team.group_id" class="card team-card">
        <div class="card-header">
          <h2>{{ team.group_name }}</h2>
          <span v-if="team.preference_rank <= 3" :class="getPreferenceTagClass(team.preference_rank)">
            {{ getPreferenceText(team.preference_rank) }}
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

        <div class="card-actions">
          <button @click="handleSelectTeam(team)" class="btn btn-primary" :disabled="team.advisor && team.advisor.teacher_id !== currentUserTeacherId">
            <span v-if="!team.advisor">选择此团队</span>
            <span v-else-if="team.advisor.teacher_id === currentUserTeacherId">✔ 已选择</span>
            <span v-else>已被 {{ team.advisor.teacher_name }} 选择</span>
          </button>
        </div>
      </div>
    </main>

    <div v-if="!isLoading && teams.length === 0 && activeEvent" class="status-card info-card-bg">
      <h3>当前活动暂无团队</h3>
      <p>目前还没有学生创建团队，请稍后再来查看。</p>
    </div>

    <div v-if="!isLoading && !activeEvent" class="status-card info-card-bg">
      <h3>当前没有正在进行的互选活动</h3>
      <p>请耐心等待管理员开启新的活动。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';
import { jwtDecode } from 'jwt-decode';

const teams = ref([]);
const activeEvent = ref(null);
const isLoading = ref(true);
const error = ref(null);
const currentUserTeacherId = ref(null);

const fetchTeams = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const response = await api.getTeamsForTeacher();
    teams.value = response.data.teams;
    activeEvent.value = response.data.active_event;
  } catch (err) {
    error.value = "加载团队列表失败，请刷新页面重试。";
  } finally {
    isLoading.value = false;
  }
};

const decodeToken = () => {
  const token = localStorage.getItem('teacherAccessToken');
  if (token) {
    try {
      const decoded = jwtDecode(token);
      currentUserTeacherId.value = decoded.user_id;
    } catch (e) {
      console.error("Token decode error:", e);
    }
  }
};

onMounted(() => {
  decodeToken();
  fetchTeams();
});

const handleSelectTeam = async (team) => {
  if (team.advisor && team.advisor.teacher_id === currentUserTeacherId.value) {
    alert("您已经选择了该团队。");
    return;
  }
  if (!confirm(`您确定要选择“${team.group_name}”作为您的指导团队吗？`)) {
    return;
  }
  try {
    const response = await api.teacherSelectTeam(team.group_id);
    alert(response.data.message);
    await fetchTeams();
  } catch (err) {
    alert(`操作失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const getPreferenceText = (rank) => ({ 1: '第一志愿', 2: '第二志愿', 3: '第三志愿' }[rank] || '');
const getPreferenceTagClass = (rank) => `tag preference-tag rank-${rank}`;

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};
</script>

<style scoped>
/* 这里复用了之前版本的美化样式，保持风格统一 */
.icon {
  font-family: 'icons' !important; speak: never; font-style: normal; font-weight: normal; font-variant: normal;
  text-transform: none; line-height: 1; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
  margin-right: 8px;
}
.icon.clock::before { content: '🕒'; }

.page-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #1F2937;
  background-color: #F9FAFB;
  min-height: 100%;
}

.page-header { margin-bottom: 2.5rem; }
.page-header h1 { font-size: 2.25em; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.page-header .event-info { color: #6B7280; font-size: 1em; display: flex; align-items: center; }

.teams-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 2rem; }

.card {
  background: #FFFFFF; border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.07);
  transition: all 0.3s ease; display: flex; flex-direction: column;
}
.card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -4px rgba(0, 0, 0, 0.07);
  transform: translateY(-4px);
}

.card-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 1.5rem; border-bottom: 1px solid #E5E7EB; }
.card-header h2 { margin: 0; font-size: 1.5em; color: #3B82F6; font-weight: 700; }

.card-section { padding: 1.5rem; }
.card-section h3 { font-size: 1.1em; margin-bottom: 1rem; font-weight: 600; }
.project-description {
  line-height: 1.6; color: #6B7280;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}

.member-list { list-style: none; padding: 0; max-height: 150px; overflow-y: auto; }
.member-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #E5E7EB; }
.member-list li:last-child { border-bottom: none; }
.member-info { display: flex; flex-direction: column; }
.member-name { font-weight: 600; }
.member-id { font-size: 0.85em; color: #6B7280; }

.tag { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.member-tag { background-color: #E5E7EB; color: #4B5563; }
.preference-tag { color: white; }
.rank-1 { background-color: #EF4444; }
.rank-2 { background-color: #F59E0B; }
.rank-3 { background-color: #10B981; }

.card-actions { margin-top: auto; padding: 1.5rem; border-top: 1px solid #E5E7EB; }
.btn { width: 100%; padding: 0.75rem 1.25rem; border: 1px solid transparent; border-radius: 8px; cursor: pointer; font-size: 0.95em; font-weight: 600; transition: all 0.2s ease; }
.btn:disabled { cursor: not-allowed; }
.btn-primary { background-color: #3B82F6; color: white; }
.btn-primary:hover:not(:disabled) { background-color: #2563EB; }
.btn-primary:disabled { background-color: #60A5FA; color: #EFF6FF; }

.status-card {
  text-align: center; padding: 3rem; border-radius: 12px;
  background-color: #FFFFFF; max-width: 800px; margin: 2rem auto;
  display: flex; align-items: center; justify-content: center; gap: 1rem;
  font-size: 1.1em; font-weight: 500;
}
.info-card-bg { background-color: #DBEAFE; color: #1E40AF; }
.error-card { background-color: #FEE2E2; color: #991B1B; }

.spinner { width: 24px; height: 24px; border: 3px solid currentColor; border-bottom-color: transparent; border-radius: 50%; display: inline-block; box-sizing: border-box; animation: rotation 1s linear infinite; }
@keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>