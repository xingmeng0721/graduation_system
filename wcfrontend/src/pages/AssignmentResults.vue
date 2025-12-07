<template>
  <div class="page-container">
    <div class="page-header">
      <h2>最终分配与发布</h2>
      <p class="page-description">在此页面查看并发布 **已结束活动** 的最终分配结果，并可进行最后的手动微调。</p>
    </div>

    <!-- 1. 活动选择 -->
    <el-card class="select-card" shadow="never">
      <template #header>
        <div class="card-header"><span>已结束的活动列表</span></div>
      </template>

      <!-- 左侧菜单式活动列表 -->
      <el-menu
        class="event-menu"
        :default-active="String(selectedEventId)"
        @select="handleMenuSelect"
      >
        <el-menu-item
          v-for="event in finishedEvents"
          :key="event.event_id"
          :index="String(event.event_id)"
        >
          {{ event.event_name }}
          <span style="font-size: 12px; color: #999">（结束于 {{ formatDate(event.tea_end_time) }}）</span>
        </el-menu-item>
      </el-menu>
    </el-card>

    <div v-if="selectedEventId">
      <!-- 2. 顶部统计 & 操作按钮 -->
      <el-row :gutter="24" style="margin-bottom: 24px;">
        <el-col :span="14"> <!-- 调整宽度以容纳更多按钮 -->
          <el-row :gutter="16">
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="总团队数" :value="assignmentStats.total_groups"><template #prefix><el-icon color="#409eff"><UserFilled /></el-icon></template></el-statistic></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="已分配" :value="assignmentStats.assigned_count"><template #prefix><el-icon color="#67c23a"><Select /></el-icon></template></el-statistic></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="志愿匹配" :value="assignmentStats.preference_matched"><template #prefix><el-icon color="#e6a23c"><Star /></el-icon></template></el-statistic></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="随机分配" :value="assignmentStats.random_assigned"><template #prefix><el-icon color="#f56c6c"><Opportunity /></el-icon></template></el-statistic></el-card></el-col>
          </el-row>
        </el-col>
        <el-col :span="10"> <!-- 调整宽度 -->
            <div class="button-group">
                <el-button type="primary" :icon="MagicStick" :loading="isAutoAssigning" @click="handleAutoAssign" size="default">重新分配</el-button>
                <el-button :icon="Refresh" @click="fetchAssignments" size="default">刷新</el-button>

                <!-- ✅ 新增导出按钮 -->
                <el-button type="warning" :icon="Download" :disabled="!hasAssignments" @click="handleExportExcel" size="default">导出Excel</el-button>

                <el-button :icon="DataAnalysis" @click="showMatchMatrix = true" size="default">匹配矩阵</el-button>
                <el-button type="success" :icon="Check" :disabled="!hasAssignments" @click="handlePublish" size="default">发布结果</el-button>
            </div>
        </el-col>
      </el-row>

      <!-- 3. 结果表格 -->
      <el-card class="table-card" shadow="never">
        <template #header><div class="card-header"><span>最终分配结果</span></div></template>

        <el-table :data="assignments" v-loading="loading" stripe border row-key="id">

          <!-- 展开行 -->
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="expand-wrapper">
                <div class="expand-section">
                  <h4 class="section-title">📌 项目简介</h4>
                  <div class="description-box">
                    {{ row.group.project_description || '暂无项目简介' }}
                  </div>
                </div>

                <div class="expand-section">
                  <h4 class="section-title">👥 成员详细信息</h4>
                  <el-table
                    :data="row.group.members"
                    size="small"
                    border
                    style="width: 100%"
                    :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
                  >
                    <el-table-column label="角色" width="80" align="center">
                      <template #default="{ row: member }">
                        <el-tag v-if="member.is_captain" type="danger" size="small" effect="dark">队长</el-tag>
                        <el-tag v-else type="info" size="small">成员</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="stu_name" label="姓名" width="100" />
                    <el-table-column prop="major_name" label="专业" width="150" />
                    <el-table-column prop="phone" label="手机号" width="130" />
                    <el-table-column prop="email" label="邮箱" min-width="180" />
                    <el-table-column prop="internship_location" label="实习地点" min-width="150">
                      <template #default="{ row: member }">
                        <span v-if="member.internship_location">{{ member.internship_location }}</span>
                        <span v-else style="color: #ccc;">未填写</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column type="index" label="#" width="50" />
          <el-table-column label="项目名称" min-width="200" show-overflow-tooltip>
             <template #default="{ row }">
                <span class="project-title-text">{{ row.group.project_title || row.group.group_name }}</span>
                <span v-if="!row.group.project_title" style="font-size: 12px; color: #999; margin-left: 5px;">(无项目名，显示组名)</span>
             </template>
          </el-table-column>

          <el-table-column label="队长" prop="group.captain.stu_name" width="120">
             <template #default="{ row }">
                <el-icon><User /></el-icon> {{ row.group.captain?.stu_name }}
             </template>
          </el-table-column>

          <el-table-column label="人数" prop="group.member_count" align="center" width="70">
             <template #default="{ row }"><el-tag size="small" effect="plain">{{ row.group.member_count }}</el-tag></template>
          </el-table-column>

          <el-table-column prop="teacher.teacher_name" label="指导教师" width="120">
             <template #default="{ row }">
                <span style="font-weight: bold; color: #409eff;">{{ row.teacher?.teacher_name }}</span>
             </template>
          </el-table-column>

          <el-table-column label="匹配得分" align="center" width="100">
            <template #default="{ row }">
                <el-tag :type="getScoreTagType(row.score)" effect="light"><strong>{{ row.score }}</strong></el-tag>
            </template>
          </el-table-column>

          <el-table-column label="匹配说明" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
                <div class="explanation-tags">
                    <el-tag v-for="tag in getExplanationTags(row.explanation)" :key="tag.text" :type="tag.type" effect="plain" size="small">
                        {{ tag.text }}
                    </el-tag>
                </div>
            </template>
          </el-table-column>

          <el-table-column label="类型" prop="assignment_type" align="center" width="90">
            <template #default="{ row }">
              <el-tag :type="row.assignment_type === 'manual' ? 'warning' : 'success'" effect="plain">
                {{ row.assignment_type === 'auto' ? '自动' : '手动' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" :icon="Edit" @click="handleManualAssign(row.group)">调整</el-button>
            </template>
          </el-table-column>

        </el-table>
        <el-empty v-if="!loading && assignments.length === 0" description="暂无分配记录" />
      </el-card>
    </div>

    <!-- 弹窗 -->
    <MatchOptionsDialog v-model="showMatchOptions" :event-id="selectedEventId" :group-id="currentGroupId" :group-name="currentGroupName" @select="handleTeacherSelected" />
    <MatchMatrixDialog v-model="showMatchMatrix" :event-id="selectedEventId" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { MagicStick, Refresh, Check, Edit, Download } from '@element-plus/icons-vue'; // 引入 Download
import { UserFilled, Select, Star, Opportunity, DataAnalysis, User } from '@element-plus/icons-vue';
import api from '../services/api';
import MatchOptionsDialog from '../components/MatchOptionsDialog.vue';
import MatchMatrixDialog from '../components/MatchMatrixDialog.vue';
import * as XLSX from 'xlsx'; // 引入 xlsx

const route = useRoute();
const finishedEvents = ref([]);
const selectedEventId = ref(null);
const assignments = ref([]);
const loading = ref(false);
const isAutoAssigning = ref(false);
const showMatchOptions = ref(false);
const currentGroupId = ref(null);
const currentGroupName = ref('');
const showMatchMatrix = ref(false);

const hasAssignments = computed(() => assignments.value.length > 0);
const assignmentStats = ref({
    total_groups: 0,
    assigned_count: 0,
    preference_matched: 0,
    random_assigned: 0,
});

const getScoreTagType = (score) => {
    if (score >= 15) return 'success';
    if (score >= 5) return 'primary';
    if (score > 0) return 'warning';
    return 'info';
};

const handleMenuSelect = async (key) => {
  selectedEventId.value = Number(key)
  await handleEventChange()
}

const getExplanationTags = (explanation) => {
    if (!explanation) return [];
    if (!explanation.includes(' + ')) {
        let type = 'info';
        if (explanation.includes('手动')) type = 'warning';
        return [{ text: explanation, type: type }];
    }
    return explanation.split(' + ').map(part => {
        let type = 'primary';
        if (part.includes('教师')) type = 'warning';
        if (part.includes('学生')) type = 'success';
        return { text: part, type: type };
    });
};

const fetchFinishedEvents = async () => {
  try {
    const response = await api.getMutualSelectionEvents();
    const now = new Date();
    finishedEvents.value = response.data.filter(event => {
        const stuEndTime = new Date(event.stu_end_time);
        const teaEndTime = new Date(event.tea_end_time);
        return now > stuEndTime && now > teaEndTime;
    });
    if (finishedEvents.value.length > 0) {
      selectedEventId.value = finishedEvents.value[0].event_id
      await fetchAssignments()
    }
  } catch (error) { ElMessage.error('获取已结束的活动列表失败'); }
};

const handleEventChange = async () => {
  assignments.value = [];
  await fetchAssignments();
};

const fetchAssignments = async () => {
  if (!selectedEventId.value) return;
  loading.value = true;
  try {
    const response = await api.getAssignments(selectedEventId.value);
    assignments.value = response.data;
    assignmentStats.value.total_groups = assignments.value.length;
    assignmentStats.value.assigned_count = assignments.value.filter(a => a.teacher).length;
    assignmentStats.value.preference_matched = assignments.value.filter(a => a.score > 0).length;
    assignmentStats.value.random_assigned = assignments.value.filter(a => a.score === 0).length;
  } catch (error) { ElMessage.error('获取分配结果失败'); }
  finally { loading.value = false; }
};

// ✅ 导出 Excel 功能实现
const handleExportExcel = () => {
  if (!assignments.value || assignments.value.length === 0) {
    ElMessage.warning('暂无数据可导出');
    return;
  }

  try {
    const exportData = [];
    assignments.value.forEach((item) => {
      const group = item.group;
      const teacher = item.teacher;
      const members = group.members || [];
      const scoreTag = item.score > 0 ? `${item.score}分` : '随机/无志愿';
      const assignType = item.assignment_type === 'auto' ? '自动分配' : '手动调整';

      // 展开成员，每一行代表一个学生
      members.forEach((member) => {
        exportData.push({
          '项目名称': group.project_title || group.group_name,
          '项目简介': group.project_description || '无',
          '团队名称': group.group_name,
          '指导教师': teacher ? teacher.teacher_name : '未分配',
          '教师工号': teacher ? teacher.teacher_no : '-',
          '匹配类型': assignType,
          '匹配得分': scoreTag,
          '学生姓名': member.stu_name,
          '学号': member.stu_no,
          '角色': member.is_captain ? '队长' : '成员',
          '专业': member.major_name || '-',
          '手机号': member.phone || '-',
          '邮箱': member.email || '-',
          '实习地点': member.internship_location || '-'
        });
      });
    });

    const ws = XLSX.utils.json_to_sheet(exportData);

    // 设置列宽
    const wscols = [
      { wch: 25 }, { wch: 40 }, { wch: 15 }, { wch: 10 }, { wch: 10 },
      { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 12 }, { wch: 8 },
      { wch: 15 }, { wch: 13 }, { wch: 20 }, { wch: 15 }
    ];
    ws['!cols'] = wscols;

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "最终分配结果");

    // 获取活动名称作为文件名
    const eventName = finishedEvents.value.find(e => e.event_id === selectedEventId.value)?.event_name || '分配结果';
    const timeStr = new Date().toISOString().slice(0, 10);
    XLSX.writeFile(wb, `${eventName}_最终分配结果_${timeStr}.xlsx`);

    ElMessage.success('导出成功！');
  } catch (error) {
    console.error(error);
    ElMessage.error('导出失败，请检查数据');
  }
};

const handleAutoAssign = async () => {
  try {
    await ElMessageBox.confirm('这将覆盖现有的分配结果，确定要对这个已结束的活动重新执行最终分配吗？', '确认最终分配', { type: 'warning' });
    isAutoAssigning.value = true;
    const response = await api.autoAssign(selectedEventId.value);
    ElMessage.success(response.data.message || '分配完成');
    if (response.data) {
        assignmentStats.value = { ...assignmentStats.value, ...response.data };
    }
    await fetchAssignments();
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.error || '分配失败');
  } finally { isAutoAssigning.value = false; }
};

const handleManualAssign = (group) => {
  currentGroupId.value = group.group_id;
  currentGroupName.value = group.project_title || group.group_name;
  showMatchOptions.value = true;
};

const handleTeacherSelected = async (teacherId) => {
  try {
    await api.manualAssign(selectedEventId.value, currentGroupId.value, teacherId);
    ElMessage.success('手动调整成功');
    await fetchAssignments();
  } catch (error) { ElMessage.error(error.response?.data?.error || '调整失败'); }
};

const handlePublish = async () => {
  try {
    await ElMessageBox.confirm('发布后结果将对所有师生可见，且不可更改。确定要发布吗？', '！！！最终确认！！！', { type: 'error' });
    const response = await api.publishAssignments(selectedEventId.value);
    ElMessage.success(response.data.message || '发布成功');
    await fetchAssignments();
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.error || '发布失败');
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('zh-CN');
};

onMounted(fetchFinishedEvents);
</script>

<style scoped>
.page-container {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100%;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
.select-card, .table-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}
.select-card {
  margin-bottom: 24px;
}
.table-card {
  margin-top: 24px;
}
.card-header {
  font-weight: 600;
  font-size: 16px;
}
.button-group {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  height: 100%;
}
.expand-wrapper {
  padding: 10px 20px 20px 20px;
  background-color: #f8f9fa;
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
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 8px;
  line-height: 1;
}
.description-box {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  background-color: #fff;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  white-space: pre-wrap;
}
.project-title-text {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}
.explanation-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}
.event-menu {
  border-right: none;
}
</style>