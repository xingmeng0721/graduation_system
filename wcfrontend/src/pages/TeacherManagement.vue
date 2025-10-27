<template>
  <div>
    <h1>教师管理</h1>
    <div class="management-container">
      <!-- 批量注册教师 -->
      <div class="form-card">
        <h2>批量注册教师</h2>
        <div class="bulk-register-actions">
          <button @click="handleDownloadTemplate" class="btn-secondary">下载模板</button>
          <input type="file" @change="handleFileChange" accept=".xlsx, .xls" ref="fileInput" style="display: none;" />
          <button @click="$refs.fileInput.click()" class="btn-secondary">选择文件</button>
          <button @click="handleBulkUpload" :disabled="!selectedFile || isUploading" class="btn-submit">
            {{ isUploading ? '上传中...' : '上传并注册' }}
          </button>
        </div>
        <p v-if="selectedFile" class="file-name-display">已选择文件: {{ selectedFile.name }}</p>

        <!-- 批量注册结果显示区域 -->
        <div v-if="bulkResults" class="bulk-results">
          <h4>注册结果</h4>
          <p class="success-message">成功: {{ bulkResults.success_count }}</p>
          <p class="error-message">失败: {{ bulkResults.failure_count }}</p>
          <div v-if="bulkResults.failed_entries && bulkResults.failed_entries.length > 0">
            <h5>失败详情:</h5>
            <ul class="failed-list">
              <li v-for="(item, index) in bulkResults.failed_entries" :key="index">
                行 {{ item.row }}: (工号: {{ item.teacher_no || '未知' }}) - {{ item.error }}
              </li>
            </ul>
          </div>
        </div>
        <div v-if="bulkError" class="error-message">{{ bulkError }}</div>
      </div>

      <!-- 添加新教师表单 -->
      <div class="form-card">
        <h2>添加新教师</h2>
        <form @submit.prevent="addTeacher">
          <div class="form-grid">
            <div class="form-group">
              <label>工号</label>
              <input v-model="newTeacher.teacher_no" type="text" required />
            </div>
            <div class="form-group">
              <label>姓名</label>
              <input v-model="newTeacher.teacher_name" type="text" required />
            </div>
            <div class="form-group">
              <label>初始密码</label>
              <input v-model="newTeacher.password" type="password" required />
            </div>
            <div class="form-group">
              <label>手机号 (选填)</label>
              <input v-model="newTeacher.phone" type="text" />
            </div>
            <div class="form-group">
              <label>电子邮箱 (选填)</label>
              <input v-model="newTeacher.email" type="email" />
            </div>
            <div class="form-group">
              <label>研究方向 (选填)</label>
              <input v-model="newTeacher.research_direction" type="text" />
            </div>
            <div class="form-group form-group-full">
              <label>简介 (选填)</label>
              <textarea v-model="newTeacher.introduction"></textarea>
            </div>
          </div>
          <div v-if="addTeacherError" class="error-message">{{ addTeacherError }}</div>
          <div v-if="addTeacherSuccess" class="success-message">{{ addTeacherSuccess }}</div>
          <button type="submit" class="btn-submit">确认添加</button>
        </form>
      </div>

      <!-- 教师列表 -->
      <div class="list-card">
        <div class="list-header">
          <h2>教师列表</h2>
          <div class="filters">
            <div class="form-group">
              <label>搜索</label>
              <input type="text" v-model="searchQuery" placeholder="按工号或姓名搜索..." />
            </div>
          </div>
        </div>

        <div v-if="listSuccess" class="success-message">{{ listSuccess }}</div>
        <div v-if="listError" class="error-message">{{ listError }}</div>

        <div v-if="selectedTeacherIds.size > 0" class="bulk-actions-bar">
          <span>已选择 {{ selectedTeacherIds.size }} 名教师</span>
          <button @click="handleDeleteSelected" class="btn-danger">删除选中</button>
        </div>

        <table>
          <thead>
            <tr>
              <th><input type="checkbox" :checked="isAllFilteredSelected" @change="toggleSelectAllFiltered" /></th>
              <th>工号</th>
              <th>姓名</th>
              <th>研究方向</th>
              <th>手机号</th>
              <th>电子邮箱</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="teacher in filteredTeachers" :key="teacher.teacher_id">
              <td><input type="checkbox" :value="teacher.teacher_id" v-model="selectedTeacherIds" /></td>
              <td>{{ teacher.teacher_no }}</td>
              <td>{{ teacher.teacher_name }}</td>
              <td>{{ teacher.research_direction || '无' }}</td>
              <td>{{ teacher.phone || '无' }}</td>
              <td>{{ teacher.email || '无' }}</td>
              <td>
                <button @click="openEditModal(teacher)" class="btn-secondary-small">编辑</button>
                <button @click="handleDeleteSingle(teacher)" class="btn-danger-small">删除</button>
              </td>
            </tr>
            <tr v-if="filteredTeachers.length === 0">
              <td :colspan="7" style="text-align: center;">没有找到符合条件的教师。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 编辑教师的模态框 -->
    <div v-if="editingTeacher" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <h2>编辑教师信息</h2>
        <form @submit.prevent="handleUpdateTeacher">
          <div class="form-grid">
            <div class="form-group"><label>工号</label><input v-model="editingTeacher.teacher_no" type="text" required /></div>
            <div class="form-group"><label>姓名</label><input v-model="editingTeacher.teacher_name" type="text" required /></div>
            <div class="form-group"><label>手机号</label><input v-model="editingTeacher.phone" type="text" /></div>
            <div class="form-group"><label>电子邮箱</label><input v-model="editingTeacher.email" type="email" /></div>
            <div class="form-group"><label>研究方向</label><input v-model="editingTeacher.research_direction" type="text" /></div>
            <div class="form-group"><label>新密码 (留空则不修改)</label><input v-model="editingTeacher.password" type="password" /></div>
            <div class="form-group form-group-full"><label>简介</label><textarea v-model="editingTeacher.introduction"></textarea></div>
          </div>
          <div v-if="editError" class="error-message">{{ editError }}</div>
          <div class="modal-actions">
            <button type="button" @click="closeEditModal" class="btn-secondary">取消</button>
            <button type="submit" class="btn-submit">保存更改</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import api from '../services/api';

// --- 状态定义 ---
const teachers = ref([]);
const newTeacher = ref({
  teacher_no: '', teacher_name: '', password: '', phone: '', email: '', research_direction: '', introduction: ''
});
const editingTeacher = ref(null);
const selectedTeacherIds = ref(new Set());
const searchQuery = ref('');

// 批量注册状态
const selectedFile = ref(null);
const isUploading = ref(false);
const bulkResults = ref(null);
const bulkError = ref(null);

// 消息状态
const addTeacherError = ref(null);
const addTeacherSuccess = ref(null);
const listError = ref(null);
const listSuccess = ref(null);
const editError = ref(null);

// --- 数据获取 ---
const fetchData = async () => {
  listError.value = null;
  try {
    const response = await api.getTeachers();
    teachers.value = response.data;
  } catch (err) {
    console.error("Failed to fetch teachers:", err);
    listError.value = "加载教师列表失败。";
  }
};
onMounted(fetchData);

// --- 计算属性 ---
const filteredTeachers = computed(() => {
  let result = teachers.value;
  if (searchQuery.value) {
    const lowerCaseQuery = searchQuery.value.toLowerCase();
    result = result.filter(t =>
      t.teacher_name.toLowerCase().includes(lowerCaseQuery) ||
      t.teacher_no.toLowerCase().includes(lowerCaseQuery)
    );
  }
  return result;
});

const isAllFilteredSelected = computed(() => {
  const filteredIds = filteredTeachers.value.map(t => t.teacher_id);
  return filteredIds.length > 0 && filteredIds.every(id => selectedTeacherIds.value.has(id));
});

watch(searchQuery, () => { selectedTeacherIds.value.clear(); });

// --- 方法 ---
const clearMessages = () => {
  addTeacherError.value = null; addTeacherSuccess.value = null;
  listError.value = null; listSuccess.value = null; editError.value = null;
  bulkResults.value = null; bulkError.value = null;
};

const addTeacher = async () => {
  clearMessages();
  try {
    const response = await api.createTeacher(newTeacher.value);
    addTeacherSuccess.value = `教师 ${response.data.teacher_name} 添加成功！`;
    Object.keys(newTeacher.value).forEach(key => newTeacher.value[key] = '');
    await fetchData();
  } catch (err) {
    const errorData = err.response?.data;
    let errorMessage = "添加失败：";
    if (typeof errorData === 'object' && errorData !== null) {
      errorMessage += Object.values(errorData).flat().join(' ');
    } else {
      errorMessage += '请检查输入。';
    }
    addTeacherError.value = errorMessage;
  }
};

const openEditModal = (teacher) => {
  editingTeacher.value = { ...teacher, password: '' };
  editError.value = null;
};
const closeEditModal = () => { editingTeacher.value = null; };

const handleUpdateTeacher = async () => {
  clearMessages();
  if (!editingTeacher.value) return;
  const teacherData = { ...editingTeacher.value };
  if (!teacherData.password) delete teacherData.password;

  try {
    await api.updateTeacher(teacherData.teacher_id, teacherData);
    listSuccess.value = `教师 ${teacherData.teacher_name} 的信息已更新。`;
    closeEditModal();
    await fetchData();
  } catch (err) {
    const errorData = err.response?.data;
    let errorMessage = "更新失败：";
    if (typeof errorData === 'object' && errorData !== null) {
      errorMessage += Object.values(errorData).flat().join(' ');
    } else {
      errorMessage += '请检查输入。';
    }
    editError.value = errorMessage;
  }
};

const handleDeleteSingle = async (teacher) => {
  clearMessages();
  if (confirm(`确定要删除教师 ${teacher.teacher_name} (工号: ${teacher.teacher_no}) 吗？`)) {
    try {
      await api.deleteTeacher(teacher.teacher_id);
      listSuccess.value = `教师 ${teacher.teacher_name} 已删除。`;
      await fetchData();
    } catch (err) {
      listError.value = `删除失败: ${err.response?.data?.detail || '服务器错误'}`;
    }
  }
};

const toggleSelectAllFiltered = (event) => {
  const isChecked = event.target.checked;
  filteredTeachers.value.forEach(t => {
    if (isChecked) selectedTeacherIds.value.add(t.teacher_id);
    else selectedTeacherIds.value.delete(t.teacher_id);
  });
};

const handleDeleteSelected = async () => {
  clearMessages();
  if (confirm(`确定要删除选中的 ${selectedTeacherIds.value.size} 名教师吗？`)) {
    try {
      const idsToDelete = Array.from(selectedTeacherIds.value);
      await api.bulkDeleteTeachers(idsToDelete);
      listSuccess.value = `成功删除 ${idsToDelete.length} 名教师。`;
      selectedTeacherIds.value.clear();
      await fetchData();
    } catch (err) {
      listError.value = `批量删除失败: ${err.response?.data?.error || '服务器错误'}`;
    }
  }
};

// --- 批量操作方法 ---
const handleFileChange = (event) => {
  selectedFile.value = event.target.files[0];
  bulkResults.value = null;
  bulkError.value = null;
};

const handleDownloadTemplate = async () => {
  clearMessages();
  try {
    const response = await api.downloadTeacherTemplate();
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'teacher_registration_template.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    bulkError.value = "下载模板失败。";
    console.error("Download failed:", error);
  }
};

const handleBulkUpload = async () => {
  if (!selectedFile.value) {
    bulkError.value = "请先选择一个文件。";
    return;
  }
  isUploading.value = true;
  bulkError.value = null;
  bulkResults.value = null;

  try {
    const response = await api.bulkRegisterTeachers(selectedFile.value);
    bulkResults.value = response.data;
  } catch (err) {
    console.error("Failed to bulk register:", err);
    bulkError.value = "上传失败：" + (err.response?.data?.error || '服务器发生未知错误。');
  } finally {
    await fetchData();
    isUploading.value = false;
    if (document.querySelector('input[type=file]')) {
      document.querySelector('input[type=file]').value = '';
    }
    selectedFile.value = null;
  }
};
</script>

<style scoped>
/* 完全复用学生管理页面的样式 */
.management-container { display: flex; flex-direction: column; gap: 40px; }
.form-card, .list-card { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.form-group { display: flex; flex-direction: column; }
.form-group-full { grid-column: 1 / -1; }
label { margin-bottom: 8px; font-weight: 600; }
input[type="text"], input[type="password"], input[type="email"], textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-family: inherit; }
textarea { resize: vertical; min-height: 80px; }
.btn-submit { margin-top: 20px; padding: 12px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
.btn-submit:disabled { background-color: #a0cffc; cursor: not-allowed; }
.error-message, .success-message { text-align: left; margin-top: 15px; padding: 10px; border-radius: 4px; }
.error-message { color: #dc3545; background-color: #f8d7da; }
.success-message { color: #155724; background-color: #d4edda; }
.bulk-register-actions { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
.btn-secondary { padding: 12px 20px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
.btn-secondary:hover { background-color: #5a6268; }
.file-name-display { margin-top: 15px; font-style: italic; color: #555; }
.bulk-results { margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }
.bulk-results h4 { margin-bottom: 10px; }
.bulk-results .success-message, .bulk-results .error-message { text-align: left; margin: 5px 0; }
.failed-list { list-style-type: none; padding-left: 0; margin-top: 10px; }
.failed-list li { background-color: #f8d7da; color: #721c24; padding: 8px; border-radius: 4px; margin-bottom: 5px; font-size: 0.9em; }
.list-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
.filters { display: flex; gap: 20px; align-items: flex-end; }
.filters .form-group { margin-bottom: 0; }
.filters label { font-size: 0.9em; margin-bottom: 5px; }
.filters input[type="text"] { padding: 8px; }
.bulk-actions-bar { background-color: #e9f5ff; border: 1px solid #b3d9ff; border-radius: 6px; padding: 10px 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
.btn-danger { padding: 8px 15px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-danger-small, .btn-secondary-small { padding: 5px 10px; font-size: 0.8em; border: none; border-radius: 4px; cursor: pointer; }
.btn-danger-small { background-color: #dc3545; color: white; }
.btn-secondary-small { background-color: #6c757d; color: white; margin-right: 5px; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
th { background-color: #f2f2f2; }
th:first-child, td:first-child { width: 40px; text-align: center; }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background: white; padding: 30px 40px; border-radius: 8px; width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto; }
.modal-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 30px; }
</style>