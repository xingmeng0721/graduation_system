<template>
  <el-container class="dashboard-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
      <div class="sidebar-header">
        <h3 v-if="!isCollapse">管理后台</h3>
        <span v-else class="header-icon">管</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard/users">
          <el-icon><User /></el-icon>
          <template #title>管理员数据</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/register">
          <el-icon><UserFilled /></el-icon>
          <template #title>注册新用户</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/students">
          <el-icon><Reading /></el-icon>
          <template #title>学生管理</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/teachers">
          <el-icon><Briefcase /></el-icon>
          <template #title>教师管理</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/mutual-selection">
          <el-icon><Setting /></el-icon>
          <template #title>毕业设计配置</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/auto-assignment">
          <el-icon><Connection /></el-icon>
          <template #title>自动分配</template>
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
  User, UserFilled, Reading, Briefcase, Setting, Connection,
  Fold, Expand, SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const pageTitleMap = {
  '/dashboard/users': '管理员数据',
  '/dashboard/register': '注册新用户',
  '/dashboard/students': '学生管理',
  '/dashboard/teachers': '教师管理',
  '/dashboard/mutual-selection': '毕业设计配置',
  '/dashboard/auto-assignment': '自动分配'
}

const pageTitle = computed(() => pageTitleMap[route.path] || '管理后台')

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

    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
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