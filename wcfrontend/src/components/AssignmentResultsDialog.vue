<template>
  <el-dialog
    v-model="visible"
    title="预分配模拟结果"
    width="90%"
    top="5vh"
    @close="handleClose"
    destroy-on-close
  >
    <div v-loading="loading">
      <el-alert
        title="此结果仅为模拟，不会被保存。您可以在此弹窗内进行手动微调，以观察不同分配方案的效果。"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 20px;"
      />
      <el-table :data="assignments" stripe border max-height="calc(80vh - 100px)">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="group.group_name" label="团队名称" />
        <el-table-column label="队长" prop="group.captain.stu_name" />
        <el-table-column label="成员数" prop="group.member_count" align="center" />
        <el-table-column prop="teacher.teacher_name" label="预分配导师" />
        <el-table-column prop="score" label="匹配得分" align="center">
            <template #default="{ row }">
                <el-tag :type="row.score > 10 ? 'success' : row.score > 0 ? 'primary' : 'info'">
                {{ row.score }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column prop="explanation" label="匹配说明" show-overflow-tooltip/>
        <el-table-column label="类型" prop="assignment_type" align="center">
          <template #default="{ row }">
            <el-tag :type="row.assignment_type === 'manual' ? 'warning' : ''">
              {{ row.assignment_type === 'auto' ? '自动' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- ✅【最终修复】在这里加上您要的手动调整功能！ -->
        <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" :icon="Edit" @click="handleManualAssign(row.group)">调整</el-button>
            </template>
        </el-table-column>

      </el-table>
       <el-empty v-if="!loading && assignments.length === 0" description="没有生成任何分配结果" />
    </div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>

    <!-- ✅【最终修复】引入调整功能所需的子弹窗 -->
    <MatchOptionsDialog
      v-model="showMatchOptions"
      :event-id="props.eventId"
      :group-id="currentGroupId"
      :group-name="currentGroupName"
      @select="handleTeacherSelected"
    />
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Edit } from '@element-plus/icons-vue';
import api from '../services/api';
import MatchOptionsDialog from './MatchOptionsDialog.vue'; // 引入子弹窗

const props = defineProps({
  modelValue: Boolean,
  eventId: [Number, String],
});
const emit = defineEmits(['update:modelValue']);

const visible = ref(false);
const loading = ref(false);
const assignments = ref([]);

// ✅【最终修复】为手动调整功能添加所需的状态
const showMatchOptions = ref(false);
const currentGroupId = ref(null);
const currentGroupName = ref('');

watch(() => props.modelValue, (val) => {
  visible.value = val;
  if (val && props.eventId) {
    fetchAssignments();
  }
});

const fetchAssignments = async () => {
  if (!props.eventId) return;
  loading.value = true;
  try {
    const response = await api.getAssignments(props.eventId);
    assignments.value = response.data;
  } catch (error) {
    ElMessage.error('获取预分配结果失败');
  } finally {
    loading.value = false;
  }
};

// ✅【最终修复】添加完整的手动调整方法
const handleManualAssign = (group) => {
  currentGroupId.value = group.group_id;
  currentGroupName.value = group.group_name;
  showMatchOptions.value = true;
};

const handleTeacherSelected = async (teacherId) => {
  try {
    await api.manualAssign(props.eventId, currentGroupId.value, teacherId);
    ElMessage.success('手动调整成功！正在刷新模拟结果...');
    // 关键：调整后立刻刷新当前弹窗内的数据
    await fetchAssignments();
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '调整失败');
  }
};

const handleClose = () => {
  emit('update:modelValue', false);
};
</script>