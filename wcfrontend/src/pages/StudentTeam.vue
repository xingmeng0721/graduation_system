<template>
  <div class="page-container">
    <h1>我的团队</h1>
    <div v-if="loading" class="loading-state">正在加载团队信息...</div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <!-- 场景一：已加入团队 -->
    <div v-if="myTeam && !loading" class="team-container">
      <!-- 左侧：团队信息 -->
      <div class="team-info-card">
        <h2>{{ myTeam.group_name }}</h2>
        <p class="event-name">所属活动: {{ myTeam.event_name }}</p>

        <div class="project-section">
          <h3>项目信息 <button v-if="isCaptain" @click="openEditProjectModal" class="btn-edit-small">编辑</button></h3>
          <h4>{{ myTeam.project_title || '尚未填写项目标题' }}</h4>
          <p>{{ myTeam.project_description || '尚未填写项目简介' }}</p>
        </div>

        <div class="advisor-section">
          <h3>志愿导师 <button v-if="isCaptain" @click="openEditAdvisorsModal" class="btn-edit-small">选择</button></h3>
          <p>第一志愿: {{ myTeam.preferred_advisor_1?.teacher_name || '未选择' }}</p>
          <p>第二志愿: {{ myTeam.preferred_advisor_2?.teacher_name || '未选择' }}</p>
          <p>第三志愿: {{ myTeam.preferred_advisor_3?.teacher_name || '未选择' }}</p>
        </div>

        <div class="final-advisor-section">
          <h3>最终指导老师</h3>
          <p class="final-advisor">{{ myTeam.advisor?.teacher_name || '待分配' }}</p>
        </div>

        <div class="actions-bar">
          <button @click="handleLeaveTeam" class="btn btn-danger">
            {{ isCaptain ? '解散团队' : '退出团队' }}
          </button>
        </div>
      </div>

      <!-- 右侧：成员管理 -->
      <div class="team-members-card">
        <h3>团队成员 ({{ myTeam.members.length }})
          <button v-if="isCaptain" @click="openInviteModal" class="btn-primary-small">邀请新成员</button>
        </h3>
        <ul>
          <li v-for="member in myTeam.members" :key="member.stu_id">
            {{ member.stu_name }} ({{ member.stu_no }})
            <span v-if="member.stu_id === myTeam.captain.stu_id" class="captain-badge">队长</span>
            <button v-if="isCaptain && member.stu_id !== myTeam.captain.stu_id" @click="removeMember(member)" class="btn-remove-small">移除</button>
          </li>
        </ul>
      </div>
    </div>

    <!-- 场景二：未加入团队 -->
    <div v-if="!myTeam && !loading && activeEvent" class="no-team-container">
      <div class="action-card">
        <h3>创建我的团队</h3>
        <p>您正在参与活动 “{{ activeEvent.event_name }}”。创建一个团队来开始您的项目吧！</p>
        <form @submit.prevent="handleCreateTeam">
          <div class="form-group">
            <label>团队名称</label>
            <input v-model="newTeam.group_name" required placeholder="例如：AI图像识别小组">
          </div>
          <div class="form-group">
            <label>项目标题</label>
            <input v-model="newTeam.project_title" required placeholder="一个响亮的项目名称">
          </div>
          <div class="form-group">
            <label>项目简介</label>
            <textarea v-model="newTeam.project_description" required placeholder="简单描述一下你们想做什么"></textarea>
          </div>
          <button type="submit" class="btn btn-primary">确认创建，成为队长</button>
        </form>
      </div>
      <div class="action-card">
        <h3>或加入现有团队</h3>
        <p>查看当前活动中可以加入的团队列表。</p>
        <button @click="fetchJoinableTeams" class="btn btn-secondary">查找团队</button>
      </div>
    </div>

    <!-- 场景三：无进行中的活动 -->
    <div v-if="!activeEvent && !loading" class="no-event-card">
        <h3>当前没有正在进行的互选活动</h3>
        <p>请等待管理员开启新的活动后再进行组队操作。</p>
    </div>

    <!-- 弹窗：邀请成员 -->
    <div v-if="isInviteModalVisible" class="modal-overlay" @click.self="isInviteModalVisible = false">
      <div class="modal-content">
        <h2>邀请新成员</h2>
        <p>从当前活动中选择未分组的学生加入您的团队。</p>
        <div v-for="student in availableStudents" :key="student.stu_id" class="student-invite-item">
          <span>{{ student.stu_name }} ({{ student.stu_no }})</span>
          <button @click="inviteStudent(student)">邀请</button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="isAllTeamsModalVisible" class="modal-overlay" @click.self="isAllTeamsModalVisible = false">
  <div class="modal-content">
    <h2>当前活动的所有团队</h2>

    <div v-if="allTeams.length === 0">暂无团队信息</div>
    <ul v-else>
      <li v-for="team in allTeams" :key="team.group_id" class="joinable-team-item">
        <h4>{{ team.group_name }}</h4>
        <p>项目：{{ team.project_title || '未填写' }}</p>
        <p>队长：{{ team.captain?.stu_name }}</p>
        <p>成员数：{{ team.members.length }}/{{ team.max_members }}</p>
        <button @click="joinTeam(team)">申请加入</button>
      </li>
    </ul>
  </div>
</div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api'; // 假设api.js已更新

const myTeam = ref(null);
const activeEvent = ref(null); // 当前学生参与的活动
const loading = ref(true);
const error = ref(null);
const isCaptain = ref(false);

const newTeam = ref({
  group_name: '',
  project_title: '',
  project_description: '',
});

const isInviteModalVisible = ref(false);
const availableStudents = ref([]); // 可邀请的学生列表
const isAllTeamsModalVisible = ref(false);
const allTeams = ref([]);


const fetchData = async () => {
  console.log("--- [DEBUG] fetchData started ---");
  loading.value = true;
  error.value = null;

  // 1. 尝试获取团队信息
  try {
    console.log("Step 1: Calling api.getMyTeam()...");
    const teamResponse = await api.getMyTeam();
    myTeam.value = teamResponse.data;
    console.log("Step 1 SUCCESS: Found team data.", myTeam.value);
  } catch (err) {
    if (err.response && err.response.status === 404) {
      console.log("Step 1 FAILED with 404: User has no team. This is expected.");
      myTeam.value = null;
    } else {
      console.error("Step 1 FAILED with unexpected error:", err);
      error.value = "加载团队信息时发生意外错误。";
    }
  }

  // 2. 尝试获取活动信息
  try {
    console.log("Step 2: Calling api.getActiveEventForStudent()...");
    const eventResponse = await api.getActiveEventForStudent();
    activeEvent.value = eventResponse.data;
    console.log("Step 2 SUCCESS: Found active event.", activeEvent.value);
  } catch (err) {
    if (err.response && err.response.status === 404) {
      console.log("Step 2 FAILED with 404: No active event found for this user.");
      activeEvent.value = null;
    } else {
      console.error("Step 2 FAILED with unexpected error:", err);
      error.value = "加载活动信息时发生意外错误。";
    }
  }

  loading.value = false;
  console.log("--- [DEBUG] fetchData finished ---");
};

onMounted(fetchData);

const handleCreateTeam = async () => {
  if (!newTeam.value.group_name || !newTeam.value.project_title) {
    alert("团队名称和项目标题不能为空！");
    return;
  }
  try {
    await api.createTeam(newTeam.value); // 后端createTeam现在应该处理这些新字段
    alert('团队创建成功！');
    fetchData(); // 重新加载页面数据
  } catch (err) {
    alert(`创建失败: ${err.response?.data?.error || '未知错误'}`);
  }
};

const openInviteModal = async () => {
    try {
        // 后端需要一个接口来获取同活动下、未组队的学生
        const response = await api.getAvailableStudentsForTeam();
        availableStudents.value = response.data;
        isInviteModalVisible.value = true;
    } catch(err) {
        alert("获取可邀请学生列表失败。");
    }
};

// 其他方法如 openEditProjectModal, handleLeaveTeam 等保持不变或根据新逻辑实现
const handleLeaveTeam = async () => {
  if (isCaptain.value) {
    if (!confirm('您是队长，解散团队后所有成员都将被移出。确定要解散团队吗？')) return;
  } else {
    if (!confirm('确定要退出当前团队吗？')) return;
  }
  try {
    const res = await api.leaveTeam();
    alert(res.data.message || '操作成功');
    fetchData(); // 重新加载团队信息
  } catch (err) {
    alert(err.response?.data?.error || '操作失败');
  }
};
const openEditProjectModal = () => { alert("编辑项目功能待实现"); };
const openEditAdvisorsModal = () => { alert("选择志愿导师功能待实现"); };
const fetchJoinableTeams = async () => {
  try {
    const response = await api.getAllTeams(); // 调用 /all-teams 接口
    allTeams.value = response.data;
    isAllTeamsModalVisible.value = true;
  } catch (err) {
    alert(err.response?.data?.error || '加载团队列表失败');
  }
};
const joinTeam = async (team) => {
  if (!confirm(`确定要申请加入团队「${team.group_name}」吗？`)) return;
  try {
    await api.joinTeam(team.group_id);
    alert('申请加入成功！');
    isAllTeamsModalVisible.value = false;
    fetchData();
  } catch (err) {
    alert(err.response?.data?.error || '申请失败');
  }
};
const inviteStudent = (student) => { alert(`邀请 ${student.stu_name} 的功能待实现`); };
const removeMember = (member) => { alert(`移除 ${member.stu_name} 的功能待实现`); };
</script>

<style scoped>
/* 样式与之前类似，但为新布局调整 */
.page-container { padding: 20px; max-width: 1200px; margin: auto; }
.team-container { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
.team-info-card, .team-members-card, .action-card, .no-event-card { background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
h2, h3 { margin-top: 0; }
.event-name { font-style: italic; color: #666; }
.project-section, .advisor-section, .final-advisor-section { margin-top: 25px; }
.final-advisor { font-weight: bold; color: #007bff; font-size: 1.1em; }
.captain-badge { background-color: #ffc107; color: #333; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; font-weight: bold; margin-left: 8px; }
.btn-edit-small, .btn-primary-small, .btn-remove-small { padding: 4px 8px; font-size: 0.8em; margin-left: 10px; cursor: pointer; border-radius: 4px; border: 1px solid transparent; }
.btn-edit-small { border-color: #6c757d; color: #6c757d; background: none; }
.btn-primary-small { background-color: #007bff; color: white; border: none; }
.btn-remove-small { background-color: #ff4d4f; color: white; border: none; }
.no-team-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; }
.form-group input, .form-group textarea, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1em; }
textarea { min-height: 100px; resize: vertical; }
</style>