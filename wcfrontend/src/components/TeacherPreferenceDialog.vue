<template>
  <el-dialog
    v-model="visible"
    :title="`设置志愿：${team?.project_title || '团队详情'}`"
    width="900px"
    @close="handleClose"
  >
    <div v-if="loading" v-loading="loading" style="height: 300px;"></div>

    <div v-else-if="team">
      <!-- 项目信息 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header>
          <h4 style="margin: 0;">项目信息</h4>
        </template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="项目标题">{{ team.project_title || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="项目简介">
            <div style="max-height: 200px; overflow-y: auto; white-space: pre-wrap;">
              {{ team.project_description || '未填写' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 团队成员 -->
      <el-card shadow="never">
        <template #header>
          <h4 style="margin: 0;">团队成员 ({{ team.member_count || 0 }}人)</h4>
        </template>
        <el-table :data="team.members" border stripe size="small">
          <el-table-column label="姓名" width="100">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 6px;">
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
              <el-text v-if="row.phone" copyable size="small">{{ row.phone }}</el-text>
              <span v-else style="color: #909399;">未填写</span>
            </template>
          </el-table-column>
          <el-table-column label="电子邮箱" min-width="160">
            <template #default="{ row }">
              <el-text v-if="row.email" copyable size="small">{{ row.email }}</el-text>
              <span v-else style="color: #909399;">未填写</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 底部：设为我的志愿 -->
    <template #footer>
      <div class="dialog-footer">
        <span class="footer-label">设为我的志愿：</span>
        <el-button-group>
          <el-button
            v-for="rank in choiceLimit"
            :key="rank"
            :type="currentChoice === rank ? preferenceTagTypes[rank-1] : 'default'"
            :plain="currentChoice !== rank"
            :disabled="isRankOccupied(rank)"
            @click="handleSetPreference(rank)"
          >
            第{{ ['一','二','三','四','五'][rank - 1] || rank }}志愿
          </el-button>
        </el-button-group>
        <el-button
          v-if="currentChoice"
          type="danger"
          link
          @click="handleSetPreference(null)"
          style="margin-left: 10px;"
        >
          取消志愿
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean,
  team: Object,
  preferences: Object,
  choiceLimit: Number
})

const emit = defineEmits(['update:modelValue', 'update:preferences'])

const visible = ref(false)
const loading = ref(false)
const preferenceTagTypes = ['danger', 'warning', 'success', 'primary', 'info']

watch(() => props.modelValue, (val) => {
  visible.value = val
})

const handleClose = () => {
  emit('update:modelValue', false)
}

const currentChoice = computed(() => {
  if (!props.preferences || !props.team) return null
  const entry = Object.entries(props.preferences).find(([, id]) => id === props.team.group_id)
  return entry ? parseInt(entry[0]) : null
})

const isRankOccupied = (rank) => {
  if (!props.preferences) return false
  const occupantId = props.preferences[rank]
  return occupantId && occupantId !== props.team?.group_id
}

const handleSetPreference = (rank) => {
  const newPreferences = { ...props.preferences }

  Object.keys(newPreferences).forEach(key => {
    if (newPreferences[key] === props.team.group_id) {
      newPreferences[key] = null
    }
  })

  if (rank !== null) {
    if (newPreferences[rank]) {
      ElMessage.warning(`第${rank}志愿已被其他团队占用，请先取消。`)
      return
    }
    newPreferences[rank] = props.team.group_id
  }

  emit('update:preferences', newPreferences)
  ElMessage.success({
    message: rank ? `已将该团队设为第${rank}志愿，记得保存哦！` : '已取消志愿，记得保存最终修改。',
    duration: 2000
  })
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding-top: 10px;
}
.footer-label {
  font-size: 14px;
  color: #606266;
  margin-right: 12px;
}
</style>
