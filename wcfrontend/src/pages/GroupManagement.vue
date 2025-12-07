<template>
  <div class="page-container">
    <div class="page-header">
      <h2>活动监控与小组管理</h2>
      <p class="page-description">在此页面监控所有活动，管理学生分组并对活动进行预分配模拟。</p>
    </div>

    <!-- 1. 活动选择 -->
    <el-card class="select-card" shadow="never">
      <template #header>
        <div class="card-header"><span>活动列表</span></div>
      </template>
      <el-menu
        :default-active="String(selectedEventId)"
        class="event-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item
          v-for="event in allEvents"
          :key="event.event_id"
          :index="String(event.event_id)"
        >
          {{ event.event_name }}
          <span style="color: #999; font-size: 13px">
            （{{ getEventStatus(event) }}）
          </span>
        </el-menu-item>
      </el-menu>
    </el-card>

    <div v-if="loading" class="loading-container" v-loading="loading">加载活动数据中...</div>

    <div v-if="selectedEventId && eventData" class="management-content">
      <!-- 2. 统计卡片 -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="总参与学生" :value="eventData.stats.total_students" /></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="已组队学生" :value="eventData.stats.grouped_students" /></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="未组队学生" :value="eventData.stats.ungrouped_students" /></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><el-statistic title="已创建团队" :value="eventData.stats.total_groups" /></el-card></el-col>
      </el-row>

      <!-- 3. 顶部操作按钮 -->
      <div class="action-header">
        <el-button
          type="primary"
          :icon="MagicStick"
          :loading="isAutoAssigning"
          @click="handleAutoAssign"
          size="large"
        >
          {{ isAutoAssigning ? '预分配中...' : '运行预分配模拟' }}
        </el-button>
        <el-button :icon="View" @click="showAssignmentDialog = true" size="large">
          查看（预）分配结果
        </el-button>
        <el-button :icon="DataAnalysis" @click="showMatchMatrix = true" size="large">
          查看完整匹配矩阵
        </el-button>
      </div>

      <!-- 4. 管理布局 -->
      <div class="management-layout">

        <!-- 左侧：已创建团队 (摘要) -->
        <div class="panel">
          <el-card shadow="never" class="full-height-card">
            <template #header>
              <div class="card-header">
                <span>已创建团队 ({{ eventData.groups_list.length }})</span>
                <div>
                  <el-button type="primary" :icon="Plus" @click="handleCreateGroup" size="small">新建团队</el-button>
                  <el-button link type="primary" size="small" @click="showGroupDialog = true">查看全部详情</el-button>
                </div>
              </div>
            </template>

            <el-table :data="eventData.groups_list.slice(0, 5)" stripe>
              <el-table-column prop="group_name" label="团队名称" width="100" show-overflow-tooltip />
              <!-- ✅ 新增：项目标题摘要 -->
              <el-table-column prop="project_title" label="项目标题" min-width="120" show-overflow-tooltip>
                <template #default="{ row }">{{ row.project_title || '-' }}</template>
              </el-table-column>
              <el-table-column label="队长" prop="captain.stu_name" width="80" />
              <el-table-column label="人数" prop="member_count" align="center" width="60" />
            </el-table>
            <div v-if="eventData.groups_list.length > 5" class="table-hint">
              仅显示前5个团队，点击“查看全部详情”以查看完整信息...
            </div>
          </el-card>
        </div>

        <!-- 右侧：未组队学生 (摘要) -->
        <div class="panel">
          <el-card shadow="never" class="full-height-card">
            <template #header>
              <div class="card-header">
                <span>未组队学生 ({{ eventData.stats.ungrouped_students }})</span>
                <el-button link type="primary" size="small" @click="showStudentDialog = true">查看全部详情</el-button>
              </div>
            </template>

            <el-table :data="eventData.ungrouped_students_list.slice(0, 6)" stripe>
              <el-table-column prop="stu_name" label="姓名" width="90" />
              <el-table-column prop="major_name" label="专业" show-overflow-tooltip />
              <el-table-column prop="internship_location" label="实习地点" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.internship_location">{{ row.internship_location }}</span>
                  <span v-else style="color: #ccc">未填写</span>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="eventData.ungrouped_students_list.length > 6" class="table-hint">
              仅显示部分学生，点击“查看全部详情”以查看完整信息...
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- ✅ 弹窗：团队管理 (含项目简介 + 详细成员信息) -->
    <el-dialog v-model="showGroupDialog" title="已创建团队列表" width="900px" destroy-on-close>
      <div class="dialog-scroll">
        <el-table :data="eventData?.groups_list || []" stripe border row-key="group_id">

          <!-- ✅ 展开行：显示项目简介 + 成员详细信息 -->
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="expand-wrapper">

                <!-- 1. 项目详细信息板块 -->
                <div class="expand-section">
                  <h4 class="section-title">📂 项目信息</h4>
                  <div class="project-info-grid">
                     <div class="info-item">
                        <span class="label">项目标题：</span>
                        <span class="value">{{ row.project_title || '未填写' }}</span>
                     </div>
                     <div class="info-item full-width">
                        <span class="label">项目简介：</span>
                        <div class="value description-box">
                            {{ row.project_description || '暂无项目简介' }}
                        </div>
                     </div>
                  </div>
                </div>

                <!-- 2. 团队成员详情板块 -->
                <div class="expand-section">
                  <h4 class="section-title">👥 团队成员详情 ({{ row.member_count }}人)</h4>
                  <el-table :data="row.members" size="small" border>
                    <el-table-column label="角色" width="70" align="center">
                      <template #default="{ row: member }">
                          <el-tag v-if="member.stu_id === row.captain?.stu_id" type="danger" size="small">队长</el-tag>
                          <el-tag v-else type="info" size="small">成员</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="stu_name" label="姓名" width="90" />
                    <el-table-column prop="phone" label="联系电话" width="120" />
                    <el-table-column prop="email" label="电子邮箱" min-width="150" show-overflow-tooltip />
                    <el-table-column prop="internship_location" label="实习地点" min-width="120" show-overflow-tooltip>
                      <template #default="{ row: member }">
                        {{ member.internship_location || '未填写' }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>

              </div>
            </template>
          </el-table-column>

          <!-- 主表格列 -->
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="group_name" label="团队名称" width="140" show-overflow-tooltip />

          <!-- ✅ 新增：主表也显示项目标题 -->
          <el-table-column prop="project_title" label="项目标题" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
                <span v-if="row.project_title">{{ row.project_title }}</span>
                <span v-else style="color:#ccc; font-style: italic;">未命名</span>
            </template>
          </el-table-column>

          <el-table-column label="队长" prop="captain.stu_name" width="100" />
          <el-table-column label="人数" prop="member_count" align="center" width="70" />

          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditGroup(row)">编辑</el-button>
              <el-popconfirm title="确定删除此团队？" @confirm="handleDeleteGroup(row)">
                <template #reference><el-button size="small" type="danger" link>删除</el-button></template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- ✅ 弹窗：未组队学生 (含详细信息) -->
    <el-dialog v-model="showStudentDialog" title="未组队学生详情" width="850px" destroy-on-close>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <span style="color: #666; font-size: 14px;">共 {{ filteredStudents.length }} 位学生</span>
        <el-input
            v-model="studentSearchQuery"
            placeholder="搜索姓名或学号"
            clearable
            size="default"
            :prefix-icon="Search"
            style="width: 250px;"
        />
      </div>

      <div class="dialog-scroll">
        <el-table :data="filteredStudents" stripe border height="500">
          <el-table-column prop="stu_name" label="姓名" width="100" fixed />
          <el-table-column prop="stu_no" label="学号" width="120" />
          <el-table-column prop="major_name" label="专业" width="150" show-overflow-tooltip />
          <el-table-column prop="phone" label="联系电话" width="130" />
          <el-table-column prop="email" label="电子邮箱" min-width="180" show-overflow-tooltip />
          <el-table-column prop="internship_location" label="实习地点" min-width="150" show-overflow-tooltip>
             <template #default="{ row }">
                <el-tag v-if="row.internship_location" size="small" type="info" effect="plain">
                    {{ row.internship_location }}
                </el-tag>
                <span v-else style="color: #ccc; font-size: 12px;">未填写</span>
             </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <GroupEditDialog v-if="eventData" v-model="isGroupDialogVisible" :group-data="editingGroup" :event-data="eventData" @submitted="refreshEventData" />
    <MatchMatrixDialog v-model="showMatchMatrix" :event-id="selectedEventId" />
    <AssignmentResultsDialog v-model="showAssignmentDialog" :event-id="selectedEventId" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, DataAnalysis, Plus, View, Search } from '@element-plus/icons-vue'
import api from '../services/api'
import GroupEditDialog from '../components/GroupEditDialog.vue'
import MatchMatrixDialog from '../components/MatchMatrixDialog.vue'
import AssignmentResultsDialog from '../components/AssignmentResultsDialog.vue'

const allEvents = ref([])
const selectedEventId = ref(null)
const eventData = ref(null)
const loading = ref(false)
const isAutoAssigning = ref(false)
const showMatchMatrix = ref(false)
const isGroupDialogVisible = ref(false)
const editingGroup = ref(null)
const showAssignmentDialog = ref(false)
const showGroupDialog = ref(false)
const showStudentDialog = ref(false)
const studentSearchQuery = ref('')

const filteredStudents = computed(() => {
  if (!eventData.value) return []
  const q = studentSearchQuery.value?.toLowerCase?.() || ''
  return eventData.value.ungrouped_students_list.filter(
    s => s.stu_name.toLowerCase().includes(q) || s.stu_no.includes(q)
  )
})

const fetchAllEvents = async () => {
  try {
    const res = await api.getMutualSelectionEvents()
    allEvents.value = res.data
    if (allEvents.value.length > 0) {
      const latest = [...allEvents.value].sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      )[0]

      selectedEventId.value = latest.event_id
      handleEventChange(latest.event_id)
    }
  } catch {
    ElMessage.error('获取活动列表失败')
  }
}

const handleMenuSelect = id => {
  selectedEventId.value = Number(id)
  handleEventChange(selectedEventId.value)
}

const handleEventChange = async id => {
  if (!id) {
    eventData.value = null
    return
  }
  loading.value = true
  try {
    const res = await api.getEventManagementInfo(id)
    eventData.value = res.data
  } catch {
    ElMessage.error('获取活动详情失败')
  } finally {
    loading.value = false
  }
}

const refreshEventData = async () => {
  if (selectedEventId.value) await handleEventChange(selectedEventId.value)
}

const handleCreateGroup = () => {
  editingGroup.value = null
  isGroupDialogVisible.value = true
}
const handleEditGroup = g => {
  editingGroup.value = g
  isGroupDialogVisible.value = true
}
const handleDeleteGroup = async g => {
  try {
    await api.adminDeleteGroup(g.group_id)
    ElMessage.success('团队删除成功！')
    await refreshEventData()
  } catch (e) {
    ElMessage.error(`删除失败: ${e.response?.data?.error || '未知错误'}`)
  }
}

const handleAutoAssign = async () => {
  try {
    await ElMessageBox.confirm('这将执行一次预分配模拟，结果将以弹窗形式展示，不会覆盖正式数据。确定吗？', '确认预分配', { type: 'info' })
    isAutoAssigning.value = true
    const res = await api.autoAssign(selectedEventId.value)
    ElMessage.success(res.data.message || '预分配完成！')
    showAssignmentDialog.value = true
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '预分配失败')
  } finally {
    isAutoAssigning.value = false
  }
}

const getEventStatus = e => {
  const now = new Date()
  const s = new Date(e.stu_start_time)
  const end1 = new Date(e.stu_end_time)
  const end2 = new Date(e.tea_end_time)
  if (now > end1 && now > end2) return '已结束'
  if (now >= s) return '进行中'
  return '未开始'
}

onMounted(fetchAllEvents)
</script>

<style scoped>
.page-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
  font-size: 14px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.event-menu {
  border-right: none;
}

.stats-row {
  margin-bottom: 20px;
}

.action-header {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.management-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.full-height-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-hint {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 10px 0;
  background: #fcfcfc;
  border-top: 1px solid #ebeef5;
}

.dialog-scroll {
  max-height: 60vh;
  overflow-y: auto;
}

/* 滚动条美化 */
.dialog-scroll::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.dialog-scroll::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}
.dialog-scroll::-webkit-scrollbar-track {
  background-color: #f5f7fa;
}

/* 展开行样式 */
.expand-wrapper {
  padding: 10px 20px;
  background-color: #f9faFC;
  border-radius: 4px;
}

.expand-section {
  margin-bottom: 20px;
}
.expand-section:last-child {
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  border-left: 3px solid #409eff;
  padding-left: 8px;
}

.project-info-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.info-item {
    width: 100%;
    margin-bottom: 5px;
}

.info-item .label {
    font-weight: bold;
    color: #606266;
    margin-right: 5px;
}

.info-item .value {
    color: #303133;
}

.description-box {
    margin-top: 5px;
    padding: 10px;
    background: #fff;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    line-height: 1.5;
    white-space: pre-wrap;
    font-size: 13px;
}

@media (max-width: 1200px) {
  .management-layout {
    grid-template-columns: 1fr;
  }
}
</style>