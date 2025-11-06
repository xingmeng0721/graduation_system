<template>
  <div class="page-container">
    <div class="page-header">
      <h2>管理员数据</h2>
    </div>

    <el-card class="table-card" shadow="never">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40">
          <Loading />
        </el-icon>
        <p>正在加载...</p>
      </div>

      <!-- 错误提示 -->
      <el-alert
        v-if="error"
        :title="error"
        type="error"
        :closable="false"
        show-icon
      />

      <!-- 数据表格 -->
      <el-table
        v-if="!loading && !error"
        :data="users"
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa' }"
      >
        <el-table-column prop="admin_id" label="ID" width="80" />
        <el-table-column prop="admin_name" label="名称" min-width="150" />
        <el-table-column prop="admin_username" label="用户名" min-width="150" />
      </el-table>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && !error && users.length === 0"
        description="暂无管理员数据"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import api from '../services/api'

const users = ref([])
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const response = await api.getUsers()
    users.value = response.data
  } catch (err) {
    error.value = '无法加载用户数据，请稍后重试'
    console.error(err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-container {
  max-width: 1200px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.table-card {
  border-radius: 8px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.loading-container p {
  margin-top: 16px;
  font-size: 14px;
}
</style>