<!-- src/components/TeacherTeamDetailDialog.vue -->
<template>
  <el-dialog
    v-model="visible"
    :title="`${teamData?.group_name} - 详细信息`"
    width="900px"
    @close="handleClose"
  >
    <div v-loading="loading">
      <!-- 项目信息 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header>
          <h4 style="margin: 0;">项目信息</h4>
        </template>
        <el-descriptions :column="1" border v-if="teamData">
          <el-descriptions-item label="项目标题">
            {{ teamData.project_title || '未填写' }}
          </el-descriptions-item>
          <el-descriptions-item label="项目简介">
            <!-- ✅ 优化：允许横向滚动 -->
            <div style="max-height: 300px; overflow: auto; white-space: pre-wrap; word-break: break-word;">
              {{ teamData.project_description || '未填写' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 志愿导师信息 -->
      <el-card shadow="never" style="margin-bottom: 16px;" v-if="teamData">
        <template #header>
          <h4 style="margin: 0;">学生选择的志愿导师</h4>
        </template>
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="preference-item">
              <span class="preference-label">第一志愿</span>
              <span class="preference-value">
                {{ teamData.preferred_advisor_1?.teacher_name || '未选择' }}
              </span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="preference-item">
              <span class="preference-label">第二志愿</span>
              <span class="preference-value">
                {{ teamData.preferred_advisor_2?.teacher_name || '未选择' }}
              </span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="preference-item">
              <span class="preference-label">第三志愿</span>
              <span class="preference-value">
                {{ teamData.preferred_advisor_3?.teacher_name || '未选择' }}
              </span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 团队成员详细信息 -->
      <el-card shadow="never">
        <template #header>
          <h4 style="margin: 0;">团队成员 ({{ teamData?.member_count }}人)</h4>
        </template>
        <el-table
          :data="teamData?.members"
          border
          stripe
          v-if="teamData"
        >
          <el-table-column label="姓名" width="100">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                {{ row.stu_name }}
                <el-tag v-if="row.is_captain" type="warning" size="small">队长</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="stu_no" label="学号" width="120" />
          <el-table-column prop="grade" label="年级" width="80" />
          <el-table-column prop="major_name" label="专业" min-width="120" />
          <el-table-column label="联系电话" width="120">
            <template #default="{ row }">
              <el-text v-if="row.phone" copyable size="small">
                {{ row.phone }}
              </el-text>
              <span v-else style="color: #909399;">未填写</span>
            </template>
          </el-table-column>
          <el-table-column label="电子邮箱" min-width="150">
            <template #default="{ row }">
              <el-text v-if="row.email" copyable size="small">
                {{ row.email }}
              </el-text>
              <span v-else style="color: #909399;">未填写</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api'

const props = defineProps({
  modelValue: Boolean,
  groupId: [Number, String]
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const loading = ref(false)
const teamData = ref(null)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.groupId) {
    fetchTeamDetail()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const fetchTeamDetail = async () => {
  loading.value = true
  try {
    const response = await api.teacherGetGroupDetail(props.groupId)
    teamData.value = response.data
  } catch (error) {
    ElMessage.error('获取团队详情失败')
    console.error('Failed to fetch team detail:', error)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  teamData.value = null
}
</script>

<style scoped>
.preference-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.preference-label {
  font-size: 14px;
  color: #909399;
}

.preference-value {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}
</style>