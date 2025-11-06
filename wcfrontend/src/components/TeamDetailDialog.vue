<!-- src/components/TeamDetailDialog.vue -->
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
            <!-- ✅ 优化：允许横向滚动，不截断内容 -->
            <div style="max-height: 300px; overflow: auto; white-space: pre-wrap; word-break: break-word;">
              {{ teamData.project_description || '未填写' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 指导老师信息 -->
      <el-card shadow="never" style="margin-bottom: 16px;" v-if="teamData?.advisor">
        <template #header>
          <h4 style="margin: 0;">指导老师</h4>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="姓名">
            {{ teamData.advisor.teacher_name }}
          </el-descriptions-item>
          <el-descriptions-item label="工号">
            {{ teamData.advisor.teacher_no }}
          </el-descriptions-item>
          <el-descriptions-item label="联系电话">
            <el-text v-if="teamData.advisor.phone" copyable>
              {{ teamData.advisor.phone }}
            </el-text>
            <span v-else>未填写</span>
          </el-descriptions-item>
          <el-descriptions-item label="电子邮箱">
            <el-text v-if="teamData.advisor.email" copyable>
              {{ teamData.advisor.email }}
            </el-text>
            <span v-else>未填写</span>
          </el-descriptions-item>
          <el-descriptions-item label="研究方向" :span="2">
            {{ teamData.advisor.research_direction || '未填写' }}
          </el-descriptions-item>
          <el-descriptions-item label="个人简介" :span="2">
            <!-- ✅ 优化：允许横向滚动 -->
            <div style="max-height: 200px; overflow: auto; white-space: pre-wrap; word-break: break-word;">
              {{ teamData.advisor.introduction || '未填写' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 团队成员信息 -->
      <el-card shadow="never">
        <template #header>
          <h4 style="margin: 0;">团队成员 ({{ teamData?.member_count }}人)</h4>
        </template>
        <el-table :data="teamData?.members" border stripe v-if="teamData">
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
    const response = await api.getGroupDetail(props.groupId)
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