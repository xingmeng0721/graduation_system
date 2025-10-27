<template>
  <div class="page-container">
    <h1>自动分配</h1>
    <p class="page-description">
      这里列出了所有的互选活动。对于已经过了截止时间的活动，您可以点击“自动分配”按钮，系统将为未选择导师的学生指派导师。
    </p>

    <!-- 分配结果提示 -->
    <div v-if="assignmentResult" class="assignment-result">
      <h4>分配结果</h4>
      <p class="success-message">{{ assignmentResult.message }}</p>
      <p>成功分配: {{ assignmentResult.assigned_count }} 人</p>
      <p v-if="assignmentResult.unassigned_count > 0" class="error-message">
        未分配: {{ assignmentResult.unassigned_count }} 人 (可能是由于导师容量已满)
      </p>
      <div v-if="assignmentResult.unassigned_students && assignmentResult.unassigned_students.length > 0">
        <h5>未分配学生列表:</h5>
        <ul class="failed-list">
          <li v-for="(student, index) in assignmentResult.unassigned_students" :key="index">
            {{ student.stu_name }}
          </li>
        </ul>
      </div>
    </div>

    <div v-if="apiError" class="error-message">{{ apiError }}</div>

    <!-- 数据表格 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>活动名称</th>
            <th>截止时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="4" class="text-center">加载中...</td>
          </tr>
          <tr v-else-if="events.length === 0">
            <td colspan="4" class="text-center">暂无互选活动</td>
          </tr>
          <tr v-for="event in events" :key="event.event_id">
            <td>{{ event.event_name }}</td>
            <td>{{ formatDateTime(event.end_time) }}</td>
            <td>
              <span :class="getEventStatus(event.end_time).class">
                {{ getEventStatus(event.end_time).text }}
              </span>
            </td>
            <td>
              <button
                @click="handleAutoAssign(event)"
                :disabled="!isEventExpired(event.end_time) || isAssigning[event.event_id]"
                class="btn btn-primary"
              >
                {{ isAssigning[event.event_id] ? '分配中...' : '自动分配' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const events = ref([]);
const loading = ref(false);
const isAssigning = ref({}); // 用于跟踪每个按钮的加载状态
const assignmentResult = ref(null);
const apiError = ref(null);

const fetchEvents = async () => {
  loading.value = true;
  apiError.value = null;
  try {
    const response = await api.getMutualSelectionEvents();
    // 按截止时间降序排序
    events.value = response.data.sort((a, b) => new Date(b.end_time) - new Date(a.end_time));
  } catch (error) {
    console.error("获取活动列表失败:", error);
    apiError.value = "获取活动列表失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
};

onMounted(fetchEvents);

const isEventExpired = (endTime) => {
  return new Date(endTime) < new Date();
};

const getEventStatus = (endTime) => {
  if (isEventExpired(endTime)) {
    return { text: '已结束', class: 'status-expired' };
  }
  return { text: '进行中', class: 'status-active' };
};

const handleAutoAssign = async (event) => {
  if (!confirm(`确定要为活动 "${event.event_name}" 执行自动分配吗？\n此操作将覆盖该活动之前的分配结果。`)) {
    return;
  }

  isAssigning.value[event.event_id] = true;
  assignmentResult.value = null;
  apiError.value = null;

  try {
    const response = await api.autoAssignEvent(event.event_id);
    assignmentResult.value = response.data;
  } catch (error) {
    console.error(`分配失败 (Event ID: ${event.event_id}):`, error);
    apiError.value = `分配失败: ${error.response?.data?.error || '服务器内部错误'}`;
  } finally {
    isAssigning.value[event.event_id] = false;
  }
};

const formatDateTime = (dateTime) => {
  if (!dateTime) return 'N/A';
  return new Date(dateTime).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
};
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.page-description {
  margin-bottom: 20px;
  color: #555;
  background-color: #f8f9fa;
  border-left: 4px solid #007bff;
  padding: 15px;
  border-radius: 4px;
}
.table-wrapper {
  overflow-x: auto;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th, .data-table td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
  vertical-align: middle;
}
.data-table th {
  background-color: #f2f2f2;
}
.text-center {
  text-align: center;
}
.btn {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn-primary { background-color: #007bff; color: white; }
.btn-primary:disabled { background-color: #a0cffc; cursor: not-allowed; }

.status-active {
  color: #28a745;
  font-weight: bold;
}
.status-expired {
  color: #dc3545;
  font-weight: bold;
}

.assignment-result {
  background-color: #e9f5ff;
  border: 1px solid #b3d9ff;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 20px;
}
.assignment-result h4 {
  margin-top: 0;
}
.error-message {
  color: #721c24;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 10px;
  border-radius: 4px;
  margin-top: 15px;
}
.success-message {
    color: #155724;
    font-weight: bold;
}
.failed-list {
  list-style-type: none;
  padding-left: 0;
  margin-top: 10px;
}
.failed-list li {
  background-color: #f8d7da;
  color: #721c24;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 5px;
  font-size: 0.9em;
}
</style>