<template>
  <div class="page-container">
    <!-- 1. 页面标题与状态 -->
    <div class="page-header">
      <div class="header-left">
        <h2>我的毕业设计团队</h2>
        <!-- 状态标签 -->
        <el-tag
          v-if="dashboard.has_active_event"
          :type="dashboard.is_editable ? 'success' : 'warning'"
          size="large"
          effect="dark"
          style="margin-left: 12px;"
        >
          {{ dashboard.is_editable ? '学生互选进行中' : '导师选拔与匹配中' }}
        </el-tag>
      </div>

      <div class="header-right" v-if="dashboard.has_active_event">
         <span class="time-info">
            <el-icon><Timer /></el-icon>
            {{ dashboard.is_editable ? ' 志愿填报截止: ' : ' 最终结果公布: ' }}
            <strong>{{ formatDate(dashboard.is_editable ? dashboard.active_event_info.end_time : dashboard.active_event_info.tea_end_time) }}</strong>
         </span>
      </div>
    </div>

    <!-- 2. 全局状态提示横幅 (当处于不可编辑阶段时显示) -->
    <div v-if="dashboard.has_active_event && !dashboard.is_editable" class="status-alert">
      <el-alert
        title="学生互选阶段已结束"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>当前处于<strong>导师选拔与系统匹配阶段</strong>。您的团队信息已锁定，无法进行修改、加入或退出操作。请耐心等待最终结果公布。</p>
        </template>
      </el-alert>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在加载信息...</p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />

    <!-- 有活动时的内容 -->
    <template v-if="dashboard.has_active_event && !loading">

      <!-- 场景一：已加入团队 -->
      <div v-if="dashboard.my_team_info" class="team-container">
        <!-- 团队信息卡片 -->
        <el-card class="team-info-card" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="header-title-group">
                <h3>{{ dashboard.my_team_info.group_name }}</h3>
                <!-- 锁定图标 -->
                <el-tag v-if="!dashboard.is_editable" type="info" size="small" effect="plain" round>
                  <el-icon><Lock /></el-icon> 已锁定
                </el-tag>
              </div>
              <div>
                <!-- 查看完整信息按钮 -->
                <el-button
                  type="primary"
                  link
                  @click="viewTeamDetail(dashboard.my_team_info.group_id)"
                >
                  查看完整信息
                </el-button>
                <!-- 编辑团队信息按钮（仅队长且可编辑时可见） -->
                <el-button
                  v-if="dashboard.is_captain && dashboard.is_editable"
                  type="primary"
                  link
                  @click="openTeamEditModal"
                >
                  编辑团队信息
                </el-button>
              </div>
            </div>
          </template>

          <!-- 项目信息 -->
          <div class="info-section">
            <div class="section-header">
              <h4>项目信息</h4>
            </div>
            <div class="section-content">
              <p class="project-title">{{ dashboard.my_team_info.project_title || '尚未填写项目标题' }}</p>
              <p class="project-desc">
                {{ dashboard.my_team_info.project_description_short || '尚未填写项目简介' }}
              </p>
            </div>
          </div>

          <el-divider />

          <!-- 志愿导师 -->
          <div class="info-section">
            <div class="section-header">
              <h4>志愿导师</h4>
              <!-- 根据状态显示不同文字 -->
              <el-button type="primary" link @click="openAdvisorModal">
                {{ (dashboard.is_captain && dashboard.is_editable) ? '选择/修改' : '查看详情' }}
              </el-button>
            </div>
            <div class="section-content">
              <el-row :gutter="16">
                <el-col :span="8" v-for="i in 3" :key="i">
                  <div class="advisor-item">
                    <span class="advisor-label">第{{['一','二','三'][i-1]}}志愿</span>
                    <span class="advisor-name">{{ dashboard.my_team_info[`preferred_advisor_${i}`]?.teacher_name || '未选择' }}</span>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>

          <el-divider />

          <!-- 最终指导老师 -->
          <div class="info-section">
            <div class="section-header">
              <h4>最终指导老师</h4>
            </div>
            <div class="section-content">
              <el-tag v-if="dashboard.my_team_info.advisor" type="success" size="large" effect="plain">
                {{ dashboard.my_team_info.advisor.teacher_name }}
              </el-tag>
              <el-tag v-else type="info" size="large" effect="plain">
                {{ dashboard.is_editable ? '待管理员分配' : '正在匹配中...' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 成员管理卡片 -->
        <el-card class="members-card" shadow="never">
          <template #header>
            <div class="card-header">
              <h3>团队成员 ({{ dashboard.my_team_info.member_count }})</h3>
            </div>
          </template>

          <div class="members-list">
            <div
              v-for="member in dashboard.my_team_info.members"
              :key="member.stu_id"
              class="member-item"
            >
              <div class="member-info">
                <el-avatar :size="40">{{ member.stu_name.charAt(0) }}</el-avatar>
                <div class="member-details">
                  <span class="member-name">{{ member.stu_name }}</span>
                  <span class="member-no">{{ member.stu_no }}</span>
                </div>
              </div>


<div class="member-actions">
                <!-- 如果是队长，显示标签 -->
                <el-tag v-if="member.is_captain" type="warning" size="small">队长</el-tag>

                <!-- ✅ 新增：转让队长按钮 -->
                <!-- 显示条件：我是队长 && 对方不是队长 && 处于可编辑状态 -->
                <el-button
                  v-if="dashboard.is_captain && !member.is_captain && dashboard.is_editable"
                  type="warning"
                  size="small"
                  link
                  :icon="Switch"
                  @click="handleTransferCaptain(member)"
                >
                  转让队长
                </el-button>

                <!-- 移除按钮 -->
                <el-button
                  v-if="dashboard.is_captain && !member.is_captain && dashboard.is_editable"
                  type="danger"
                  size="small"
                  link
                  @click="handleRemoveMember(member)"
                >
                  移除
                </el-button>
              </div>
            </div>
          </div>

          <!-- 底部操作栏：仅在可编辑时显示 -->
          <template #footer v-if="dashboard.is_editable">
            <div class="card-footer">
              <el-button
                v-if="dashboard.is_captain"
                type="primary"
                @click="openInviteModal"
              >
                添加新成员
              </el-button>
              <el-button
                v-if="dashboard.is_captain"
                type="danger"
                @click="handleDisbandTeam"
              >
                解散团队
              </el-button>
              <el-button
                v-else
                type="danger"
                @click="handleLeaveTeam"
              >
                退出团队
              </el-button>
            </div>
          </template>
        </el-card>
      </div>

      <!-- 场景二：未加入团队 -->
      <div v-if="!dashboard.my_team_info" class="no-team-container">

        <!-- 只有在可编辑状态下，才显示创建/加入表单 -->
        <template v-if="dashboard.is_editable">
          <el-card class="action-card" shadow="never">
            <template #header>
              <h3>创建我的团队</h3>
            </template>
            <p>迈出第一步，成为团队的领导者！</p>
            <el-form @submit.prevent="handleCreateTeam" style="margin-top: 20px;">
              <el-form-item label="团队名称">
                <el-input
                  v-model="newTeam.group_name"
                  placeholder="一个独特且响亮的名称"
                  clearable
                />
              </el-form-item>
              <el-button type="primary" native-type="submit" style="width: 100%;">
                确认创建
              </el-button>
            </el-form>
          </el-card>

          <el-card class="action-card" shadow="never">
            <template #header>
              <h3>或加入现有团队</h3>
            </template>
            <p>寻找志同道合的伙伴，加入他们吧！</p>
            <el-button
              type="primary"
              @click="openAllTeamsModal"
              style="width: 100%; margin-top: 20px;"
            >
              查找所有团队
            </el-button>
          </el-card>
        </template>

        <!-- 如果不可编辑（错过时间或已截止），显示提示 -->
        <template v-else>
            <el-card class="action-card" shadow="never" style="grid-column: span 2; text-align: center; padding: 40px;">
                <el-empty description="本次互选活动的学生组队阶段已结束。">
                    <template #image>
                        <el-icon :size="80" color="#909399"><Timer /></el-icon>
                    </template>
                    <p style="margin-top: 20px; color: #606266;">您未在规定时间内加入任何团队。</p>
                    <p style="color: #909399;">请等待最终结果公布或联系管理员咨询。</p>
                </el-empty>
            </el-card>
        </template>

      </div>
    </template>

    <!-- 场景三：无活动 -->
    <el-card v-if="!dashboard.has_active_event && !loading" class="no-activity-card" shadow="never">
      <el-empty description="当前没有正在进行的互选活动">
        <template #image>
          <el-icon :size="80" color="#909399"><InfoFilled /></el-icon>
        </template>
        <p style="margin: 20px 0;">您可以查看过去活动的结果</p>
        <el-button type="primary" @click="$router.push('/student/dashboard/history')">
          查看历史活动
        </el-button>
      </el-empty>
    </el-card>

    <!-- 编辑项目信息对话框 -->
    <el-dialog
      v-model="isTeamEditModalVisible"
      title="编辑团队信息"
      width="600px"
    >
      <el-form @submit.prevent="handleUpdateTeamInfo" label-width="100px">
        <el-form-item label="团队名称">
          <el-input v-model="editTeam.group_name" placeholder="团队名称"/>
        </el-form-item>
        <el-form-item label="项目标题">
          <el-input v-model="editTeam.project_title" placeholder="为你们的项目起个名字" />
        </el-form-item>
        <el-form-item label="项目简介">
          <el-input
            v-model="editTeam.project_description"
            type="textarea"
            :rows="4"
            placeholder="详细描述你们的项目目标和内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="isTeamEditModalVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateTeamInfo">保存团队信息</el-button>
      </template>
    </el-dialog>

    <!-- 选择/查看导师对话框 -->
    <el-dialog
        v-model="isAdvisorModalVisible"
        :title="dashboard.is_captain && dashboard.is_editable ? '选择志愿导师' : '查看可选导师'"
        width="1000px"
        :close-on-click-modal="false"
    >
      <div v-loading="modalLoading" class="advisor-selection-container">
        <!-- 提示信息 -->
        <el-alert
            v-if="dashboard.is_captain && dashboard.is_editable"
            title="请为您的团队选择三位志愿导师（按优先级顺序）"
            type="info"
            :closable="false"
            style="margin-bottom: 20px;"
        />
        <el-alert
            v-else-if="!dashboard.is_editable"
            title="志愿选择已截止，以下为您提交的最终志愿"
            type="warning"
            :closable="false"
            style="margin-bottom: 20px;"
        />

        <!-- 顶部志愿栏 -->
        <div class="preferences-cards">
          <el-card v-for="level in [1, 2, 3]" :key="level"
            :class="['preference-card', { 'has-selection': preferences[`preferred_advisor_${level}`] }]" shadow="hover">
            <div class="preference-card-header">
              <h4>第{{ ['一', '二', '三'][level - 1] }}志愿</h4>
              <el-tag :type="['danger', 'warning', 'success'][level - 1]" size="small">志愿{{ level }}</el-tag>
            </div>
            <div class="preference-card-body">
              <div v-if="preferences[`preferred_advisor_${level}`]" class="selected-advisor">
                <div class="advisor-info-selected">
                  <el-avatar :size="50">{{ getAdvisorName(preferences[`preferred_advisor_${level}`])?.charAt(0) }}</el-avatar>
                  <div class="advisor-details-selected">
                    <span class="advisor-name-large">{{ getAdvisorName(preferences[`preferred_advisor_${level}`]) }}</span>
                    <!-- 仅在可编辑模式下显示取消按钮 -->
                    <el-button v-if="dashboard.is_captain && dashboard.is_editable" type="danger" size="small" link @click="preferences[`preferred_advisor_${level}`] = null">
                      取消选择
                    </el-button>
                  </div>
                </div>
              </div>
              <div v-else class="empty-selection">
                <el-icon :size="40" color="#c0c4cc"><User /></el-icon>
                <span class="empty-text">未选择导师</span>
              </div>
            </div>
          </el-card>
        </div>

        <el-divider />

        <!-- 导师列表 (只在可编辑时或者为了查看详情时显示) -->
        <div class="advisor-list-section">
          <div class="list-header">
            <h4>{{ dashboard.is_editable ? '可选导师列表' : '所有导师列表' }}</h4>
            <el-input v-model="advisorSearchQuery" placeholder="按姓名或研究方向搜索" clearable :prefix-icon="Search" style="width: 300px;" />
          </div>

          <el-scrollbar max-height="400px">
            <el-card v-for="advisor in filteredAdvisors" :key="advisor.teacher_id"
              :class="['advisor-card', { 'is-selected': isAdvisorSelected(advisor.teacher_id) }]" shadow="hover">
              <div class="advisor-card-content">
                <div class="advisor-left">
                  <el-avatar :size="45">{{ advisor.teacher_name.charAt(0) }}</el-avatar>
                  <div class="advisor-info-main">
                    <h5 class="advisor-name-main">{{ advisor.teacher_name }}</h5>
                    <p class="advisor-research">{{ advisor.research_direction || '暂无研究方向信息' }}</p>
                  </div>
                </div>
                <div class="advisor-right">
                  <el-button type="primary" link size="small" @click="showAdvisorDetails(advisor)">详细资料</el-button>

                  <!-- 只有在可编辑模式下，才显示选择按钮 -->
                  <el-button-group v-if="dashboard.is_captain && dashboard.is_editable">
                    <el-button
                      :type="preferences.preferred_advisor_1 === advisor.teacher_id ? 'danger' : 'default'"
                      size="small"
                      @click="setPreference(1, advisor.teacher_id)"
                      :disabled="isAdvisorSelected(advisor.teacher_id) && preferences.preferred_advisor_1 !== advisor.teacher_id">
                      一志愿
                    </el-button>
                    <el-button
                      :type="preferences.preferred_advisor_2 === advisor.teacher_id ? 'warning' : 'default'"
                      size="small"
                      @click="setPreference(2, advisor.teacher_id)"
                      :disabled="isAdvisorSelected(advisor.teacher_id) && preferences.preferred_advisor_2 !== advisor.teacher_id">
                      二志愿
                    </el-button>
                    <el-button
                      :type="preferences.preferred_advisor_3 === advisor.teacher_id ? 'success' : 'default'"
                      size="small"
                      @click="setPreference(3, advisor.teacher_id)"
                      :disabled="isAdvisorSelected(advisor.teacher_id) && preferences.preferred_advisor_3 !== advisor.teacher_id">
                      三志愿
                    </el-button>
                  </el-button-group>
                </div>
              </div>
            </el-card>
            <el-empty v-if="filteredAdvisors.length === 0" description="没有找到匹配的导师" />
          </el-scrollbar>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-custom">
          <!-- 只有在可编辑模式下才显示保存按钮 -->
          <template v-if="dashboard.is_captain && dashboard.is_editable">
            <el-alert
              v-if="!preferences.preferred_advisor_1 || !preferences.preferred_advisor_2 || !preferences.preferred_advisor_3"
              title="提示：建议选择全部三个志愿以提高成功率" type="warning" :closable="false" show-icon
              style="flex: 1; margin-right: 16px;" />
            <el-button @click="isAdvisorModalVisible = false" size="large">取消</el-button>
            <el-button type="primary" @click="handleUpdateAdvisors" size="large"
              :disabled="!preferences.preferred_advisor_1 && !preferences.preferred_advisor_2 && !preferences.preferred_advisor_3">
              保存志愿选择
            </el-button>
          </template>
          <!-- 非编辑模式/非队长只显示关闭 -->
          <el-button v-else @click="isAdvisorModalVisible = false" type="primary" size="large" style="width: 100%;">
            关闭
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 导师详情对话框 -->
    <el-dialog
      v-model="showAdvisorDetail"
      :title="`${advisorDetail?.teacher_name} - 导师详情`"
      width="600px"
    >
      <el-descriptions v-if="advisorDetail" :column="1" border>
        <el-descriptions-item label="研究方向">
          {{ advisorDetail.research_direction || '未填写' }}
        </el-descriptions-item>
        <el-descriptions-item label="联系邮箱">
          {{ advisorDetail.email || '未填写' }}
        </el-descriptions-item>
        <el-descriptions-item label="联系电话">
          {{ advisorDetail.phone || '未填写' }}
        </el-descriptions-item>
        <el-descriptions-item label="个人简介">
          <div class="introduction-box">
            {{ advisorDetail.introduction || '未填写' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 添加新成员对话框 -->
    <el-dialog
      v-model="isInviteModalVisible"
      title="添加新成员"
      width="600px"
    >
      <el-input
        v-model="teammateSearchQuery"
        placeholder="按姓名或专业搜索..."
        clearable
        style="margin-bottom: 16px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div v-if="modalLoading" class="loading-container">
        <el-icon class="is-loading" :size="30"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <el-scrollbar v-else-if="filteredTeammates.length > 0" max-height="400px">
        <div
          v-for="student in filteredTeammates"
          :key="student.stu_id"
          class="teammate-item"
        >
          <div class="teammate-info">
            <span class="teammate-name">{{ student.stu_name }}</span>
            <span class="teammate-major">{{ student.major_name }}</span>
          </div>
          <el-button type="primary" size="small" @click="handleAddMember(student)">
            添加
          </el-button>
        </div>
      </el-scrollbar>

      <el-empty v-else description="没有找到匹配的学生" />
    </el-dialog>

    <!-- 浏览所有团队对话框 -->
    <el-dialog
      v-model="isAllTeamsModalVisible"
      title="加入一个团队"
      width="700px"
    >
      <div v-if="modalLoading" class="loading-container">
        <el-icon class="is-loading" :size="30"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <el-scrollbar v-else-if="allTeams.length > 0" max-height="500px">
        <el-card
          v-for="team in allTeams"
          :key="team.group_id"
          class="team-card"
          shadow="hover"
        >
          <div class="team-card-content">
            <div class="team-card-info">
              <h4>{{ team.group_name }}</h4>
              <p>队长: {{ team.captain.stu_name }} | 成员: {{ team.member_count }}人</p>
            </div>
            <el-button type="primary" @click="handleJoinTeam(team.group_id)">
              申请加入
            </el-button>
          </div>
        </el-card>
      </el-scrollbar>

      <el-empty v-else description="当前活动还没有人创建团队" />
    </el-dialog>

    <!-- 团队详情对话框 -->
    <TeamDetailDialog
      v-model="showTeamDetail"
      :group-id="currentTeamId"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, InfoFilled, Search, User, Lock, Timer,Switch } from '@element-plus/icons-vue'
import api from '../services/api'
import TeamDetailDialog from '../components/TeamDetailDialog.vue'

// 状态定义
const loading = ref(true)
const error = ref(null)
const dashboard = ref({
  has_active_event: false,
  active_event_info: null,
  my_team_info: null,
  is_captain: false,
  is_editable: false, // 默认为 false
  phase_status: 'none'
})
const isEditingGroupName = ref(false)

// 弹窗状态
const modalLoading = ref(false)
const isAdvisorModalVisible = ref(false)
const isInviteModalVisible = ref(false)
const isAllTeamsModalVisible = ref(false)
const showAdvisorDetail = ref(false)
const showTeamDetail = ref(false)
const currentTeamId = ref(null)
const isTeamEditModalVisible = ref(false)

// 表单数据
const newTeam = ref({ group_name: '' })
const editTeam = reactive({
  group_name: '',
  project_title: '',
  project_description: ''
})
const preferences = reactive({
  preferred_advisor_1: null,
  preferred_advisor_2: null,
  preferred_advisor_3: null
})
const advisorDetail = ref(null)

// 列表数据
const availableAdvisors = ref([])
const availableTeammates = ref([])
const allTeams = ref([])
const teammateSearchQuery = ref('')
const advisorSearchQuery = ref('');

// 计算属性
const filteredAdvisors = computed(() => {
  if (!advisorSearchQuery.value) {
    return availableAdvisors.value;
  }
  const query = advisorSearchQuery.value.toLowerCase();
  return availableAdvisors.value.filter(advisor =>
    advisor.teacher_name.toLowerCase().includes(query) ||
    (advisor.research_direction && advisor.research_direction.toLowerCase().includes(query))
  );
});

const filteredTeammates = computed(() => {
  if (!teammateSearchQuery.value) return availableTeammates.value
  const query = teammateSearchQuery.value.toLowerCase()
  return availableTeammates.value.filter(
    s => s.stu_name.toLowerCase().includes(query) || s.major_name.toLowerCase().includes(query)
  )
})

// 数据获取
const fetchDashboardData = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await api.getDashboard()
    dashboard.value = response.data
    // 如果有团队信息，初始化编辑表单
    if (dashboard.value.my_team_info) {
        editTeam.group_name = dashboard.value.my_team_info.group_name
        editTeam.project_title = dashboard.value.my_team_info.project_title
        editTeam.project_description = dashboard.value.my_team_info.project_description
    }
  } catch (err) {
    error.value = '加载信息失败，请刷新页面重试'
    console.error('Dashboard fetch error:', err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboardData)

// 辅助方法
const isAdvisorSelected = (teacherId) => {
  return Object.values(preferences).includes(teacherId)
}

const getAdvisorName = (teacherId) => {
  if (!teacherId) return null
  const advisor = availableAdvisors.value.find(a => a.teacher_id === teacherId)
  return advisor ? advisor.teacher_name : '未知导师'
}

const setPreference = (level, teacherId) => {
  for (const key in preferences) {
    if (preferences[key] === teacherId) {
      preferences[key] = null
    }
  }
  preferences[`preferred_advisor_${level}`] = teacherId
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 弹窗操作
const openTeamEditModal = () => {
  const teamInfo = dashboard.value.my_team_info
  editTeam.group_name = teamInfo.group_name || ''
  editTeam.project_title = teamInfo.project_title || ''
  editTeam.project_description = teamInfo.project_description || ''
  isTeamEditModalVisible.value = true
}

const openAdvisorModal = async () => {
  advisorSearchQuery.value = '';
  const teamInfo = dashboard.value.my_team_info
  preferences.preferred_advisor_1 = teamInfo.preferred_advisor_1?.teacher_id || null
  preferences.preferred_advisor_2 = teamInfo.preferred_advisor_2?.teacher_id || null
  preferences.preferred_advisor_3 = teamInfo.preferred_advisor_3?.teacher_id || null

  isAdvisorModalVisible.value = true
  modalLoading.value = true
  try {
    if (availableAdvisors.value.length === 0) {
      const res = await api.getAvailableAdvisors()
      availableAdvisors.value = res.data
    }
  } catch (err) {
    ElMessage.error('获取导师列表失败')
    isAdvisorModalVisible.value = false
  } finally {
    modalLoading.value = false
  }
}

const openInviteModal = () => {
  isInviteModalVisible.value = true
  fetchAvailableTeammates()
}

const fetchAvailableTeammates = async () => {
  modalLoading.value = true
  teammateSearchQuery.value = ''
  try {
    const res = await api.getAvailableTeammates()
    availableTeammates.value = res.data
  } catch (err) {
    ElMessage.error('获取可添加成员列表失败')
    isInviteModalVisible.value = false
  } finally {
    modalLoading.value = false
  }
}

const openAllTeamsModal = async () => {
  isAllTeamsModalVisible.value = true
  modalLoading.value = true
  try {
    const res = await api.getAllTeamsInActiveEvent()
    allTeams.value = res.data
  } catch (err) {
    ElMessage.error('获取团队列表失败')
  } finally {
    modalLoading.value = false
  }
}

const showAdvisorDetails = (advisor) => {
  advisorDetail.value = advisor
  showAdvisorDetail.value = true
}

const viewTeamDetail = (groupId) => {
  currentTeamId.value = groupId
  showTeamDetail.value = true
}

// 业务操作
const handleCreateTeam = async () => {
  if (!validateGroupName(newTeam.value.group_name)) return
  try {
    await api.createTeam({ group_name: newTeam.value.group_name })
    ElMessage.success('团队创建成功！')
    await fetchDashboardData()
  } catch (err) {
    const errorMsg = err.response?.data?.group_name?.[0] || err.response?.data?.error || '未知错误'
    ElMessage.error(`创建失败: ${errorMsg}`)
  }
}

const handleTransferCaptain = async (member) => {
  try {
    await ElMessageBox.confirm(
      `确定要将队长权限转让给 "${member.stu_name}" 吗？\n转让后您将变成普通队员，且失去管理团队的权限。`,
      '⚠️ 慎重操作',
      {
        confirmButtonText: '确认转让',
        cancelButtonText: '取消',
        type: 'warning',
        icon: Switch
      }
    )

    // 调用 API
    const res = await api.transferCaptain(member.stu_id)
    ElMessage.success(res.data.message)

    // 刷新数据，此时页面会自动更新权限（隐藏编辑按钮等）
    await fetchDashboardData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`转让失败: ${err.response?.data?.error || '未知错误'}`)
    }
  }
}


const handleUpdateTeamInfo = async () => {
    if (!validateGroupName(editTeam.group_name)) return
  try {
    const payload = {
      group_name: editTeam.group_name,
      project_title: editTeam.project_title,
      project_description: editTeam.project_description
    }
    await api.updateMyTeam(payload)
    ElMessage.success('团队信息更新成功！')
    isTeamEditModalVisible.value = false
    await fetchDashboardData()
  } catch (err) {
    ElMessage.error(`更新失败: ${err.response?.data?.error || '请检查输入'}`)
  }
}

const handleUpdateAdvisors = async () => {
  try {
    const payload = {
      preferred_advisor_1_id: preferences.preferred_advisor_1,
      preferred_advisor_2_id: preferences.preferred_advisor_2,
      preferred_advisor_3_id: preferences.preferred_advisor_3
    }
    await api.updateMyTeam(payload)
    ElMessage.success('导师选择保存成功！')
    isAdvisorModalVisible.value = false
    await fetchDashboardData()
  } catch (err) {
    ElMessage.error(`更新失败: ${err.response?.data?.error || '请检查输入'}`)
  }
}

const validateGroupName = (name) => {
  const pattern = /^[\u4e00-\u9fa5a-zA-Z0-9_ ]{1,10}$/
  if (!name || name.trim() === '') {
    ElMessage.error('团队名称不能为空')
    return false
  }
  if (name.length > 10) {
    ElMessage.error('团队名称不能超过 10 个字符')
    return false
  }
  if (!pattern.test(name)) {
    ElMessage.error('团队名称包含非法字符，只能使用中文、英文、数字、下划线和空格')
    return false
  }
  return true
}

const handleJoinTeam = async (teamId) => {
  try {
    await ElMessageBox.confirm('确定要申请加入该团队吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    await api.joinTeam(teamId)
    ElMessage.success('成功加入团队！')
    isAllTeamsModalVisible.value = false
    await fetchDashboardData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`加入失败: ${err.response?.data?.error || '未知错误'}`)
    }
  }
}

const handleLeaveTeam = async () => {
  try {
    await ElMessageBox.confirm('您确定要退出当前团队吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await api.leaveTeam()
    ElMessage.success(res.data.message)
    await fetchDashboardData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`操作失败: ${err.response?.data?.error || '未知错误'}`)
    }
  }
}

const handleDisbandTeam = async () => {
  try {
    await ElMessageBox.confirm('警告：此操作不可逆！确定要解散您的团队吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await api.disbandTeam()
    ElMessage.success(res.data.message)
    await fetchDashboardData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`操作失败: ${err.response?.data?.error || '未知错误'}`)
    }
  }
}

const handleRemoveMember = async (member) => {
  try {
    await ElMessageBox.confirm(`确定要将成员"${member.stu_name}"移出团队吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await api.removeMember(member.stu_id)
    ElMessage.success(res.data.message)
    await fetchDashboardData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`操作失败: ${err.response?.data?.error || '未知错误'}`)
    }
  }
}

const handleAddMember = async (student) => {
  try {
    await ElMessageBox.confirm(`确定要将"${student.stu_name}"直接添加到您的团队中吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    const res = await api.addMemberByCaptain({ student_id: student.stu_id })
    ElMessage.success(res.data.message)
    await fetchAvailableTeammates()
    await fetchDashboardData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`添加失败: ${err.response?.data?.error || '未知错误'}`)
    }
  }
}
</script>

<style scoped>
.page-container {
  max-width: 1400px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header-left {
  display: flex;
  align-items: center;
}
.header-right .time-info {
  color: #606266;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.status-alert {
    margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
}

.loading-container p {
  margin-top: 16px;
}

.team-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.no-team-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.team-info-card,
.members-card,
.action-card,
.no-activity-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-title-group {
    display: flex;
    align-items: center;
    gap: 10px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.info-section {
  margin-bottom: 24px;
}

.info-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.section-content {
  color: #606266;
}

.project-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.project-desc {
  line-height: 1.6;
  color: #606266;
  margin: 0;
}

.advisor-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.advisor-label {
  font-size: 14px;
  color: #909399;
}

.advisor-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.members-list {
  max-height: 400px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.member-item:last-child {
  border-bottom: none;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.member-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.member-no {
  font-size: 13px;
  color: #909399;
}

.member-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-footer {
  display: flex;
  gap: 12px;
}

.preferences-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.preference-card {
  border-radius: 8px;
  transition: all 0.3s;
}

.preference-card.has-selection {
  border: 2px solid #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
}

.preference-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preference-card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.preference-card-body {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.selected-advisor {
  width: 100%;
}

.advisor-info-selected {
  display: flex;
  align-items: center;
  gap: 12px;
}

.advisor-details-selected {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.advisor-name-large {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.empty-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.empty-text {
  font-size: 14px;
  color: #909399;
}

.help-text {
  font-size: 12px;
  color: #c0c4cc;
}

.advisor-list-section {
  margin-top: 24px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.list-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.advisor-card {
  margin-bottom: 12px;
  border-radius: 8px;
  transition: all 0.3s;
}

.advisor-card.is-selected {
  background-color: #ecf5ff;
  border: 1px solid #b3d8ff;
}

.advisor-card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.advisor-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.advisor-info-main {
  flex: 1;
  min-width: 0;
}

.advisor-name-main {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.advisor-research {
  margin: 0;
  font-size: 14px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.advisor-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.dialog-footer-custom {
  display: flex;
  align-items: center;
  width: 100%;
}

.introduction-box {
  white-space: pre-wrap;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.teammate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.teammate-item:hover {
  background-color: #f5f7fa;
}

.teammate-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.teammate-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.teammate-major {
  font-size: 13px;
  color: #909399;
}

.team-card {
  margin-bottom: 12px;
}

.team-card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.team-card-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.team-card-info p {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

@media (max-width: 1200px) {
  .team-container {
    grid-template-columns: 1fr;
  }

  .no-team-container {
    grid-template-columns: 1fr;
  }

  .preferences-cards {
    grid-template-columns: 1fr;
  }

  .advisor-card-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .advisor-right {
    width: 100%;
    justify-content: space-between;
  }

  .dialog-footer-custom {
    flex-direction: column;
    gap: 12px;
  }

  .dialog-footer-custom .el-alert {
    margin-right: 0;
    width: 100%;
  }
}
</style>