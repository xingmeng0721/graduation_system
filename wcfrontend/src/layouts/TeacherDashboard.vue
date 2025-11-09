<template>
  <el-container class="dashboard-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
      <div class="sidebar-header">
        <h3 v-if="!isCollapse">教师仪表盘</h3>
        <span v-else class="header-icon">教</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/teacher/dashboard/profile">
          <el-icon><User /></el-icon>
          <template #title>个人信息</template>
        </el-menu-item>

        <el-menu-item index="/teacher/dashboard/select-team">
          <el-icon><UserFilled /></el-icon>
          <template #title>选择指导团队</template>
        </el-menu-item>

        <el-menu-item index="/teacher/dashboard/history">
          <el-icon><Document /></el-icon>
          <template #title>历史活动结果</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button
          type="danger"
          :icon="SwitchButton"
          @click="handleLogout"
          :class="{ 'collapse-btn': isCollapse }"
        >
          <span v-if="!isCollapse">退出登录</span>
        </el-button>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部工具栏 -->
      <el-header class="header">
        <el-button
          circle
          :icon="isCollapse ? Expand : Fold"
          @click="toggleCollapse"
        />
        <div class="header-title">{{ pageTitle }}</div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  User, UserFilled, Document,
  Fold, Expand, SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const pageTitleMap = {
  '/teacher/dashboard/profile': '个人信息',
  '/teacher/dashboard/select-team': '选择指导团队',
  '/teacher/dashboard/history': '历史活动结果'
}

const pageTitle = computed(() => pageTitleMap[route.path] || '教师仪表盘')

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    localStorage.removeItem('teacherAccessToken')
    localStorage.removeItem('teacherRefreshToken')
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
}

.sidebar {
  background-color: #2c3e50;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-icon {
  font-size: 20px;
  font-weight: 600;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background-color: #2c3e50;
}

.sidebar-menu :deep(.el-menu-item) {
  color: #bdc3c7;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: #34495e;
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #409eff;
  color: #fff;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-footer .el-button {
  width: 100%;
}

.collapse-btn {
  padding: 12px;
}

.main-container {
  background-color: #f5f7fa;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 20px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.main-content {
  padding: 20px;
}
</style>