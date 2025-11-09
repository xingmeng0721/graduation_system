<template>
  <div class="page-container">
    <div class="page-header">
      <h2>管理员列表</h2>
      <div class="header-actions">
        <el-button
          type="danger"
          :disabled="selectedUsers.length === 0"
          @click="handleBulkDelete"
        >
          批量删除 ({{ selectedUsers.length }})
        </el-button>
      </div>
    </div>

    <el-table
      :data="users"
      @selection-change="handleSelectionChange"
      v-loading="loading"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="admin_username" label="用户名" />
      <el-table-column prop="admin_name" label="姓名" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button
            type="danger"
            size="small"
            link
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../services/api'

const users = ref([])
const selectedUsers = ref([])
const loading = ref(false)

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await api.getUsers()  // ✅ 修改这里
    users.value = response.data
  } catch (error) {
    ElMessage.error('获取管理员列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(`确定要删除管理员 "${user.admin_name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.deleteAdminUser(user.admin_id)
    ElMessage.success('删除成功')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.error || '删除失败')
    }
  }
}

const handleBulkDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedUsers.value.length} 名管理员吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedUsers.value.map(user => user.admin_id)
    await api.bulkDeleteAdminUsers(ids)
    ElMessage.success(`成功删除 ${selectedUsers.value.length} 名管理员`)
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.error || '批量删除失败')
    }
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>