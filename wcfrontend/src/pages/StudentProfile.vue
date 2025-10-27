<template>
  <div class="student-profile">
    <h2>个人信息管理</h2>
    <div v-if="loading" class="loading-spinner">加载中...</div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <!-- 个人信息表单 -->
    <div v-if="student" class="profile-card">
      <h3>欢迎，{{ student.stu_name }}</h3>

      <!-- 学号，不可修改 -->
      <p><strong>学号：</strong>{{ student.stu_no }}</p>

      <!-- 可编辑的字段：年级，专业，手机号 -->
      <div>
        <label for="grade">年级：</label>
        <input v-if="isEditing" v-model="student.grade" type="text" id="grade" />
        <span v-else>{{ student.grade }}</span>
      </div>

      <div>
        <label for="major">专业：</label>
        <input v-if="isEditing" v-model="student.major_name" type="text" id="major" />
        <span v-else>{{ student.major_name || '未分配' }}</span>
      </div>

      <div>
        <label for="phone">手机号：</label>
        <input v-if="isEditing" v-model="student.phone" type="text" id="phone" />
        <span v-else>{{ student.phone || '未提供' }}</span>
      </div>

      <!-- 修改和保存按钮 -->
      <button v-if="!isEditing" @click="editProfile" class="btn-edit">修改</button>
      <button v-if="isEditing" @click="saveProfile" class="btn-save">保存</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const student = ref(null);
const loading = ref(true);
const error = ref(null);
const isEditing = ref(false);  // 控制是否进入编辑状态

onMounted(async () => {
  try {
    const response = await api.getStudentProfile();
    student.value = response.data;  // 获取学生信息并赋值
  } catch (err) {
    console.error('获取学生信息失败:', err);
    error.value = '无法加载个人信息，请稍后再试。';
  } finally {
    loading.value = false;
  }
});

// 进入编辑模式
const editProfile = () => {
  isEditing.value = true;  // 修改状态设为 true，显示输入框
};

// 保存修改的个人信息
const saveProfile = async () => {
  try {
    await api.updateStudentProfile(student.value);  // 假设你已经有 updateStudentProfile API 用于更新数据
    isEditing.value = false;  // 保存后退出编辑状态
  } catch (err) {
    console.error('保存学生信息失败:', err);
    error.value = '保存个人信息失败，请稍后再试。';
  }
};
</script>

<style scoped>
.student-profile {
  padding: 20px;
  background-color: #fff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  max-width: 600px;
  margin: 20px auto;
}

.profile-card {
  padding: 20px;
}

.error-message {
  color: red;
  text-align: center;
}

.loading-spinner {
  text-align: center;
  font-size: 18px;
  color: #34495e;
  padding: 50px;
}

input {
  padding: 8px;
  margin: 5px 0;
  width: 100%;
  border-radius: 4px;
  border: 1px solid #ccc;
}

button {
  padding: 10px 20px;
  margin: 10px 0;
  cursor: pointer;
  border: none;
  border-radius: 4px;
}

.btn-edit {
  background-color: #2ecc71;
  color: white;
}

.btn-save {
  background-color: #3498db;
  color: white;
}
</style>
