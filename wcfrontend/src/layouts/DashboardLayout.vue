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
        <el-menu-item index="/dashboard/profile">
          <el-icon><User /></el-icon>
          <template #title>个人信息</template>
        </el-menu-item>

        <el-divider />

        <el-menu-item-group title="用户管理">
            <el-menu-item index="/dashboard/users">
            <el-icon><Avatar /></el-icon>
            <template #title>管理员列表</template>
            </el-menu-item>

            <el-menu-item index="/dashboard/register">
            <el-icon><UserFilled /></el-icon>
            <template #title>注册新用户</template>
            </el-menu-item>
        </el-menu-item-group>

        <el-divider />

        <el-menu-item-group title="教学管理">
            <el-menu-item index="/dashboard/students">
            <el-icon><Reading /></el-icon>
            <template #title>学生管理</template>
            </el-menu-item>

            <el-menu-item index="/dashboard/teachers">
            <el-icon><Briefcase /></el-icon>
            <template #title>教师管理</template>
            </el-menu-item>
        </el-menu-item-group>

        <el-divider />

        <el-menu-item-group title="活动与分配">
            <el-menu-item index="/dashboard/mutual-selection">
                <el-icon><Setting /></el-icon>
                <template #title>互选活动配置</template>
            </el-menu-item>

            <!-- ✅【核心美化】移除子菜单，将两个功能作为一级菜单项 -->
            <el-menu-item index="/dashboard/group-management">
                <el-icon><Monitor /></el-icon>
                <template #title>小组与预分配</template>
            </el-menu-item>

            <el-menu-item index="/dashboard/assignment-results">
                <el-icon><Finished /></el-icon>
                <template #title>最终分配结果</template>
            </el-menu-item>
        </el-menu-item-group>

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
  User, UserFilled, Reading, Briefcase, Setting, Avatar,
  Fold, Expand, SwitchButton, Monitor, Finished
} from '@element-plus/icons-vue' // ✅ 引入 Avatar 图标，移除 Connection

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const pageTitleMap = {
  '/dashboard/profile': '个人信息',
  '/dashboard/users': '管理员数据',
  '/dashboard/register': '注册新用户',
  '/dashboard/students': '学生管理',
  '/dashboard/teachers': '教师管理',
  '/dashboard/mutual-selection': '互选活动配置',
  '/dashboard/group-management': '小组与预分配管理',
  '/dashboard/assignment-results': '最终分配结果'
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
  box-shadow: 2px 0 6px rgba(0, 21, 41, .35);
  z-index: 10;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}

.header-icon {
  font-size: 20px;
  font-weight: 600;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background-color: transparent; /* ✅ 透明背景以适应父容器 */
  overflow-y: auto;
  overflow-x: hidden;
}

/* ✅ 美化：为 el-menu-item-group 添加标题样式 */
.sidebar-menu :deep(.el-menu-item-group__title) {
  padding-left: 20px !important;
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
  line-height: normal;
}

/* ✅ 美化：分割线样式 */
.el-divider {
  background-color: rgba(255, 255, 255, 0.1);
  margin: 0;
}

.sidebar-menu :deep(.el-menu-item) {
  color: #bdc3c7;
  height: 50px;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: #34495e;
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #409EFF;
  color: #fff;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.sidebar-footer .el-button {
  width: 100%;
}

.collapse-btn {
  padding: 12px;
}

.main-container {
  background-color: #f0f2f5; /* ✅ 使用更柔和的背景色 */
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
  padding: 24px;
}
</style>