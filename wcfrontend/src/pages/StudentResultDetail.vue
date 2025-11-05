<template>
  <div class="page-container">
    <div v-if="isLoading" class="status-card"><div class="spinner"></div>正在加载活动结果...</div>
    <div v-if="error" class="status-card error-card">{{ error }}</div>
    <div v-if="resultData">
      <header class="page-header">
        <h1>"{{ resultData.event_name }}" - 活动结果</h1>
        <button @click="$router.back()" class="btn btn-secondary">返回历史列表</button>
      </header>
      <div v-if="resultData.my_team_info" class="results-container">
        <div class="main-panel">
          <h2>我的最终团队</h2>
          <div class="card group-card">
            <div class="card-header"><h3>{{ resultData.my_team_info.group_name }}</h3></div>
            <div class="card-section">
              <h4>最终指导老师</h4>
              <p class="highlight">{{ resultData.my_team_info.advisor?.teacher_name || '未分配' }}</p>
            </div>
            <div class="card-section">
              <h4>项目信息</h4>
              <p><strong>标题:</strong> {{ resultData.my_team_info.project_title || '未填写' }}</p>
              <p><strong>简介:</strong> {{ resultData.my_team_info.project_description || '未填写' }}</p>
            </div>
            <div class="card-section">
              <h4>团队成员</h4>
              <ul class="member-list">
                <li v-for="member in resultData.my_team_info.members" :key="member.stu_id">
                  {{ member.stu_name }} ({{ member.stu_no }})
                  <span v-if="member.is_captain" class="tag member-tag">队长</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <aside class="sidebar-panel">
          <div class="card">
            <h3>我当时的志愿</h3>
            <ul class="preference-list">
              <li><span>第一志愿:</span> <strong>{{ resultData.my_team_info.preferred_advisor_1?.teacher_name || '未选择' }}</strong></li>
              <li><span>第二志愿:</span> <strong>{{ resultData.my_team_info.preferred_advisor_2?.teacher_name || '未选择' }}</strong></li>
              <li><span>第三志愿:</span> <strong>{{ resultData.my_team_info.preferred_advisor_3?.teacher_name || '未选择' }}</strong></li>
            </ul>
          </div>
        </aside>
      </div>
      <div v-else class="status-card info-card-bg">
        <h3>您在该活动中未加入任何团队</h3>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../services/api';

const route = useRoute();
const isLoading = ref(true);
const error = ref(null);
const resultData = ref(null);

onMounted(async () => {
  const eventId = route.params.id;
  try {
    const response = await api.getStudentHistoryDetail(eventId);
    resultData.value = response.data;
  } catch (err) {
    error.value = "无法加载活动结果。";
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
/* (此处省略与教师结果详情页面完全相同的样式) */
</style>