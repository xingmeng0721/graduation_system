<template>
  <div class="page-container">
    <!-- ... (页面标题, 加载状态, 错误提示保持不变) ... -->
    <div class="page-header">
      <h2>选择指导团队</h2>
      <el-tag v-if="activeEvent" type="primary" size="large">
        {{ activeEvent.event_name }} - 截止: {{ formatDate(activeEvent.end_time) }}
      </el-tag>
    </div>
    <div v-if="isLoading" class="loading-container" v-loading="isLoading"><p>正在加载数据...</p></div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <template v-if="!isLoading && activeEvent">
      <!-- 顶部志愿栏 -->
      <div class="preferences-cards">
         <el-card v-for="rank in choiceLimitRange" :key="rank"
          :class="['preference-card', { 'has-selection': preferences[rank] }]" shadow="hover">
          <div class="preference-card-header">
            <h4>第{{ ['一', '二', '三', '四', '五'][rank - 1] || rank }}志愿</h4>
            <el-tag :type="preferenceTagTypes[rank-1] || 'info'" size="small">志愿 {{ rank }}</el-tag>
          </div>
          <div class="preference-card-body">
            <div v-if="preferences[rank] && getTeamById(preferences[rank])" class="selected-team-info">
              <div class="selected-team-details">
                <span class="selected-project-title">{{ getTeamById(preferences[rank]).project_title || '未命名项目' }}</span>
                <span class="selected-captain-name">队长: {{ getTeamById(preferences[rank]).captain.stu_name }}</span>
              </div>
              <el-button type="danger" circle :icon="Close" @click="clearPreference(rank)" />
            </div>
            <div v-else class="empty-selection">
              <el-icon :size="40" color="#c0c4cc"><OfficeBuilding /></el-icon>
              <span class="empty-text">待选择</span>
            </div>
          </div>
        </el-card>
      </div>

      <el-divider />

      <!-- 团队列表区域 -->
      <div class="team-list-section">
        <div class="list-controls">
          <h3>可选团队列表 ({{ filteredTeams.length }})</h3>
          <div class="filters">
            <el-input v-model="searchQuery" placeholder="搜索项目或队长" clearable :prefix-icon="Search" style="width: 240px; margin-right: 16px;" />
            <el-checkbox v-model="showOnlyStudentPreferred" label="只看选择我的团队" size="large" border />
            <el-button type="primary" @click="savePreferences" style="margin-left: 16px;">
              <el-icon><Select /></el-icon>
              保存所有志愿
            </el-button>
          </div>
        </div>

        <!-- ✅ 竖向列表布局 -->
        <div class="team-vertical-list">
          <div v-for="team in filteredTeams" :key="team.group_id"
            :class="['team-list-item', { 'is-selected': team.my_preference_rank }]">
            <div class="item-content">
              <div class="item-main">
                <h4 class="item-project-title">{{ team.project_title || '未命名项目' }}</h4>
                <p class="item-project-desc">{{ team.project_description_short || '该团队尚未填写项目简介。' }}</p>
                <div class="item-meta">
                  <span><el-icon><User /></el-icon>队长: {{ team.captain.stu_name }}</span>
                  <span><el-icon><TrendCharts /></el-icon>成员: {{ team.member_count }}人</span>
                </div>
              </div>
              <div class="item-tags">
                <el-tag v-if="team.my_preference_rank" :type="preferenceTagTypes[team.my_preference_rank-1] || 'info'" effect="dark">
                  我的第{{ team.my_preference_rank }}志愿
                </el-tag>
                <el-tag v-if="team.student_preference_rank" type="success" effect="light">
                  学生第{{ team.student_preference_rank }}志愿
                </el-tag>
              </div>
            </div>
            <div class="item-actions">
              <!-- ✅ 调用新的弹窗 -->
              <el-button type="primary" @click="openPreferenceDialog(team)">
                查看详情 & 选择志愿
              </el-button>
            </div>
          </div>
        </div>
        <el-empty v-if="filteredTeams.length === 0" description="没有找到符合条件的团队" />
      </div>
    </template>

    <!-- 无活动状态 -->
    <el-card v-if="!isLoading && !activeEvent" class="no-activity-card" shadow="never">
      <el-empty description="当前没有正在进行的互选活动" />
    </el-card>

    <!-- ✅ 使用新的志愿选择弹窗 -->
    <TeacherPreferenceDialog
      v-if="activeEvent"
      v-model="isDetailModalVisible"
      :team="selectedTeam"
      :preferences="preferences"
      :choice-limit="activeEvent.teacher_choice_limit"
      @update:preferences="handlePreferencesUpdate"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading, Close, User, TrendCharts, Select, Search, OfficeBuilding } from '@element-plus/icons-vue';
import api from '../services/api';
// ✅ 引入新组件
import TeacherPreferenceDialog from '../components/TeacherPreferenceDialog.vue';

const teams = ref([]);
const activeEvent = ref(null);
const isLoading = ref(true);
const error = ref(null);
const preferences = reactive({});
const isDetailModalVisible = ref(false);
const selectedTeam = ref(null);
const showOnlyStudentPreferred = ref(false);
const searchQuery = ref('');
const preferenceTagTypes = ['danger', 'warning', 'success', 'primary', 'info'];

const choiceLimitRange = computed(() => {
  if (!activeEvent.value) return [];
  return Array.from({ length: activeEvent.value.teacher_choice_limit || 5 }, (_, i) => i + 1);
});

const sortedTeams = computed(() => {
  return [...teams.value].sort((a, b) => {
    const rankA = a.my_preference_rank || 99;
    const rankB = b.my_preference_rank || 99;
    const studentPrefA = a.student_preference_rank || 99;
    const studentPrefB = b.student_preference_rank || 99;
    if (rankA !== 99 || rankB !== 99) return rankA - rankB;
    if (studentPrefA !== 99 || studentPrefB !== 99) return studentPrefA - studentPrefB;
    return a.group_id - b.group_id;
  });
});

const filteredTeams = computed(() => {
  let tempTeams = sortedTeams.value;
  if (showOnlyStudentPreferred.value) tempTeams = tempTeams.filter(team => team.student_preference_rank);
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    tempTeams = tempTeams.filter(team =>
      (team.project_title?.toLowerCase().includes(query)) ||
      (team.captain.stu_name?.toLowerCase().includes(query))
    );
  }
  return tempTeams;
});

const fetchDashboard = async () => {
  isLoading.value = true; error.value = null;
  try {
    const response = await api.getTeacherDashboard();
    teams.value = response.data.teams;
    activeEvent.value = response.data.active_event;
    if (activeEvent.value) {
      choiceLimitRange.value.forEach(rank => {
        preferences[rank] = response.data.preferences[rank] || null;
      });
    }
  } catch (err) {
    error.value = '加载数据失败，请刷新页面重试。';
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchDashboard);

// ✅ 修改：打开新的弹窗
const openPreferenceDialog = (team) => {
  selectedTeam.value = team;
  isDetailModalVisible.value = true;
};

const savePreferences = async () => {
  try {
    await ElMessageBox.confirm('确定要保存当前的志愿选择吗？', '提示', { type: 'info' });
    const prefsToSubmit = {};
    Object.keys(preferences).forEach(rank => { if (preferences[rank]) prefsToSubmit[rank] = preferences[rank]; });
    await api.setTeacherPreferences(prefsToSubmit);
    ElMessage.success('志愿保存成功！');
    await fetchDashboard();
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(`保存失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const clearPreference = (rank) => {
  preferences[rank] = null;
};

// ✅ 新增：处理子组件传回的更新，实现即时同步
const handlePreferencesUpdate = (newPreferences) => {
  Object.assign(preferences, newPreferences);
  // 手动更新列表中的 my_preference_rank 以实现即时刷新
  teams.value.forEach(team => {
      const rank = Object.keys(newPreferences).find(key => newPreferences[key] === team.group_id);
      team.my_preference_rank = rank ? parseInt(rank) : null;
  });
};

const getTeamById = (teamId) => teams.value.find(t => t.group_id === teamId);
const formatDate = (dateString) => dateString ? new Date(dateString).toLocaleString('zh-CN') : 'N/A';
</script>


<style scoped>
.team-vertical-list {
  display: flex;
  flex-direction: column;
  gap: 10px; /* 卡片之间几乎无间距 */
}

.team-list-item {
  display: flex;
  justify-content: space-between;
  align-items: stretch; /* 让左右内容对齐 */
  padding: 6px 10px; /* 极小内边距 */
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  background-color: #fff;
  transition: all 0.15s;
  min-height: 56px;
}

.team-list-item:hover {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-7);
}

.team-list-item.is-selected {
  border-left: 3px solid var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.item-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center; /* 垂直居中 */
  gap: 6px;
  overflow: hidden;
}

.item-main {
  flex: 1;
  min-width: 0;
  line-height: 1.3;
}

.item-project-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--el-text-color-primary);
}

.item-project-desc {
  font-size: 14px;
  color: #606266;
  margin: 2px 0 0 0;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  gap: 10px;
  font-size: 11.5px;
  color: #909399;
  margin-top: 2px;
}

.item-meta span {
  display: flex;
  align-items: center;
  gap: 3px;
}

.item-tags {
  display: flex;
  flex-direction: column;
  justify-content: center; /* 垂直居中标签 */
  align-items: center;
  gap: 4px;
  min-width: 90px;
}

.item-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding-left: 6px;
}

/* 页面整体布局 */
.page-container {
  padding: 12px 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.preferences-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.preference-card {
  border-radius: 6px;
  padding: 6px 10px;
}

.preference-card-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.preference-card-body {
  min-height: 60px;
  padding-top: 4px;
}

.list-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.list-controls h3 {
  margin: 0;
  font-size: 16px;
}

.filters {
  display: flex;
  align-items: center;
}

.loading-container {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.no-activity-card {
  text-align: center;
}

/* 选中卡片信息栏 */
.selected-team-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.selected-team-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.selected-project-title {
  font-size: 13px;
  font-weight: 600;
}

.selected-captain-name {
  font-size: 12px;
  color: #909399;
}

.empty-selection {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #c0c4cc;
}

.empty-text {
  font-size: 13px;
  font-weight: 500;
}
</style>
