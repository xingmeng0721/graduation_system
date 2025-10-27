<template>
  <div>
    <h1>学生管理</h1>
    <div class="management-container">
      <div class="form-card">
        <h2>批量注册学生</h2>
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
                行 {{ item.row }}: (学号: {{ item.stu_no || '未知' }}) - {{ item.error }}
              </li>
            </ul>
          </div>
        </div>
        <div v-if="bulkError" class="error-message">{{ bulkError }}</div>
      </div>
      <!-- 添加新学生表单 -->
      <div class="form-card">
        <h2>添加新学生</h2>
        <form @submit.prevent="addStudent">
          <div class="form-grid">
            <div class="form-group">
              <label>学号</label>
              <input v-model="newStudent.stu_no" type="text" required />
            </div>
            <div class="form-group">
              <label>姓名</label>
              <input v-model="newStudent.stu_name" type="text" required />
            </div>
            <div class="form-group">
              <label>初始密码</label>
              <input v-model="newStudent.password" type="password" required />
            </div>
            <div class="form-group">
              <label>年级</label>
              <input v-model="newStudent.grade" type="text" required />
            </div>
            <div class="form-group">
              <label>专业</label>
              <input v-model="newStudent.major" type="text" required placeholder="请输入专业名称" />
            </div>
            <div class="form-group">
              <label>手机号 (选填)</label>
              <input v-model="newStudent.phone" type="text" />
            </div>
            <div class="form-group">
              <label>邮箱 (选填)</label>
              <input v-model="newStudent.email" type="email" />
            </div>
          </div>
          <div v-if="addStudentError" class="error-message">{{ addStudentError }}</div>
          <div v-if="addStudentSuccess" class="success-message">{{ addStudentSuccess }}</div>
          <button type="submit" class="btn-submit">确认添加</button>
        </form>
      </div>

      <div class="list-card">
        <div class="list-header">
          <h2>学生列表</h2>
          <div class="filters">
            <div class="form-group">
              <label>搜索</label>
              <input type="text" v-model="searchQuery" placeholder="按学号或姓名搜索..." />
            </div>
            <div class="form-group">
              <label>按年级筛选</label>
              <select v-model="selectedGrade">
                <option value="">全部年级</option>
                <option v-for="grade in uniqueGrades" :key="grade" :value="grade">
                  {{ grade }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>按专业筛选</label>
              <select v-model="selectedMajor">
                <option value="">全部专业</option>
                <option v-for="major in majors" :key="major.major_id" :value="major.major_name">
                  {{ major.major_name }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div v-if="listSuccess" class="success-message">{{ listSuccess }}</div>
        <div v-if="listError" class="error-message">{{ listError }}</div>

        <div v-if="selectedStudentIds.size > 0" class="bulk-actions-bar">
          <span>已选择 {{ selectedStudentIds.size }} 名学生</span>
          <button @click="handleDeleteSelected" class="btn-danger">删除选中</button>
        </div>

        <table>
          <thead>
            <tr>
              <th><input type="checkbox" :checked="isAllFilteredSelected" @change="toggleSelectAllFiltered" /></th>
              <th>学号</th>
              <th>姓名</th>
              <th>年级</th>
              <th>专业</th>
              <th>分组</th>
              <th>手机号</th>
              <th>邮箱</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in filteredStudents" :key="student.stu_id">
              <td><input type="checkbox" :value="student.stu_id" v-model="selectedStudentIds" /></td>
              <td>{{ student.stu_no }}</td>
              <td>{{ student.stu_name }}</td>
              <td>{{ student.grade }}</td>
              <td>{{ student.major_name || '无' }}</td>
              <td>{{ student.group_name || '无' }}</td>
              <td>{{ student.phone || '无' }}</td>
              <td>{{ student.email || '无' }}</td>
              <td>
                <button @click="openEditModal(student)" class="btn-secondary-small">编辑</button>
                <button @click="handleDeleteSingle(student)" class="btn-danger-small">删除</button>
              </td>
            </tr>
            <tr v-if="filteredStudents.length === 0">
              <td :colspan="9" style="text-align: center;">没有找到符合条件的学生。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  <div v-if="editingStudent" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <h2>编辑学生信息</h2>
        <form @submit.prevent="handleUpdateStudent">
          <div class="form-grid">
            <div class="form-group">
              <label>学号</label>
              <input v-model="editingStudent.stu_no" type="text" required />
            </div>
            <div class="form-group">
              <label>姓名</label>
              <input v-model="editingStudent.stu_name" type="text" required />
            </div>
            <div class="form-group">
              <label>年级</label>
              <input v-model="editingStudent.grade" type="text" required />
            </div>
            <div class="form-group">
              <label>专业</label>
              <select v-model="editingStudent.major">
                <option v-for="major in majors" :key="major.major_id" :value="major.major_name">
                  {{ major.major_name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>手机号</label>
              <input v-model="editingStudent.phone" type="text" />
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input v-model="editingStudent.email" type="email" />
            </div>
            <div class="form-group">
              <label>新密码 (留空则不修改)</label>
              <input v-model="editingStudent.password" type="password" placeholder="输入新密码" />
            </div>
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

const addStudentError = ref(null);
const addStudentSuccess = ref(null);

const listError = ref(null);
const listSuccess = ref(null);

const students = ref([]);
const majors = ref([]);
const error = ref(null);
const success = ref(null);

const searchQuery = ref('');
const selectedGrade = ref('');
const selectedMajor = ref('');


const selectedStudentIds = ref(new Set());

const editingStudent = ref(null);
const editError = ref(null);

const newStudent = ref({
  stu_no: '',
  stu_name: '',
  password: '',
  grade: '',
  phone: '',
  major: '',
  email: '',
});


const selectedFile = ref(null);
const isUploading = ref(false);
const bulkResults = ref(null);
const bulkError = ref(null);


const fetchData = async () => {
  listError.value = null;

  try {
    const studentsRes = await api.getStudents();
    students.value = studentsRes.data;
  } catch (err) {
    console.error("Failed to fetch students:", err);
    error.value = "加载学生列表失败。";
  }

  try {
    const majorsRes = await api.getMajors();
    majors.value = majorsRes.data;
  } catch (err) {
    console.error("Failed to fetch majors:", err);
    if (!error.value) {
      error.value = "加载专业列表失败，筛选功能可能受影响。";
    }
  }
};

onMounted(fetchData);

const filteredStudents = computed(() => {
  let result = students.value;
  if (searchQuery.value) {
    const lowerCaseQuery = searchQuery.value.toLowerCase();
    result = result.filter(student =>
      student.stu_name.toLowerCase().includes(lowerCaseQuery) ||
      student.stu_no.toLowerCase().includes(lowerCaseQuery)
    );
  }
  if (selectedGrade.value) {
    result = result.filter(student => student.grade === selectedGrade.value);
  }
  if (selectedMajor.value) {
    result = result.filter(student => student.major_name === selectedMajor.value);
  }
  return result;
});

const uniqueGrades = computed(() => {
  const grades = students.value.map(s => s.grade);
  return [...new Set(grades)].sort();
});

const isAllFilteredSelected = computed(() => {
  const filteredIds = filteredStudents.value.map(s => s.stu_id);
  if (filteredIds.length === 0) return false;
  return filteredIds.every(id => selectedStudentIds.value.has(id));
});

watch([selectedGrade, selectedMajor], () => {
  selectedStudentIds.value.clear();
});

const openEditModal = (student) => {
  editingStudent.value = { ...student, major: student.major_name, password: '' };
  editError.value = null;
};

const handleUpdateStudent = async () => {
  if (!editingStudent.value) return;

  const studentData = { ...editingStudent.value };
  if (!studentData.password) {
    delete studentData.password;
  }

  try {
    await api.updateStudent(studentData.stu_id, studentData);
    listSuccess.value = `学生 ${studentData.stu_name} 的信息已更新。`;
    closeEditModal();
    await fetchData(); // 刷新列表
  } catch (err) {
    console.error("Failed to update student:", err);
    editError.value = "更新失败：" + (err.response?.data?.detail || '请检查输入。');
  }
};


const closeEditModal = () => {
  editingStudent.value = null;
};

const toggleSelectAllFiltered = (event) => {
  const isChecked = event.target.checked;
  const filteredIds = filteredStudents.value.map(s => s.stu_id);
  if (isChecked) {
    filteredIds.forEach(id => selectedStudentIds.value.add(id));
  } else {
    filteredIds.forEach(id => selectedStudentIds.value.delete(id));
  }
};

const handleDeleteSingle = async (student) => {
  if (confirm(`确定要删除学生 ${student.stu_name} (学号: ${student.stu_no}) 吗？`)) {
    try {
      await api.deleteStudent(student.stu_id);
      listSuccess.value = `学生 ${student.stu_name} 已删除。`;
      await fetchData();
    } catch (err) {
      listError.value = `删除失败: ${err.response?.data?.detail || '服务器错误'}`;
    }
  }
};

const handleDeleteSelected = async () => {
  if (selectedStudentIds.value.size === 0) {
    alert("请先选择要删除的学生。");
    return;
  }
  if (confirm(`确定要删除选中的 ${selectedStudentIds.value.size} 名学生吗？`)) {
    try {
      const idsToDelete = Array.from(selectedStudentIds.value);
      await api.bulkDeleteStudents(idsToDelete);
      listSuccess.value = `成功删除 ${idsToDelete.length} 名学生。`;
      selectedStudentIds.value.clear();
      await fetchData();
    } catch (err) {
      listError.value = `批量删除失败: ${err.response?.data?.error || '服务器错误'}`;
    }
  }
};


const addStudent = async () => {
  addStudentError.value = null;
  addStudentSuccess.value = null;
  listSuccess.value = null; // 同时清理其他区域的消息，避免混淆
  listError.value = null
  try {
    // 1. 发送API请求，并接收返回的数据
    const response = await api.createStudent(newStudent.value);

    // 2. 使用API返回的数据中的姓名来显示成功信息
    const createdStudentName = response.data.stu_name;
    addStudentSuccess.value = `学生 ${createdStudentName} 添加成功！`;

    // 3. 清空表单
    Object.keys(newStudent.value).forEach(key => newStudent.value[key] = '');

    // 4. 重新加载学生列表
    fetchData();
  } catch (err) {
    console.error("Failed to add student:", err);
    addStudentError.value = "添加失败：" + (err.response?.data?.detail || '请检查输入。');
  }
};


const handleFileChange = (event) => {
  selectedFile.value = event.target.files[0];
  bulkResults.value = null; // 清除旧的结果
  bulkError.value = null;
};

const handleDownloadTemplate = async () => {
  try {
    const response = await api.downloadStudentTemplate();
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'student_registration_template.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (err) {
    console.error("Failed to download template:", err);
    bulkError.value = "下载模板失败。";
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
    const response = await api.bulkRegisterStudents(selectedFile.value);

    if (response && response.data && typeof response.data.success_count !== 'undefined') {
      bulkResults.value = response.data;
    } else {
      success.value = "批量操作已提交。";
    }

  } catch (err) {
    console.error("Failed to bulk register:", err);
    bulkError.value = "上传失败：" + (err.response?.data?.error || '服务器发生未知错误。');

  } finally {
    console.log("Refreshing data after bulk upload attempt...");
    await fetchData();

    isUploading.value = false;
    if (document.querySelector('input[type=file]')) {
      document.querySelector('input[type=file]').value = '';
    }
    selectedFile.value = null;
  }
};

onMounted(fetchData);
</script>

<style scoped>
.management-container { display: flex; flex-direction: column; gap: 40px; }
.form-card, .list-card { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.form-group { display: flex; flex-direction: column; }
label { margin-bottom: 8px; font-weight: 600; }
input[type="text"], input[type="password"], input[type="email"], select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.btn-submit { margin-top: 20px; padding: 12px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
.btn-submit:disabled { background-color: #a0cffc; cursor: not-allowed; }
.error-message, .success-message { text-align: center; margin-top: 15px; padding: 10px; border-radius: 4px; }
.error-message { color: #dc3545; background-color: #f8d7da; }
.success-message { color: #155724; background-color: #d4edda; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
th { background-color: #f2f2f2; }
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
.filters select { padding: 8px; min-width: 150px; }
.bulk-actions-bar { background-color: #e9f5ff; border: 1px solid #b3d9ff; border-radius: 6px; padding: 10px 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
.bulk-actions-bar span { font-weight: 600; color: #0056b3; }
.btn-danger { padding: 8px 15px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-danger-small { padding: 5px 10px; font-size: 0.8em; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; }
table th:first-child, table td:first-child { width: 40px; text-align: center; }
.filters { display: flex; gap: 20px; align-items: flex-end; }
.filters input[type="text"] { padding: 8px; }
.btn-secondary-small {
  padding: 5px 10px; font-size: 0.8em; background-color: #6c757d;
  color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px;
}
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.6); display: flex;
  justify-content: center; align-items: center; z-index: 1000;
}
.modal-content {
  background: white; padding: 30px 40px; border-radius: 8px;
  width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto;
}
.modal-actions {
  display: flex; justify-content: flex-end; gap: 15px; margin-top: 30px;
}
</style>