<template>
  <el-dialog
    v-model="visible"
    title="全局匹配矩阵"
    width="95%"
    top="5vh"
    @close="handleClose"
  >
    <div v-loading="loading">
      <!-- 顶部统计 -->
      <el-row :gutter="16" style="margin-bottom: 20px;">
        <el-col :span="8">
          <el-card shadow="hover">
            <el-statistic title="总团队数" :value="matrixData?.total_groups || 0">
              <template #prefix>
                <el-icon color="#409eff"><UserFilled /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <el-statistic title="总教师数" :value="matrixData?.total_teachers || 0">
              <template #prefix>
                <el-icon color="#67c23a"><Avatar /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <el-statistic title="平均匹配度" :value="averageScore" :precision="2">
              <template #prefix>
                <el-icon color="#e6a23c"><TrendCharts /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
      </el-row>

      <!-- 教师负载统计 -->
      <el-card style="margin-bottom: 20px;" shadow="never">
        <template #header>
          <div class="card-header">
            <span>教师负载统计</span>
          </div>
        </template>
        <el-table :data="matrixData?.teacher_stats || []" stripe border>
          <el-table-column prop="teacher_name" label="教师姓名" width="120" />
          <el-table-column label="当前负载" min-width="300">
            <template #default="{ row }">
              <el-progress
                :percentage="getLoadPercentage(row)"
                :color="row.is_over_capacity ? '#f56c6c' : '#67c23a'"
                :status="row.is_over_capacity ? 'exception' : undefined"
              >
                <span style="font-size: 12px;">
                  {{ row.assigned_count }}/{{ row.capacity_limit }}
                </span>
              </el-progress>
            </template>
          </el-table-column>
          <el-table-column prop="assigned_count" label="已分配团队" width="120" align="center" />
          <el-table-column prop="remaining_capacity" label="剩余容量" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="row.remaining_capacity > 0 ? 'success' : 'danger'">
                {{ row.remaining_capacity }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_over_capacity" type="danger">超额</el-tag>
              <el-tag v-else-if="row.remaining_capacity === 0" type="warning">满额</el-tag>
              <el-tag v-else type="success">正常</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 团队匹配矩阵 -->
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>团队-教师匹配矩阵</span>
            <el-input
              v-model="searchText"
              placeholder="搜索团队名称或队长"
              style="width: 300px;"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </template>

        <el-collapse v-model="activeNames" accordion>
          <el-collapse-item
            v-for="groupMatch in filteredMatrix"
            :key="groupMatch.group_id"
            :name="groupMatch.group_id"
          >
            <template #title>
              <div class="collapse-title">
                <el-tag type="primary" size="large">{{ groupMatch.group_name }}</el-tag>
                <span class="group-info">
                  队长: {{ groupMatch.captain_name }} | 成员: {{ groupMatch.member_count }}人
                </span>
              </div>
            </template>

            <el-table
              :data="groupMatch.teachers"
              stripe
              size="small"
              :default-sort="{ prop: 'score', order: 'descending' }"
            >
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="teacher_name" label="教师姓名" width="120" />
              <el-table-column label="匹配得分" width="100" align="center" sortable prop="score">
                <template #default="{ row }">
                  <el-tag
                    :type="getScoreType(row.score)"
                    effect="dark"
                    size="large"
                  >
                    <strong>{{ row.score }}</strong>
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="志愿详情" min-width="200">
                <template #default="{ row }">
                  <div class="preference-tags">
                    <el-tag
                      v-if="row.teacher_rank"
                      type="warning"
                      size="small"
                      effect="plain"
                    >
                      教师第{{ row.teacher_rank }}志愿
                    </el-tag>
                    <el-tag
                      v-if="row.student_rank"
                      type="success"
                      size="small"
                      effect="plain"
                    >
                      学生第{{ row.student_rank }}志愿
                    </el-tag>
                    <el-tag v-if="!row.teacher_rank && !row.student_rank" type="info" size="small">
                      无志愿匹配
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="教师负载" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_over_capacity ? 'danger' : 'success'">
                    {{ row.current_load }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="推荐度" width="120" align="center">
                <template #default="{ row }">
                  <el-rate
                    :model-value="getRecommendationRate(row.score, row.is_over_capacity)"
                    disabled
                    show-score
                    :max="5"
                  />
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="exportMatrix">导出数据</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Avatar, TrendCharts, Search } from '@element-plus/icons-vue'
import api from '../services/api'

const props = defineProps({
  modelValue: Boolean,
  eventId: [Number, String]
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const loading = ref(false)
const matrixData = ref(null)
const activeNames = ref([])
const searchText = ref('')

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.eventId) {
    fetchMatrixData()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const filteredMatrix = computed(() => {
  if (!matrixData.value?.match_matrix) return []
  if (!searchText.value) return matrixData.value.match_matrix

  const query = searchText.value.toLowerCase()
  return matrixData.value.match_matrix.filter(group =>
    group.group_name.toLowerCase().includes(query) ||
    group.captain_name.toLowerCase().includes(query)
  )
})

const averageScore = computed(() => {
  if (!matrixData.value?.match_matrix) return 0

  let totalScore = 0
  let count = 0

  matrixData.value.match_matrix.forEach(group => {
    group.teachers.forEach(teacher => {
      totalScore += teacher.score
      count++
    })
  })

  return count > 0 ? totalScore / count : 0
})

const fetchMatrixData = async () => {
  loading.value = true
  try {
    const response = await api.getAllMatchOptions(props.eventId)
    matrixData.value = response.data
  } catch (error) {
    ElMessage.error('获取匹配矩阵失败')
    console.error('Failed to fetch matrix:', error)
  } finally {
    loading.value = false
  }
}

const getLoadPercentage = (row) => {
  if (row.capacity_limit === 0) return 0
  return Math.min(Math.round((row.assigned_count / row.capacity_limit) * 100), 100)
}

const getScoreType = (score) => {
  if (score >= 15) return 'success'
  if (score >= 10) return 'primary'
  if (score >= 5) return 'warning'
  if (score > 0) return 'info'
  return 'info'
}

const getRecommendationRate = (score, isOverCapacity) => {
  if (isOverCapacity) return 1
  if (score >= 15) return 5
  if (score >= 10) return 4
  if (score >= 5) return 3
  if (score > 0) return 2
  return 1
}

const exportMatrix = () => {
  if (!matrixData.value) return

  const data = JSON.stringify(matrixData.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `匹配矩阵_${new Date().getTime()}.json`
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success('数据已导出')
}

const handleClose = () => {
  visible.value = false
  searchText.value = ''
  activeNames.value = []
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.group-info {
  color: #606266;
  font-size: 14px;
}

.preference-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>