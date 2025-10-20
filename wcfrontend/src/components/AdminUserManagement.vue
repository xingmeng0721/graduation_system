<template>
  <div class="user-management">
    <h1>管理员用户管理</h1>

    <!-- 添加用户表单 -->
    <div class="form-container">
      <input v-model="newUser.admin_name" placeholder="姓名" />
      <input v-model="newUser.admin_username" placeholder="用户名" />
      <input v-model="newUser.admin_password" type="password" placeholder="密码" />
      <button @click="addUser">添加用户</button>
    </div>

    <!-- 用户列表 -->
    <div class="user-list">
      <h2>用户列表</h2>
      <ul>
        <li v-for="user in users" :key="user.admin_id">
          <span>ID: {{ user.admin_id }}</span>
          <span>姓名: {{ user.admin_name }}</span>
          <span>用户名: {{ user.admin_username }}</span>
          <button @click="deleteUser(user.admin_id)">删除</button>
        </li>
      </ul>
       <p v-if="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// API 的基础 URL
const API_URL = 'http://127.0.0.1:6184/api/admin-users/';

// 响应式状态
const users = ref([]);
const newUser = ref({
  admin_name: '',
  admin_username: '',
  admin_password: ''
});
const error = ref(null);

// 获取所有用户
const fetchUsers = async () => {
  try {
    const response = await axios.get(API_URL);
    users.value = response.data;
    error.value = null;
  } catch (e) {
    console.error('获取用户列表失败:', e);
    error.value = '无法加载用户数据，请检查后端服务是否运行。';
  }
};

// 添加新用户
const addUser = async () => {
  if (!newUser.value.admin_name || !newUser.value.admin_username || !newUser.value.admin_password) {
    alert('所有字段均为必填项！');
    return;
  }
  try {
    await axios.post(API_URL, newUser.value);
    // 清空表单
    newUser.value = { admin_name: '', admin_username: '', admin_password: '' };
    // 重新获取列表
    await fetchUsers();
  } catch (e) {
    console.error('添加用户失败:', e);
    alert('添加用户失败，可能是用户名已存在。');
  }
};

// 删除用户
const deleteUser = async (id) => {
  if (confirm(`确定要删除 ID 为 ${id} 的用户吗？`)) {
    try {
      await axios.delete(`${API_URL}${id}/`);
      await fetchUsers();
    } catch (e) {
      console.error('删除用户失败:', e);
      alert('删除用户失败。');
    }
  }
};

// 组件挂载时获取用户列表
onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
.user-management {
  max-width: 800px;
  margin: 0 auto;
  font-family: sans-serif;
}
.form-container {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ccc;
  border-radius: 5px;
}
.form-container input {
  margin-right: 10px;
  padding: 8px;
}
.user-list ul {
  list-style: none;
  padding: 0;
}
.user-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}
.user-list li span {
  margin-right: 15px;
}
</style>