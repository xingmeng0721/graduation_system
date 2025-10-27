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
            <th>开始时间</th>
            <th>结束时间</th>
            <th>参与教师数</th>
            <th>参与学生数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="text-center">加载中...</td>
          </tr>
          <tr v-else-if="events.length === 0">
            <td colspan="7" class="text-center">暂无数据</td>
          </tr>
          <tr v-for="event in events" :key="event.event_id">
            <td><input type="checkbox" v-model="selectedEvents" :value="event.event_id" /></td>
            <td>{{ event.event_name }}</td>
            <td>{{ formatDateTime(event.start_time) }}</td>
            <td>{{ formatDateTime(event.end_time) }}</td>
            <td>{{ event.teachers.length }}</td>
            <td>{{ event.students.length }}</td>
            <td>
              <button @click="openModal(event)" class="btn btn-secondary btn-sm">编辑</button>
              <button @click="handleDelete(event.event_id)" class="btn btn-danger btn-sm">删除</button>
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
          <div class="form-group">
            <label>开始时间</label>
            <input type="datetime-local" v-model="currentEvent.start_time" required />
          </div>
          <div class="form-group">
            <label>结束时间</label>
            <input type="datetime-local" v-model="currentEvent.end_time" required />
          </div>
          <div class="form-group">
            <label>选择教师 (可多选)</label>
            <select multiple v-model="currentEvent.teachers" class="multi-select">
              <option v-for="teacher in allTeachers" :key="teacher.teacher_id" :value="teacher.teacher_id">
                {{ teacher.teacher_name }} ({{ teacher.teacher_no }})
              </option>
            </select>
          </div>

          <!-- 学生选择区域 (带筛选和快捷操作) -->
          <div class="form-group">
            <label>选择学生 (可多选)</label>
            <div class="student-filters">
              <select v-model="studentGradeFilter">
                <option value="">所有年级</option>
                <option v-for="grade in uniqueGrades" :key="grade" :value="grade">{{ grade }}</option>
              </select>
              <select v-model="studentMajorFilter">
                <option value="">所有专业</option>
                <option v-for="major in allMajors" :key="major.major_id" :value="major.major_name">
                  {{ major.major_name }}
                </option>
              </select>
              <!-- 新增快捷按钮 -->
              <button type="button" @click="selectAllFilteredStudents" class="btn btn-action">全选当前</button>
              <button type="button" @click="deselectAllStudents" class="btn btn-action">全部取消</button>
            </div>
            <select multiple v-model="currentEvent.students" class="multi-select">
              <optgroup v-for="(group, majorName) in groupedStudents" :key="majorName" :label="majorName">
                <option v-for="student in group" :key="student.stu_id" :value="student.stu_id">
                  {{ student.stu_name }} ({{ student.stu_no }})
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

// 响应式状态
const events = ref([]);
const loading = ref(false);
const isModalVisible = ref(false);
const isEditing = ref(false);
const currentEvent = ref({});
const selectedEvents = ref([]);

const allTeachers = ref([]);
const allStudents = ref([]);
const allMajors = ref([]);

// 学生筛选状态
const studentGradeFilter = ref('');
const studentMajorFilter = ref('');

// --- 数据获取 ---
const fetchEvents = async () => {
  loading.value = true;
  try {
    const response = await api.getMutualSelectionEvents();
    events.value = response.data;
  } catch (error) {
    console.error("获取活动列表失败:", error);
    alert("获取活动列表失败！");
  } finally {
    loading.value = false;
  }
};

const fetchRelatedData = async () => {
  try {
    const [teacherRes, studentRes, majorRes] = await Promise.all([
      api.getTeachers(),
      api.getStudents(),
      api.getMajors(),
    ]);
    allTeachers.value = teacherRes.data;
    allStudents.value = studentRes.data;
    allMajors.value = majorRes.data;
  } catch (error) {
    console.error("获取教师、学生或专业列表失败:", error);
  }
};

onMounted(() => {
  fetchEvents();
  fetchRelatedData();
});

// --- 计算属性 ---
const uniqueGrades = computed(() => {
  const grades = allStudents.value.map(s => s.grade);
  return [...new Set(grades)].sort();
});

const filteredStudents = computed(() => {
  return allStudents.value.filter(student => {
    const gradeMatch = !studentGradeFilter.value || student.grade === studentGradeFilter.value;
    const majorMatch = !studentMajorFilter.value || student.major_name === studentMajorFilter.value;
    return gradeMatch && majorMatch;
  });
});

const groupedStudents = computed(() => {
  return filteredStudents.value.reduce((acc, student) => {
    const major = student.major_name || '未分配专业';
    if (!acc[major]) {
      acc[major] = [];
    }
    acc[major].push(student);
    return acc;
  }, {});
});


// --- 弹窗逻辑 ---
const openModal = (event = null) => {
  studentGradeFilter.value = '';
  studentMajorFilter.value = '';
  if (event) {
    isEditing.value = true;
    currentEvent.value = {
      ...event,
      start_time: formatForInput(event.start_time),
      end_time: formatForInput(event.end_time),
      teachers: event.teachers.map(t => t.teacher_id),
      students: event.students.map(s => s.stu_id),
    };
  } else {
    isEditing.value = false;
    currentEvent.value = {
      event_name: '',
      start_time: '',
      end_time: '',
      teachers: [],
      students: [],
    };
  }
  isModalVisible.value = true;
};

const closeModal = () => {
  isModalVisible.value = false;
};

// --- CRUD 操作 ---
const handleSubmit = async () => {
  const payload = {
    event_name: currentEvent.value.event_name,
    start_time: currentEvent.value.start_time,
    end_time: currentEvent.value.end_time,
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
    fetchEvents();
  } catch (error) {
    console.error("保存活动失败:", error);
    const errorMsg = error.response?.data?.detail || Object.values(error.response?.data || {}).flat().join(' ') || '请检查输入';
    alert(`保存失败: ${errorMsg}`);
  }
};

const handleDelete = async (id) => {
  if (confirm("确定要删除这个活动吗？")) {
    try {
      await api.deleteMutualSelectionEvent(id);
      alert("删除成功！");
      fetchEvents();
    } catch (error) {
      console.error("删除失败:", error);
      alert("删除失败！");
    }
  }
};

const handleBulkDelete = async () => {
  if (selectedEvents.value.length === 0) return;
  if (confirm(`确定要删除选中的 ${selectedEvents.value.length} 个活动吗？`)) {
    try {
      await api.bulkDeleteMutualSelectionEvents(selectedEvents.value);
      alert("批量删除成功！");
      selectedEvents.value = [];
      fetchEvents();
    } catch (error) {
      console.error("批量删除失败:", error);
      alert("批量删除失败！");
    }
  }
};

// --- 新增：快捷选择学生方法 ---
const selectAllFilteredStudents = () => {
  // 使用Set来自动处理重复项
  const selectedIds = new Set(currentEvent.value.students);
  filteredStudents.value.forEach(student => {
    selectedIds.add(student.stu_id);
  });
  currentEvent.value.students = Array.from(selectedIds);
};

const deselectAllStudents = () => {
  currentEvent.value.students = [];
};

// --- 工具函数 ---
const formatDateTime = (dateTime) => {
  if (!dateTime) return '';
  return new Date(dateTime).toLocaleString('zh-CN');
};

const formatForInput = (dateTime) => {
  if (!dateTime) return '';
  const d = new Date(dateTime);
  return d.toISOString().slice(0, 16);
};

const toggleSelectAll = (event) => {
  if (event.target.checked) {
    selectedEvents.value = events.value.map(e => e.event_id);
  } else {
    selectedEvents.value = [];
  }
};
</script>

<style scoped>
/* 页面和表格样式 */
.page-container {
  padding: 20px;
}
.actions-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
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
  padding: 8px;
  text-align: left;
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
}
.btn-primary { background-color: #007bff; color: white; }
.btn-secondary { background-color: #6c757d; color: white; }
.btn-danger { background-color: #dc3545; color: white; }
.btn-sm { padding: 4px 8px; font-size: 0.9em; }

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: 8px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
}
.form-group input, .form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.multi-select {
  height: 200px;
}
.modal-actions {
  text-align: right;
  margin-top: 20px;
}
.modal-actions .btn {
  margin-left: 10px;
}

/* 学生筛选器和快捷按钮样式 */
.student-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}
.student-filters select {
  flex: 1; /* 让下拉框占据可用空间 */
}
.btn-action {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background-color: #6c757d;
  color: white;
  white-space: nowrap; /* 防止按钮文字换行 */
}
.btn-action:hover {
  background-color: #5a6268;
}
</style>