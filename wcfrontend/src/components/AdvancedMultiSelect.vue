<template>
  <div class="advanced-multi-select">
    <el-scrollbar height="300px" class="list-scrollbar">
      <div class="list-container" @mousedown.prevent>
        <div
          v-for="(item, index) in items"
          :key="item.value"
          :class="[
            'list-item',
            {
              'selected': isSelected(item.value),
              'disabled': item.disabled,
              'hoverable': !item.disabled
            }
          ]"
          @click.exact="handleClick(item, index)"
          @click.ctrl.exact="handleClick(item, index)"
          @click.meta.exact="handleClick(item, index)"
          @click.shift.exact="handleShiftClick(item, index)"
        >
          <div class="item-content">
            <div class="check-box">
              <span v-if="isSelected(item.value)" class="check-mark">✓</span>
            </div>
            <span class="item-label">{{ item.label }}</span>
          </div>
          <el-tag v-if="item.disabled" type="info" size="small" effect="plain">
            已被占用
          </el-tag>
        </div>

        <div v-if="items.length === 0" class="empty-state">
          <p>没有符合条件的数据</p>
        </div>
      </div>
    </el-scrollbar>

    <!-- 操作提示 -->
    <div class="selection-tips">
      <span class="tips-text">提示: 单击选择，Ctrl+单击多选，Shift+单击范围选择</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  items: { type: Array, required: true }, // 格式: { value, label, disabled }
  modelValue: { type: Array, required: true }
})

const emit = defineEmits(['update:modelValue'])

const lastClickedIndex = ref(-1)

const isSelected = (value) => {
  return props.modelValue.includes(value)
}

// 单击和 Ctrl/Cmd+单击 的逻辑
const handleClick = (item, index) => {
  if (item.disabled) return

  const selectedSet = new Set(props.modelValue)
  if (selectedSet.has(item.value)) {
    selectedSet.delete(item.value)
  } else {
    selectedSet.add(item.value)
  }

  emit('update:modelValue', Array.from(selectedSet))
  lastClickedIndex.value = index
}

// Shift+单击 的逻辑
const handleShiftClick = (clickedItem, clickedIndex) => {
  if (clickedItem.disabled) return

  if (lastClickedIndex.value === -1) {
    handleClick(clickedItem, clickedIndex)
    return
  }

  const selectedSet = new Set(props.modelValue)
  const start = Math.min(lastClickedIndex.value, clickedIndex)
  const end = Math.max(lastClickedIndex.value, clickedIndex)

  for (let i = start; i <= end; i++) {
    const itemInRange = props.items[i]
    if (itemInRange && !itemInRange.disabled) {
      selectedSet.add(itemInRange.value)
    }
  }

  emit('update:modelValue', Array.from(selectedSet))
}

// 当外部过滤条件变化导致 items 变化时，重置 lastClickedIndex
watch(() => props.items, () => {
  lastClickedIndex.value = -1
})
</script>

<style scoped>
.advanced-multi-select {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #ffffff;
  overflow: hidden;
}

.list-scrollbar {
  border-bottom: 1px solid #f0f0f0;
}

.list-container {
  user-select: none;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #f5f7fa;
  transition: all 0.2s ease;
  cursor: pointer;
}

.list-item:last-child {
  border-bottom: none;
}

.list-item.hoverable:hover {
  background-color: #f5f7fa;
}

.list-item.selected {
  background-color: #ecf5ff;
}

.list-item.selected .item-label {
  color: #409eff;
  font-weight: 500;
}

.list-item.disabled {
  background-color: #fafafa;
  cursor: not-allowed;
  opacity: 0.6;
}

.list-item.disabled .item-label {
  color: #c0c4cc;
  text-decoration: line-through;
}

.item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.check-box {
  width: 18px;
  height: 18px;
  border: 2px solid #dcdfe6;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.list-item.selected .check-box {
  background-color: #409eff;
  border-color: #409eff;
}

.check-mark {
  color: #ffffff;
  font-size: 14px;
  font-weight: bold;
  line-height: 1;
}

.item-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.selection-tips {
  padding: 10px 16px;
  background-color: #f5f7fa;
  border-top: 1px solid #ebeef5;
}

.tips-text {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

/* 滚动条美化 */
.list-scrollbar :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}
</style>