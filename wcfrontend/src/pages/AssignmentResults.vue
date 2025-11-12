<template>
  <div class="page-container">
    <div class="page-header">
      <h2>最终分配与发布</h2>
      <p class="page-description">在此页面查看并发布 **已结束活动** 的最终分配结果，并可进行最后的手动微调。</p>
    </div>

    <!-- 1. 活动选择 -->
    <el-card class="select-card" shadow="never">
       <template #header><div class="card-header"><span>选择已结束的活动</span></div></template>
      <el-select v-model="selectedEventId" placeholder="请选择一个已结束的活动" size="large" style="width: 100%" filterable @change="handleEventChange">
        <el-option v-for="event in finishedEvents" :key="event.event_id" :label="`${event.event_name} (结束于 ${formatDate(event.tea_end_time)})`" :value="event.event_id" />
      </el-select>
    </el-card>

    <div v-if="selectedEventId">
      <!-- 2. 顶部统计 & 操作按钮 -->
      <el-row :gutter="24" style="margin-bottom: 24px;">
        <el-col :span="16">
          <el-row :gutter="16">
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="总团队数" :value="assignmentStats.total_groups"><template #prefix><el-icon color="#409eff"><UserFilled /></el-icon></template></el-statistic></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="已分配" :value="assignmentStats.assigned_count"><template #prefix><el-icon color="#67c23a"><Select /></el-icon></template></el-statistic></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="志愿匹配" :value="assignmentStats.preference_matched"><template #prefix><el-icon color="#e6a23c"><Star /></el-icon></template></el-statistic></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="随机分配" :value="assignmentStats.random_assigned"><template #prefix><el-icon color="#f56c6c"><Opportunity /></el-icon></template></el-statistic></el-card></el-col>
          </el-row>
        </el-col>
        <el-col :span="8">
            <div class="button-group">
                <el-button type="primary" :icon="MagicStick" :loading="isAutoAssigning" @click="handleAutoAssign" size="large">重新分配</el-button>
                <el-button :icon="Refresh" @click="fetchAssignments" size="large">刷新</el-button>
                <el-button :icon="DataAnalysis" @click="showMatchMatrix = true" size="large">匹配矩阵</el-button>
                <el-button type="success" :icon="Check" :disabled="!hasAssignments" @click="handlePublish" size="large">发布结果</el-button>
            </div>
        </el-col>
      </el-row>

      <!-- 3. 结果表格 -->
      <el-card class="table-card" shadow="never">
        <template #header><div class="card-header"><span>最终分配结果</span></div></template>
        <el-table :data="assignments" v-loading="loading" stripe border>
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="group.group_name" label="团队名称" min-width="150" show-overflow-tooltip/>
          <el-table-column label="队长" prop="group.captain.stu_name" width="120"/>
          <el-table-column label="成员数" prop="group.member_count" align="center" width="80">
             <template #default="{ row }"><el-tag size="small" effect="plain">{{ row.group.member_count }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="teacher.teacher_name" label="指导教师" width="120"/>
          <el-table-column label="匹配得分" align="center" width="100">
            <template #default="{ row }">
                <el-tag :type="getScoreTagType(row.score)" effect="light" size="large"><strong>{{ row.score }}</strong></el-tag>
            </template>
          </el-table-column>

          <!-- ✅【核心修复】美化匹配说明列 -->
          <el-table-column label="匹配说明" min-width="200">
            <template #default="{ row }">
                <div class="explanation-tags">
                    <el-tag v-for="tag in getExplanationTags(row.explanation)" :key="tag.text" :type="tag.type" effect="plain" size="small">
                        {{ tag.text }}
                    </el-tag>
                </div>
            </template>
          </el-table-column>

          <el-table-column label="类型" prop="assignment_type" align="center" width="100">
            <template #default="{ row }">
              <el-tag :type="row.assignment_type === 'manual' ? 'warning' : 'success'" effect="plain">
                {{ row.assignment_type === 'auto' ? '自动' : '手动' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
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
import { MagicStick, Refresh, Check, Edit } from '@element-plus/icons-vue';
import api from '../services/api';
import MatchOptionsDialog from '../components/MatchOptionsDialog.vue';
import MatchMatrixDialog from '../components/MatchMatrixDialog.vue';

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

// ✅【核心修复】添加一个辅助函数来决定标签颜色
const getScoreTagType = (score) => {
    if (score >= 15) return 'success'; // 强烈匹配，例如双向高志愿
    if (score >= 5) return 'primary';  // 一般匹配，例如单向志愿
    if (score > 0) return 'warning';   // 弱匹配
    return 'info';                     // 无志愿匹配（随机分配）
};

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

    if (route.query.eventId) {
        const eventIdFromQuery = parseInt(route.query.eventId);
        if (finishedEvents.value.some(e => e.event_id === eventIdFromQuery)) {
            selectedEventId.value = eventIdFromQuery;
            await fetchAssignments();
        }
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
    // ✅【风格统一】简单计算统计信息
    assignmentStats.value.total_groups = assignments.value.length;
    assignmentStats.value.assigned_count = assignments.value.filter(a => a.teacher).length;
    assignmentStats.value.preference_matched = assignments.value.filter(a => a.score > 0).length;
    assignmentStats.value.random_assigned = assignments.value.filter(a => a.score === 0).length;
  } catch (error) { ElMessage.error('获取分配结果失败'); }
  finally { loading.value = false; }
};

const handleAutoAssign = async () => {
  try {
    await ElMessageBox.confirm('这将覆盖现有的分配结果，确定要对这个已结束的活动重新执行最终分配吗？', '确认最终分配', { type: 'warning' });
    isAutoAssigning.value = true;
    const response = await api.autoAssign(selectedEventId.value);
    ElMessage.success(response.data.message || '分配完成');
    // ✅【风格统一】执行分配后也更新统计信息
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
  currentGroupName.value = group.group_name;
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
/* ✅【风格统一】 */
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
  justify-content: flex-end; /* 让按钮靠右对齐 */
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  height: 100%;
}

.explanation-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}
</style>