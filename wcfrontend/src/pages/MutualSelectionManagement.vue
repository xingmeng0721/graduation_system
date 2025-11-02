<template>
  <div class="page-container">
    <h1>互选活动管理</h1>
    <div class="actions-bar">
      <button @click="openModal()" class="btn btn-primary">创建新活动</button>
      <button @click="handleBulkDelete" :disabled="selectedEvents.length === 0" class="btn btn-danger">
        批量删除
      </button>
    </div>

    <!-- 数据表格 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th><input type="checkbox" @change="toggleSelectAll" /></th>
            <th>活动名称</th>
            <th>状态</th>
            <th>学生互选时间</th>
            <th>教师互选时间</th>
            <th>参与教师数</th>
            <th>参与学生数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="text-center">加载中...</td>
          </tr>
          <tr v-else-if="events.length === 0">
            <td colspan="8" class="text-center">暂无数据</td>
          </tr>
          <tr v-for="event in events" :key="event.event_id">
            <td><input type="checkbox" v-model="selectedEvents" :value="event.event_id" /></td>
            <td>{{ event.event_name }}</td>
            <td>
              <span :class="['status-badge', `status-${getStatusClass(event.status)}`]">{{ event.status }}</span>
            </td>
            <td>{{ formatDateTimeRange(event.stu_start_time, event.stu_end_time) }}</td>
            <td>{{ formatDateTimeRange(event.tea_start_time, event.tea_end_time) }}</td>
            <td>{{ event.teacher_count }}</td>
            <td>{{ event.student_count }}</td>
            <td>
              <button @click="openModal(event)" class="btn btn-secondary btn-sm" :disabled="event.status === '已结束'">编辑</button>
              <button @click="handleDelete(event.event_id)" class="btn btn-danger btn-sm" :disabled="event.status === '已结束'">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建/编辑弹窗 -->
    <div v-if="isModalVisible" class="modal-overlay">
      <div class="modal-content">
        <h2>{{ isEditing ? '编辑活动' : '创建新活动' }}</h2>
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>活动名称</label>
            <input type="text" v-model="currentEvent.event_name" required />
          </div>
          <!-- 时间选择器 -->
          <div class="time-grid">
            <div class="form-group">
              <label>学生开始时间</label>
              <input type="datetime-local" v-model="currentEvent.stu_start_time" required />
            </div>
            <div class="form-group">
              <label>学生截止时间</label>
              <input type="datetime-local" v-model="currentEvent.stu_end_time" required />
            </div>
            <div class="form-group">
              <label>教师开始时间</label>
              <input type="datetime-local" v-model="currentEvent.tea_start_time" required />
            </div>
            <div class="form-group">
              <label>教师截止时间</label>
              <input type="datetime-local" v-model="currentEvent.tea_end_time" required />
            </div>
          </div>

          <!-- 教师选择 -->
          <div class="form-group">
            <label>选择教师 (可多选)</label>
            <select multiple v-model="currentEvent.teachers" class="multi-select">
              <option v-for="teacher in allTeachers" :key="teacher.teacher_id" :value="teacher.teacher_id" :disabled="isTeacherBusy(teacher.teacher_id)">
                {{ teacher.teacher_name }} ({{ teacher.teacher_no }})
                <span v-if="isTeacherBusy(teacher.teacher_id)"> - 已参加其他活动</span>
              </option>
            </select>
          </div>

          <!-- 学生选择 -->
          <div class="form-group">
            <label>选择学生 (可多选)</label>
            <div class="student-filters">
              <select v-model="studentGradeFilter"><option value="">所有年级</option><option v-for="grade in uniqueGrades" :key="grade" :value="grade">{{ grade }}</option></select>
              <select v-model="studentMajorFilter"><option value="">所有专业</option><option v-for="major in allMajors" :key="major.major_id" :value="major.major_name">{{ major.major_name }}</option></select>
              <button type="button" @click="selectAllFilteredStudents" class="btn btn-action">全选当前</button>
              <button type="button" @click="deselectAllStudents" class="btn btn-action">全部取消</button>
            </div>
            <select multiple v-model="currentEvent.students" class="multi-select">
              <optgroup v-for="(group, majorName) in groupedStudents" :key="majorName" :label="majorName">
                <option v-for="student in group" :key="student.stu_id" :value="student.stu_id" :disabled="isStudentBusy(student.stu_id)">
                  {{ student.stu_name }} ({{ student.stu_no }})
                  <span v-if="isStudentBusy(student.stu_id)"> - 已参加其他活动</span>
                </option>
              </optgroup>
            </select>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary">取消</button>
            <button type="submit" class="btn btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api';

// --- 响应式状态 ---
const events = ref([]);
const loading = ref(false);
const isModalVisible = ref(false);
const isEditing = ref(false);
const currentEvent = ref({});
const selectedEvents = ref([]);

const allTeachers = ref([]);
const allStudents = ref([]);
const allMajors = ref([]);

const studentGradeFilter = ref('');
const studentMajorFilter = ref('');

// --- 计算属性 ---
const busyTeacherIds = computed(() => {
  const busyIds = new Set();
  const eventIdToExclude = isEditing.value ? currentEvent.value.event_id : null;
  events.value.forEach(event => {
    if (event.event_id !== eventIdToExclude && event.status !== '已结束') {
      event.teachers.forEach(t => busyIds.add(t.teacher_id));
    }
  });
  return busyIds;
});

const busyStudentIds = computed(() => {
  const busyIds = new Set();
  const eventIdToExclude = isEditing.value ? currentEvent.value.event_id : null;
  events.value.forEach(event => {
    if (event.event_id !== eventIdToExclude && event.status !== '已结束') {
      event.students.forEach(s => busyIds.add(s.stu_id));
    }
  });
  return busyIds;
});

// --- 数据获取 ---
const fetchAllData = async () => {
  loading.value = true;
  try {
    const [eventRes, teacherRes, studentRes, majorRes] = await Promise.all([
      api.getMutualSelectionEvents(),
      api.getTeachers(),
      api.getStudents(),
      api.getMajors(),
    ]);
    events.value = eventRes.data;
    allTeachers.value = teacherRes.data;
    allStudents.value = studentRes.data;
    allMajors.value = majorRes.data;
  } catch (error) {
    console.error("获取初始数据失败:", error);
    alert("获取数据失败！");
  } finally {
    loading.value = false;
  }
};

onMounted(fetchAllData);

// --- 弹窗逻辑 ---
const openModal = (event = null) => {
  studentGradeFilter.value = '';
  studentMajorFilter.value = '';
  if (event) {
    isEditing.value = true;
    currentEvent.value = {
      ...event,
      // 使用新的 formatForInputLocal 函数
      stu_start_time: formatForInputLocal(event.stu_start_time),
      stu_end_time: formatForInputLocal(event.stu_end_time),
      tea_start_time: formatForInputLocal(event.tea_start_time),
      tea_end_time: formatForInputLocal(event.tea_end_time),
      teachers: event.teachers.map(t => t.teacher_id),
      students: event.students.map(s => s.stu_id),
    };
  } else {
    isEditing.value = false;
    currentEvent.value = {
      event_name: '',
      stu_start_time: '', stu_end_time: '',
      tea_start_time: '', tea_end_time: '',
      teachers: [], students: [],
    };
  }
  isModalVisible.value = true;
};

const closeModal = () => { isModalVisible.value = false; };

// --- CRUD 操作 ---
const handleSubmit = async () => {
  // **关键修复**：在提交时，将本地时间字符串转换为UTC格式的ISO字符串
  const toISOStringWithUTC = (localDateTime) => {
    if (!localDateTime) return null;
    // 创建一个Date对象，它会默认按本地时间解析字符串
    const date = new Date(localDateTime);
    // 使用 toISOString() 将其转换为UTC时间的字符串
    return date.toISOString();
  }

  const payload = {
    event_name: currentEvent.value.event_name,
    stu_start_time: toISOStringWithUTC(currentEvent.value.stu_start_time),
    stu_end_time: toISOStringWithUTC(currentEvent.value.stu_end_time),
    tea_start_time: toISOStringWithUTC(currentEvent.value.tea_start_time),
    tea_end_time: toISOStringWithUTC(currentEvent.value.tea_end_time),
    teachers: currentEvent.value.teachers,
    students: currentEvent.value.students,
  };

  try {
    if (isEditing.value) {
      await api.updateMutualSelectionEvent(currentEvent.value.event_id, payload);
      alert("活动更新成功！");
    } else {
      await api.createMutualSelectionEvent(payload);
      alert("活动创建成功！");
    }
    closeModal();
    await fetchAllData();
  } catch (error) {
    console.error("保存活动失败:", error);
    const errorData = error.response?.data;
    let errorMsg = '请检查输入';
    if (typeof errorData === 'string') {
        errorMsg = errorData;
    } else if (errorData) {
        // 将所有错误信息拼接起来
        errorMsg = Object.values(errorData).flat().join(' ');
    }
    alert(`保存失败: ${errorMsg}`);
  }
};

const handleDelete = async (id) => {
  if (confirm("确定要删除这个活动吗？")) {
    try {
      await api.deleteMutualSelectionEvent(id);
      alert("删除成功！");
      await fetchAllData();
    } catch (error) { console.error("删除失败:", error); alert("删除失败！"); }
  }
};

const handleBulkDelete = async () => {
  if (selectedEvents.value.length === 0) return;
  if (confirm(`确定要删除选中的 ${selectedEvents.value.length} 个活动吗？`)) {
    try {
      // 假设API需要一个对象 { ids: [...] }
      await api.bulkDeleteMutualSelectionEvents({ ids: selectedEvents.value });
      alert("批量删除成功！");
      selectedEvents.value = [];
      await fetchAllData();
    } catch (error) { console.error("批量删除失败:", error); alert("批量删除失败！"); }
  }
};

// --- 学生选择逻辑 ---
const uniqueGrades = computed(() => [...new Set(allStudents.value.map(s => s.grade))].sort());
const filteredStudents = computed(() => {
  return allStudents.value.filter(student =>
    (!studentGradeFilter.value || student.grade === studentGradeFilter.value) &&
    (!studentMajorFilter.value || student.major_name === studentMajorFilter.value)
  );
});
const groupedStudents = computed(() => {
  return filteredStudents.value.reduce((acc, student) => {
    const major = student.major_name || '未分配专业';
    if (!acc[major]) acc[major] = [];
    acc[major].push(student);
    return acc;
  }, {});
});
const selectAllFilteredStudents = () => {
  const selectedIds = new Set(currentEvent.value.students);
  filteredStudents.value.forEach(student => {
    if (!isStudentBusy(student.stu_id)) {
      selectedIds.add(student.stu_id);
    }
  });
  currentEvent.value.students = Array.from(selectedIds);
};
const deselectAllStudents = () => { currentEvent.value.students = []; };

// --- 检查函数 ---
const isTeacherBusy = (id) => busyTeacherIds.value.has(id);
const isStudentBusy = (id) => busyStudentIds.value.has(id);

// --- 工具函数 ---
const formatDateTime = (dt) => dt ? new Date(dt).toLocaleString('zh-CN', { hour12: false }) : '';
const formatDateTimeRange = (start, end) => `${formatDateTime(start)} - ${formatDateTime(end)}`;

// **关键修复**：这个函数将UTC时间字符串转换为适合 <input type="datetime-local"> 的本地时间字符串
const formatForInputLocal = (utcDateTime) => {
    if (!utcDateTime) return '';
    const date = new Date(utcDateTime);
    // 手动构建 YYYY-MM-DDTHH:mm 格式的本地时间字符串
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
};

const getStatusClass = (status) => {
  if (status === '进行中') return 'ongoing';
  if (status === '已结束') return 'finished';
  return 'pending';
};
const toggleSelectAll = (e) => {
  selectedEvents.value = e.target.checked ? events.value.map(ev => ev.event_id) : [];
};
</script>

<style scoped>
/* 页面和表格样式 */
.page-container { padding: 20px; }
.actions-bar { margin-bottom: 20px; display: flex; gap: 10px; }
.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { border: 1px solid #ddd; padding: 10px; text-align: left; vertical-align: middle;}
.data-table th { background-color: #f2f2f2; font-weight: 600; }
.text-center { text-align: center; }
.btn { padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
.btn:disabled { background-color: #ccc; cursor: not-allowed; }
.btn-primary { background-color: #007bff; color: white; }
.btn-secondary { background-color: #6c757d; color: white; }
.btn-danger { background-color: #dc3545; color: white; }
.btn-sm { padding: 4px 8px; font-size: 0.9em; margin-right: 5px;}

/* 弹窗样式 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background-color: white; padding: 30px; border-radius: 8px; width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: 600; }
.form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.multi-select { height: 200px; }
.multi-select option:disabled { color: #aaa; background-color: #f9f9f9; }
.modal-actions { text-align: right; margin-top: 20px; }
.modal-actions .btn { margin-left: 10px; }

/* 新增样式 */
.time-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.student-filters { display: flex; gap: 10px; margin-bottom: 10px; align-items: center; }
.student-filters select { flex: 1; }
.btn-action { padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; background-color: #007bff; color: white; white-space: nowrap; }
.btn-action:hover { background-color: #0056b3; }

/* 状态标签 */
.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  color: white;
  font-size: 0.85em;
  font-weight: 600;
}
.status-pending { background-color: #ffc107; } /* 未开始 - 黄色 */
.status-ongoing { background-color: #28a745; } /* 进行中 - 绿色 */
.status-finished { background-color: #6c757d; } /* 已结束 - 灰色 */
</style>