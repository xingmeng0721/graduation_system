<template>
  <div>
    <h1>学生管理</h1>
    <div class="management-container">
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
          </div>
          <div v-if="error" class="error-message">{{ error }}</div>
          <div v-if="success" class="success-message">{{ success }}</div>
          <button type="submit" class="btn-submit">确认添加</button>
        </form>
      </div>

      <!-- 学生列表 -->
      <div class="list-card">
        <h2>学生列表</h2>
        <table>
          <thead>
            <tr>
              <th>学号</th>
              <th>姓名</th>
              <th>年级</th>
              <th>专业</th>
              <th>分组</th>
              <th>组长</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in students" :key="student.stu_id">
              <td>{{ student.stu_no }}</td>
              <td>{{ student.stu_name }}</td>
              <td>{{ student.grade }}</td>
              <td>{{ student.major_name || 'N/A' }}</td>
              <td>{{ student.group_name || 'N/A' }}</td>
              <td>{{ student.is_gleader ? '是' : '否' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const students = ref([]);
const newStudent = ref({
  stu_no: '',
  stu_name: '',
  password: '',
  grade: '',
  phone: '',
  major: '',
});
const error = ref(null);
const success = ref(null);

const fetchData = async () => {
  try {
    const studentsRes = await api.getStudents();
    students.value = studentsRes.data;
  } catch (err) {
    console.error("Failed to fetch students:", err);
    error.value = "加载学生列表失败。";
  }
};

const addStudent = async () => {
  error.value = null;
  success.value = null;
  try {
    await api.createStudent(newStudent.value);
    success.value = `学生 ${newStudent.value.stu_name} 添加成功！`;
    // 清空表单
    Object.keys(newStudent.value).forEach(key => newStudent.value[key] = '');
    newStudent.value.is_gleader = false;
    // 重新加载学生列表
    fetchData();
  } catch (err) {
    console.error("Failed to add student:", err);
    error.value = "添加失败：" + (err.response?.data?.detail || '请检查输入。');
  }
};

onMounted(fetchData);
</script>

<style scoped>
.management-container { display: flex; flex-direction: column; gap: 40px; }
.form-card, .list-card { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.form-group { display: flex; flex-direction: column; }
.checkbox-group { flex-direction: row; align-items: center; gap: 10px; }
label { margin-bottom: 8px; font-weight: 600; }
input[type="text"], input[type="password"], select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
input[type="checkbox"] { width: auto; }
.btn-submit { margin-top: 20px; padding: 12px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
.error-message, .success-message { text-align: center; margin-top: 15px; padding: 10px; border-radius: 4px; }
.error-message { color: #dc3545; background-color: #f8d7da; }
.success-message { color: #155724; background-color: #d4edda; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
th { background-color: #f2f2f2; }
</style>