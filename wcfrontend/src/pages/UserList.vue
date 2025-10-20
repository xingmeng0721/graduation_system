<template>
  <div>
    <h1>管理员数据</h1>
    <div v-if="loading" class="loading">正在加载...</div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <table v-if="users.length > 0">
      <thead>
        <tr>
          <th>ID</th>
          <th>名称</th>
          <th>用户名</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.admin_id">
          <td>{{ user.admin_id }}</td>
          <td>{{ user.admin_name }}</td>
          <td>{{ user.admin_username }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const users = ref([]);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const response = await api.getUsers();
    users.value = response.data;
  } catch (err) {
    error.value = "无法加载用户数据。";
    console.error(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
</style>