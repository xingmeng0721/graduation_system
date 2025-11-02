<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>我的毕业设计团队</h1>
      <p v-if="dashboard.has_active_event">
        当前活动: <strong>{{ dashboard.active_event_info.event_name }}</strong> (截止: {{ formatDate(dashboard.active_event_info.end_time) }})
      </p>
    </div>

    <!-- 全局加载与错误状态 -->
    <div v-if="loading" class="status-card">正在加载信息...</div>
    <div v-if="error" class="status-card error">{{ error }}</div>

    <!-- 场景一：已加入团队 -->
    <div v-if="dashboard.my_team_info && !loading" class="team-container">
      <!-- 左侧：团队信息 -->
      <div class="info-card">
        <div class="card-header">
          <h2>{{ dashboard.my_team_info.group_name }}</h2>
          <span v-if="dashboard.is_captain" class="captain-flag">我是队长</span>
        </div>

        <div class="card-section">
          <h3>项目信息</h3>
          <h4>{{ dashboard.my_team_info.project_title || '尚未填写项目标题' }}</h4>
          <p>{{ dashboard.my_team_info.project_description || '尚未填写项目简介' }}</p>
          <button v-if="dashboard.is_captain" @click="openProjectEditModal" class="btn-edit-small">
            编辑项目
          </button>
        </div>

        <div class="card-section">
          <h3>志愿导师</h3>
          <ul class="advisor-list">
            <li><strong>第一志愿:</strong> {{ dashboard.my_team_info.preferred_advisor_1?.teacher_name || '未选择' }}</li>
            <li><strong>第二志愿:</strong> {{ dashboard.my_team_info.preferred_advisor_2?.teacher_name || '未选择' }}</li>
            <li><strong>第三志愿:</strong> {{ dashboard.my_team_info.preferred_advisor_3?.teacher_name || '未选择' }}</li>
          </ul>
           <button v-if="dashboard.is_captain" @click="openAdvisorModal" class="btn-edit-small">
            选择/修改导师
          </button>
        </div>

        <div class="card-section final-advisor-section">
          <h3>最终指导老师</h3>
          <p class="final-advisor">{{ dashboard.my_team_info.advisor?.teacher_name || '待管理员分配' }}</p>
        </div>
      </div>

      <!-- 右侧：成员与操作 -->
      <div class="actions-card">
        <h3>团队成员 ({{ dashboard.my_team_info.member_count }})</h3>
        <ul class="member-list">
          <li v-for="member in dashboard.my_team_info.members" :key="member.stu_id">
            <span>{{ member.stu_name }} ({{ member.stu_no }})</span>
            <div>
              <span v-if="member.is_captain" class="captain-badge">队长</span>
              <button v-if="dashboard.is_captain && !member.is_captain" @click="handleRemoveMember(member)" class="btn-remove-small" title="移除该成员">
                移除
              </button>
            </div>
          </li>
        </ul>
        <div class="card-actions">
           <button v-if="dashboard.is_captain" @click="openInviteModal" class="btn btn-primary">
            添加新成员
          </button>
          <button v-if="dashboard.is_captain" @click="handleDisbandTeam" class="btn btn-danger">
            解散团队
          </button>
          <button v-else @click="handleLeaveTeam" class="btn btn-danger">
            退出团队
          </button>
        </div>
      </div>
    </div>

    <!-- 场景二：未加入团队但有活动 -->
    <div v-if="!dashboard.my_team_info && dashboard.has_active_event && !loading" class="no-team-container">
      <div class="action-card">
        <h3>创建我的团队</h3>
        <p>迈出第一步，成为团队的领导者！</p>
        <form @submit.prevent="handleCreateTeam">
          <div class="form-group"><label>团队名称</label><input v-model="newTeam.group_name" required placeholder="一个独特且响亮的名称"></div>
          <button type="submit" class="btn btn-primary full-width">确认创建</button>
        </form>
      </div>
      <div class="action-card">
        <h3>或加入现有团队</h3>
        <p>寻找志同道合的伙伴，加入他们吧！</p>
        <button @click="openAllTeamsModal" class="btn btn-secondary full-width">查找所有团队</button>
      </div>
    </div>

    <!-- 场景三：无进行中的活动 -->
    <div v-if="!dashboard.has_active_event && !loading" class="status-card">
        <h3>当前没有正在进行的互选活动</h3>
        <p>请耐心等待管理员开启新的活动，并留意通知。</p>
    </div>

    <!-- 弹窗区 -->

    <!-- 弹窗1：仅用于编辑项目信息 -->
    <div v-if="isProjectModalVisible" class="modal-overlay" @click.self="isProjectModalVisible = false">
      <div class="modal-content">
        <h2>编辑项目信息</h2>
        <form @submit.prevent="handleUpdateProjectInfo">
            <div class="form-group">
                <label>项目标题</label>
                <input v-model="editTeam.project_title" placeholder="为你们的项目起个名字">
            </div>
            <div class="form-group">
                <label>项目简介</label>
                <textarea v-model="editTeam.project_description" rows="4" placeholder="详细描述你们的项目目标和内容"></textarea>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" @click="isProjectModalVisible = false">取消</button>
                <button type="submit" class="btn btn-primary">保存项目信息</button>
            </div>
        </form>
      </div>
    </div>

    <!-- 弹窗2：选择导师 -->
    <div v-if="isAdvisorModalVisible" class="modal-overlay" @click.self="isAdvisorModalVisible = false">
      <div class="modal-content large">
        <h2>选择志愿导师</h2>
        <div v-if="modalLoading" class="loading-state">加载导师列表中...</div>
        <div v-else class="advisor-selection-container">
          <!-- 左侧：已选志愿 -->
          <div class="preferences-summary">
            <h4>我的志愿</h4>
            <div class="preference-item">
              <span>第一志愿</span>
              <strong>{{ getAdvisorName(preferences.preferred_advisor_1) || '未选择' }}</strong>
            </div>
            <div class="preference-item">
              <span>第二志愿</span>
              <strong>{{ getAdvisorName(preferences.preferred_advisor_2) || '未选择' }}</strong>
            </div>
            <div class="preference-item">
              <span>第三志愿</span>
              <strong>{{ getAdvisorName(preferences.preferred_advisor_3) || '未选择' }}</strong>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" @click="isAdvisorModalVisible = false">取消</button>
              <button type="button" class="btn btn-primary" @click="handleUpdateAdvisors">保存选择</button>
            </div>
          </div>
          <!-- 右侧：可选导师列表 -->
          <div class="advisor-list-panel">
            <h4>可选导师列表</h4>
            <ul class="modal-list scrollable">
              <li v-for="advisor in availableAdvisors" :key="advisor.teacher_id" class="advisor-item">
                <span>{{ advisor.teacher_name }}</span>
                <div class="advisor-item-actions">
                  <button class="btn-link" @click="showAdvisorDetails(advisor)">查看详情</button>
                  <button class-="btn btn-secondary btn-sm" @click="setPreference(1, advisor.teacher_id)" :disabled="isAdvisorSelected(advisor.teacher_id)">设为一志愿</button>
                  <button class-="btn btn-secondary btn-sm" @click="setPreference(2, advisor.teacher_id)" :disabled="isAdvisorSelected(advisor.teacher_id)">设为二志愿</button>
                  <button class-="btn btn-secondary btn-sm" @click="setPreference(3, advisor.teacher_id)" :disabled="isAdvisorSelected(advisor.teacher_id)">设为三志愿</button>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div v-if="advisorDetail" class="modal-overlay" @click.self="advisorDetail = null">
      <div class="modal-content">
        <h2>{{ advisorDetail.teacher_name }} - 导师详情</h2>
        <div class="advisor-detail-card">
          <p><strong>研究方向:</strong> {{ advisorDetail.research_direction || '未填写' }}</p>
          <p><strong>联系邮箱:</strong> {{ advisorDetail.email || '未填写' }}</p>
          <p><strong>联系电话:</strong> {{ advisorDetail.phone || '未填写' }}</p>
          <p><strong>个人简介:</strong></p>
          <div class="introduction-box">{{ advisorDetail.introduction || '未填写' }}</div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary" @click="advisorDetail = null">关闭</button>
        </div>
      </div>
    </div>


    <!-- 弹窗3：添加新成员 -->
    <div v-if="isInviteModalVisible" class="modal-overlay" @click.self="isInviteModalVisible = false">
        <div class="modal-content">
            <h2>添加新成员</h2>
            <div class="form-group">
                <input type="text" v-model="teammateSearchQuery" placeholder="按姓名或专业搜索..." class="search-input">
            </div>
            <div v-if="modalLoading" class="loading-state small">加载中...</div>
            <ul v-else-if="filteredTeammates.length > 0" class="modal-list scrollable">
                <li v-for="student in filteredTeammates" :key="student.stu_id">
                    <span>{{ student.stu_name }} ({{ student.major_name }})</span>
                    <button class="btn btn-primary btn-sm" @click="handleAddMember(student)">添加</button>
                </li>
            </ul>
            <p v-else>没有找到匹配的学生或已无更多可添加的同学。</p>
        </div>
    </div>

    <!-- 弹窗4：浏览并加入团队 -->
    <div v-if="isAllTeamsModalVisible" class="modal-overlay" @click.self="isAllTeamsModalVisible = false">
        <div class="modal-content">
            <h2>加入一个团队</h2>
            <div v-if="modalLoading" class="loading-state small">加载中...</div>
            <ul v-else-if="allTeams.length > 0" class="modal-list scrollable">
                <li v-for="team in allTeams" :key="team.group_id" class="team-item">
                    <div class="team-item-info">
                        <h4>{{ team.group_name }}</h4>
                        <p>队长: {{ team.captain.stu_name }} | 成员: {{ team.member_count }}人</p>
                    </div>
                    <button class="btn btn-secondary btn-sm" @click="handleJoinTeam(team.group_id)">申请加入</button>
                </li>
            </ul>
            <p v-else>当前活动还没有人创建团队。</p>
        </div>
    </div>

  </div>
</template>

<script setup>
import {ref, onMounted, reactive, computed} from 'vue';
import api from '../services/api';

const loading = ref(true);
const error = ref(null);
const dashboard = ref({has_active_event: false, active_event_info: null, my_team_info: null, is_captain: false});

const modalLoading = ref(false);
const isProjectModalVisible = ref(false);
const isAdvisorModalVisible = ref(false);
const isInviteModalVisible = ref(false);
const isAllTeamsModalVisible = ref(false);

const newTeam = ref({group_name: ''});
const editTeam = reactive({project_title: '', project_description: ''});
const preferences = reactive({preferred_advisor_1: null, preferred_advisor_2: null, preferred_advisor_3: null});
const advisorDetail = ref(null);

const availableAdvisors = ref([]);
const availableTeammates = ref([]);
const allTeams = ref([]);
const teammateSearchQuery = ref('');

const isAdvisorSelected = (teacherId) => {
  return Object.values(preferences).includes(teacherId);
};

const getAdvisorName = (teacherId) => {
  if (!teacherId) return null;
  const advisor = availableAdvisors.value.find(a => a.teacher_id === teacherId);
  return advisor ? advisor.teacher_name : '未知导师';
};

const setPreference = (level, teacherId) => {
  // 如果要设置的导师已在其他志愿中，先清除那个志愿
  for (const key in preferences) {
    if (preferences[key] === teacherId) {
      preferences[key] = null;
    }
  }
  preferences[`preferred_advisor_${level}`] = teacherId;
};

const showAdvisorDetails = (advisor) => {
  advisorDetail.value = advisor;
};


const filteredTeammates = computed(() => {
  if (!teammateSearchQuery.value) return availableTeammates.value;
  const query = teammateSearchQuery.value.toLowerCase();
  return availableTeammates.value.filter(s => s.stu_name.toLowerCase().includes(query) || s.major_name.toLowerCase().includes(query));
});

const fetchDashboardData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.getDashboard();
    dashboard.value = response.data;
  } catch (err) {
    error.value = "加载信息失败，请刷新页面重试。";
    console.error("Dashboard fetch error:", err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchDashboardData);

const openProjectEditModal = () => {
  const teamInfo = dashboard.value.my_team_info;
  editTeam.project_title = teamInfo.project_title || '';
  editTeam.project_description = teamInfo.project_description || '';
  isProjectModalVisible.value = true;
};

const openAdvisorModal = async () => {
  const teamInfo = dashboard.value.my_team_info;
  preferences.preferred_advisor_1 = teamInfo.preferred_advisor_1?.teacher_id || null;
  preferences.preferred_advisor_2 = teamInfo.preferred_advisor_2?.teacher_id || null;
  preferences.preferred_advisor_3 = teamInfo.preferred_advisor_3?.teacher_id || null;

  isAdvisorModalVisible.value = true;
  modalLoading.value = true;
  try {
    if (availableAdvisors.value.length === 0) {
      const res = await api.getAvailableAdvisors();
      availableAdvisors.value = res.data;
    }
  } catch (err) {
    alert('获取导师列表失败');
    isAdvisorModalVisible.value = false;
  } finally {
    modalLoading.value = false;
  }
};

const fetchAvailableTeammates = async () => {
  modalLoading.value = true;
  teammateSearchQuery.value = '';
  try {
    const res = await api.getAvailableTeammates();
    availableTeammates.value = res.data;
  } catch (err) {
    alert('获取可添加成员列表失败');
    isInviteModalVisible.value = false; // 如果失败则关闭弹窗
  } finally {
    modalLoading.value = false;
  }
};

const openInviteModal = () => {
  isInviteModalVisible.value = true;
  fetchAvailableTeammates();
};


const openAllTeamsModal = async () => {
  isAllTeamsModalVisible.value = true;
  modalLoading.value = true;
  try {
    const res = await api.getAllTeamsInActiveEvent();
    allTeams.value = res.data;
  } catch (err) {
    alert('获取团队列表失败');
  } finally {
    modalLoading.value = false;
  }
};

const handleCreateTeam = async () => {
  if (!newTeam.value.group_name.trim()) return alert("团队名称不能为空！");
  try {
    await api.createTeam(newTeam.value);
    alert('团队创建成功！');
    await fetchDashboardData();
  } catch (err) {
    const errorMsg = err.response?.data?.group_name?.[0] || err.response?.data?.error || '未知错误';
    alert(`创建失败: ${errorMsg}`);
  }
};

const handleUpdateProjectInfo = async () => {
  try {
    const payload = {project_title: editTeam.project_title, project_description: editTeam.project_description};
    await api.updateMyTeam(payload);
    alert('项目信息更新成功！');
    isProjectModalVisible.value = false;
    await fetchDashboardData();
  } catch (err) {
    alert(`更新失败: ${err.response?.data?.error || '请检查输入'}`);
  }
};

const handleUpdateAdvisors = async () => {
  try {
    // [修复] 确保提交的 payload key 与后端 serializer 的 source 匹配
    const payload = {
      preferred_advisor_1_id: preferences.preferred_advisor_1,
      preferred_advisor_2_id: preferences.preferred_advisor_2,
      preferred_advisor_3_id: preferences.preferred_advisor_3,
    }
    await api.updateMyTeam(payload);
    alert('导师选择保存成功！');
    isAdvisorModalVisible.value = false;
    await fetchDashboardData();
  } catch (err) {
    alert(`更新失败: ${err.response?.data?.error || '请检查输入'}`);
  }
};



const handleJoinTeam = async (teamId) => {
  if (!confirm('确定要申请加入该团队吗？')) return;
  try {
    await api.joinTeam(teamId);
    alert('成功加入团队！');
    isAllTeamsModalVisible.value = false;
    await fetchDashboardData();
  } catch (err) {
    alert(`加入失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const handleLeaveTeam = async () => {
  if (!confirm('您确定要退出当前团队吗？')) return;
  try {
    const res = await api.leaveTeam();
    alert(res.data.message);
    await fetchDashboardData();
  } catch (err) {
    alert(`操作失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const handleDisbandTeam = async () => {
  if (!confirm('警告：此操作不可逆！确定要解散您的团队吗？')) return;
  try {
    const res = await api.disbandTeam();
    alert(res.data.message);
    await fetchDashboardData();
  } catch (err) {
    alert(`操作失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const handleRemoveMember = async (member) => {
  if (!confirm(`确定要将成员“${member.stu_name}”移出团队吗？`)) return;
  try {
    // [修复] 正确处理 async/await 的返回值
    const res = await api.removeMember(member.stu_id);
    alert(res.data.message);
    await fetchDashboardData(); // 刷新整个仪表盘数据
  } catch (err) {
    alert(`操作失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const handleAddMember = async (student) => {
  if (!confirm(`确定要将“${student.stu_name}”直接添加到您的团队中吗？`)) return;
  try {
    const res = await api.addMemberByCaptain({student_id: student.stu_id});
    alert(res.data.message);
    // [修复] 添加成功后，刷新可邀请成员列表和仪表盘数据
    await fetchAvailableTeammates(); // 刷新弹窗内的数据
    await fetchDashboardData(); // 刷新主页的成员列表
  } catch (err) {
    alert(`添加失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
/* 样式保持不变 */
.page-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #333;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 2em;
  font-weight: 700;
  color: #2c3e50;
}

.page-header p {
  color: #555;
  font-size: 1em;
}

.team-container, .no-team-container {
  display: grid;
  gap: 30px;
}

.team-container {
  grid-template-columns: 2fr 1.2fr;
}

.no-team-container {
  grid-template-columns: 1fr 1fr;
}

.info-card, .actions-card, .action-card, .status-card {
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.card-header h2 {
  margin: 0;
  font-size: 1.8em;
  color: #007bff;
}

.captain-flag {
  background: #ffc107;
  color: #333;
  padding: 5px 12px;
  border-radius: 15px;
  font-weight: 600;
  font-size: 0.8em;
}

.card-section {
  margin-top: 25px;
  border-top: 1px solid #f0f0f0;
  padding-top: 25px;
  position: relative;
}

.card-section:first-child {
  border-top: none;
  padding-top: 0;
}

.card-section h3 {
  font-size: 1.2em;
  margin-bottom: 15px;
  color: #2c3e50;
}

.card-section h4 {
  font-size: 1.1em;
  margin: 0 0 10px;
}

.card-section p {
  margin: 0;
  line-height: 1.6;
  color: #555;
}

.advisor-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.advisor-list li {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-list {
  list-style: none;
  padding: 0;
}

.member-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.member-list li:last-child {
  border-bottom: none;
}

.captain-badge {
  background: #e9ecef;
  color: #495057;
  font-size: 0.75em;
  padding: 3px 8px;
  border-radius: 10px;
  font-weight: bold;
}

.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-sm {
  padding: 8px 12px;
  font-size: 0.9em;
}

.btn-edit-small {
  position: absolute;
  top: 20px;
  right: 0;
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 0.9em;
}

.btn-edit-tiny {
  background: #f0f0f0;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 0.8em;
  padding: 2px 6px;
  border-radius: 4px;
}

.btn-remove-small {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  color: #dc3545;
}

.full-width {
  width: 100%;
  justify-content: center;
}

.card-actions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 15px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.form-group input, .form-group textarea, .form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-sizing: border-box;
}

.search-input {
  padding-left: 15px;
}

.status-card {
  text-align: center;
  padding: 50px;
  background: #f8f9fa;
  border-radius: 12px;
}

.status-card h3 {
  font-size: 1.5em;
  margin-bottom: 10px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 20px;
}

.modal-list {
  list-style: none;
  padding: 0;
}

.modal-list.scrollable {
  max-height: 50vh;
  overflow-y: auto;
  padding-right: 10px;
}

.team-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.team-item:hover {
  background-color: #f8f9fa;
}

.team-item-info p {
  margin: 2px 0;
  font-size: 0.9em;
  color: #666;
}

.loading-state.small {
  text-align: center;
  padding: 20px;
}
.modal-content.large {
  max-width: 800px;
}

.advisor-selection-container {
  display: flex;
  gap: 30px;
}

.preferences-summary {
  flex: 1;
  border-right: 1px solid #eee;
  padding-right: 30px;
}

.preference-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}
.preference-item span {
  color: #666;
}
.preference-item strong {
  font-size: 1.1em;
}

.advisor-list-panel {
  flex: 1.5;
  display: flex;
  flex-direction: column;
}

.advisor-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.advisor-item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-link {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
}

.advisor-detail-card {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 15px;
}

.advisor-detail-card p {
  margin: 0 0 12px 0;
}

.introduction-box {
  white-space: pre-wrap; /* 保留换行和空格 */
  max-height: 150px;
  overflow-y: auto;
  background-color: #fff;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>