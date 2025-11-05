<template>
  <div class="page-container">
    <h1>分配管理工作台</h1>
    <p class="page-description">
      对于已结束的活动，您可以进入“管理分配”面板。在这里，您可以先运行“自动分配”生成草稿，然后进行“手动调整”，最后“发布结果”使分配正式生效。
    </p>

    <div v-if="apiError" class="error-message global-error">{{ apiError }}</div>

    <!-- 数据表格 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>活动名称</th>
            <th>学生截止时间</th>
            <th>教师截止时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="text-center">加载中...</td>
          </tr>
          <tr v-else-if="events.length === 0">
            <td colspan="5" class="text-center">暂无互选活动</td>
          </tr>
          <tr v-for="event in events" :key="event.event_id">
            <td>{{ event.event_name }}</td>
            <td>{{ formatDateTime(event.stu_end_time) }}</td>
            <td>{{ formatDateTime(event.tea_end_time) }}</td>
            <td>
              <span :class="getEventStatus(event).class">
                {{ getEventStatus(event).text }}
              </span>
            </td>
            <td>
              <button
                @click="openAssignmentModal(event)"
                :disabled="!isEventExpired(event)"
                class="btn btn-primary"
              >
                管理分配
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分配管理弹窗 -->
    <div v-if="isModalVisible" class="modal-overlay">
      <div class="modal-content">
        <h2>“{{ selectedEvent.event_name }}” - 分配管理</h2>

        <!-- 操作按钮区域 -->
        <div class="modal-actions-bar">
          <button @click="handleAutoAssign" :disabled="isProcessing" class="btn btn-secondary">
            {{ isProcessing ? '分配中...' : '运行自动分配' }}
          </button>
          <button @click="handlePublish" :disabled="isProcessing || assignments.length === 0" class="btn btn-success">
             {{ isProcessing ? '发布中...' : '发布最终结果' }}
          </button>
          <button @click="closeModal" class="btn btn-danger">关闭</button>
        </div>

        <p v-if="modalMessage" :class="modalMessage.type === 'success' ? 'success-message' : 'error-message'">
          {{ modalMessage.text }}
        </p>

        <!-- 分配结果表格 -->
        <div class="table-wrapper modal-table">
          <table class="data-table">
             <thead>
              <tr>
                <th>小组名称</th>
                <th>分配导师</th>
                <th>得分</th>
                <th>匹配原因</th>
                <th>类型</th>
                <th>手动调整</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="modalLoading">
                <td colspan="6" class="text-center">加载分配结果中...</td>
              </tr>
              <tr v-else-if="assignments.length === 0">
                <td colspan="6" class="text-center">暂无分配结果，请先运行自动分配。</td>
              </tr>
              <tr v-for="assign in assignments" :key="assign.id">
                <td>{{ assign.group.group_name }}</td>
                <td>{{ assign.teacher.teacher_name }}</td>
                <td>{{ assign.score }}</td>
                <td>{{ assign.explanation }}</td>
                <td>
                  <span :class="['tag', assign.assignment_type === 'manual' ? 'tag-manual' : 'tag-auto']">
                    {{ assign.assignment_type === 'manual' ? '手动' : '自动' }}
                  </span>
                </td>
                <td>
                  <select @change="handleManualAssign(assign.group.group_id, $event)" :disabled="isProcessing">
                    <option :value="assign.teacher.teacher_id" selected>{{ assign.teacher.teacher_name }}</option>
                    <option v-for="t in getAvailableTeachersForGroup(assign.teacher)" :key="t.teacher_id" :value="t.teacher_id">
                      {{ t.teacher_name }}
                    </option>
                    <option value="null">-- 取消分配 --</option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import api from '../services/api';

const events = ref([]);
const loading = ref(false);
const apiError = ref(null);

const isModalVisible = ref(false);
const modalLoading = ref(false);
const isProcessing = ref(false);
const selectedEvent = ref(null);
const assignments = ref([]);
const modalMessage = ref(null);

const fetchEvents = async () => {
  loading.value = true;
  apiError.value = null;
  try {
    const response = await api.getMutualSelectionEvents();
    events.value = response.data.sort((a, b) => new Date(b.tea_end_time) - new Date(a.tea_end_time));
  } catch (error) {
    console.error("获取活动列表失败:", error);
    apiError.value = "获取活动列表失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
};

onMounted(fetchEvents);

const isEventExpired = (event) => {
  const now = new Date();
  return new Date(event.stu_end_time) < now && new Date(event.tea_end_time) < now;
};

const getEventStatus = (event) => {
  if (isEventExpired(event)) {
    return {text: '可分配', class: 'status-expired'};
  }
  const now = new Date();
  if (new Date(event.stu_start_time) > now) {
    return {text: '未开始', class: 'status-pending'};
  }
  return {text: '进行中', class: 'status-active'};
};

const formatDateTime = (dateTime) => {
  if (!dateTime) return 'N/A';
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const openAssignmentModal = async (event) => {
  selectedEvent.value = event;
  isModalVisible.value = true;
  modalMessage.value = null;
  await fetchAssignments();
};

const closeModal = () => {
  isModalVisible.value = false;
  selectedEvent.value = null;
  assignments.value = [];
};

const fetchAssignments = async () => {
  if (!selectedEvent.value) return;
  modalLoading.value = true;
  try {
    const response = await api.getAssignments(selectedEvent.value.event_id);
    assignments.value = response.data;
  } catch (error) {
    modalMessage.value = {type: 'error', text: '加载分配结果失败。'};
    console.error(error);
  } finally {
    modalLoading.value = false;
  }
};

const handleAutoAssign = async () => {
  if (!confirm(`确定要为活动 "${selectedEvent.value.event_name}" 重新运行自动分配吗？\n这将覆盖当前的所有临时分配结果。`)) return;

  isProcessing.value = true;
  modalMessage.value = null;
  try {
    const response = await api.autoAssign(selectedEvent.value.event_id);
    modalMessage.value = {type: 'success', text: response.data.message};
    await fetchAssignments();
  } catch (error) {
    modalMessage.value = {type: 'error', text: `分配失败: ${error.response?.data?.error || '服务器错误'}`};
  } finally {
    isProcessing.value = false;
  }
};

const handleManualAssign = async (groupId, event) => {
  const selectedValue = event.target.value;
  const teacherId = selectedValue === 'null' ? null : Number(selectedValue);

  isProcessing.value = true;
  modalMessage.value = null;
  try {
    const response = await api.manualAssign(selectedEvent.value.event_id, groupId, teacherId);
    modalMessage.value = {type: 'success', text: response.data.message};
    await fetchAssignments();
  } catch (error) {
    modalMessage.value = {type: 'error', text: `调整失败: ${error.response?.data?.error || '服务器错误'}`};
    await fetchAssignments();
  } finally {
    isProcessing.value = false;
  }
};

const handlePublish = async () => {
  if (!confirm(`警告：确定要发布活动 "${selectedEvent.value.event_name}" 的最终分配结果吗？\n此操作不可逆！`)) return;

  isProcessing.value = true;
  modalMessage.value = null;
  try {
    const response = await api.publishAssignments(selectedEvent.value.event_id);
    modalMessage.value = {type: 'success', text: response.data.message};
  } catch (error) {
    modalMessage.value = {type: 'error', text: `发布失败: ${error.response?.data?.error || '服务器错误'}`};
  } finally {
    isProcessing.value = false;
  }
};

const getAvailableTeachersForGroup = (currentTeacher) => {
  if (!selectedEvent.value?.teachers) return [];
  // 返回所有参与活动的老师，除了当前已分配给该组的老师
  return selectedEvent.value.teachers.filter(t => t.teacher_id !== currentTeacher?.teacher_id);
}
</script>

<style scoped>
.page-container {
  padding: 20px;
  font-family: sans-serif;
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
  font-weight: 600;
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
  font-weight: 600;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:disabled {
  background-color: #a0cffc;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.status-active {
  color: #28a745;
  font-weight: bold;
}

.status-expired {
  color: #6c757d;
  font-weight: bold;
}

.status-pending {
  color: #ffc107;
  font-weight: bold;
}

.error-message {
  color: #721c24;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

.global-error {
  margin-bottom: 20px;
}

.success-message {
  color: #155724;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  padding: 10px;
  border-radius: 4px;
  font-weight: bold;
  margin: 10px 0;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 25px;
  border-radius: 8px;
  width: 95%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.modal-content h2 {
  margin-top: 0;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.modal-actions-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.modal-table {
  flex-grow: 1;
  overflow-y: auto;
}

.modal-table select {
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #ccc;
  width: 100%;
}

.tag {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
  color: white;
  display: inline-block;
}

.tag-auto {
  background-color: #17a2b8;
}

.tag-manual {
  background-color: #ffc107;
  color: #212529;
}
</style>