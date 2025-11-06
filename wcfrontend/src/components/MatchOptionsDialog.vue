<template>
  <el-dialog
    v-model="visible"
    :title="`${groupName} - 教师匹配选项`"
    width="900px"
    @close="handleClose"
  >
    <el-alert
      title="以下是根据双向志愿计算的匹配得分，分数越高表示匹配度越好"
      type="info"
      :closable="false"
      style="margin-bottom: 16px;"
    />

    <el-table
      :data="matchOptions"
      v-loading="loading"
      stripe
      max-height="500px"
    >
      <el-table-column label="推荐" width="120">
        <template #default="{ row }">
          <el-tag :type="getRecommendationType(row.recommendation)">
            {{ row.recommendation }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="teacher_name" label="教师姓名" width="120" />

      <el-table-column
        prop="research_direction"
        label="研究方向"
        min-width="150"
        show-overflow-tooltip
      />

      <el-table-column label="匹配得分" width="100" align="center">
        <template #default="{ row }">
          <el-tag
            :type="row.total_score > 10 ? 'success' : row.total_score > 0 ? 'primary' : 'info'"
            size="large"
          >
            <strong>{{ row.total_score }}</strong>
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="得分详情" min-width="200">
        <template #default="{ row }">
          <div v-if="row.score_details.length > 0" class="score-details">
            <el-tag
              v-for="(detail, idx) in row.score_details"
              :key="idx"
              size="small"
              :type="detail.type === 'teacher_preference' ? 'warning' : 'success'"
              style="margin-right: 4px; margin-bottom: 4px;"
            >
              {{ detail.description }} (+{{ detail.score }})
            </el-tag>
          </div>
          <span v-else style="color: #909399; font-size: 14px;">无志愿匹配</span>
        </template>
      </el-table-column>

      <el-table-column label="当前负载" width="120" align="center">
        <template #default="{ row }">
          <el-progress
            :percentage="row.load_percentage"
            :color="row.is_over_capacity ? '#f56c6c' : '#67c23a'"
            :status="row.is_over_capacity ? 'exception' : undefined"
          >
            <span class="percentage-label">
              {{ row.current_load }}/{{ row.capacity_limit }}
            </span>
          </el-progress>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            @click="handleSelectTeacher(row)"
          >
            选择
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api'

const props = defineProps({
  modelValue: Boolean,
  eventId: [Number, String],
  groupId: [Number, String],
  groupName: String
})

const emit = defineEmits(['update:modelValue', 'select'])

const visible = ref(false)
const loading = ref(false)
const matchOptions = ref([])

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.eventId && props.groupId) {
    fetchMatchOptions()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const fetchMatchOptions = async () => {
  loading.value = true
  try {
    const response = await api.getMatchOptions(props.eventId, props.groupId)
    matchOptions.value = response.data.match_options
  } catch (error) {
    ElMessage.error('获取匹配选项失败')
    console.error('Failed to fetch match options:', error)
  } finally {
    loading.value = false
  }
}

const getRecommendationType = (recommendation) => {
  if (recommendation.includes('强烈推荐')) return 'success'
  if (recommendation.includes('推荐')) return 'primary'
  if (recommendation.includes('可选')) return ''
  if (recommendation.includes('超额')) return 'danger'
  return 'info'
}

const handleSelectTeacher = (row) => {
  emit('select', row.teacher_id)
  handleClose()
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.percentage-label {
  font-size: 12px;
  color: #606266;
}

.score-details {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>