<template>
  <div class="advanced-multi-select">
    <div class="list-container" @mousedown.prevent>
      <div
        v-for="(item, index) in items"
        :key="item.value"
        :class="['list-item', { 'selected': isSelected(item.value), 'disabled': item.disabled }]"
        @click.exact="handleClick(item, index)"
        @click.ctrl.exact="handleClick(item, index)"
        @click.meta.exact="handleClick(item, index)"
        @click.shift.exact="handleShiftClick(item, index)"
      >
        <span class="item-label">{{ item.label }}</span>
        <span v-if="item.disabled" class="disabled-text">- 已被占用</span>
      </div>
      <div v-if="items.length === 0" class="no-items-placeholder">
        没有符合条件的数据
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  items: { type: Array, required: true }, // 格式: { value, label, disabled }
  modelValue: { type: Array, required: true },
});

const emit = defineEmits(['update:modelValue']);

const lastClickedIndex = ref(-1);

const isSelected = (value) => {
  return props.modelValue.includes(value);
};

// 单击和 Ctrl/Cmd+单击 的逻辑
const handleClick = (item, index) => {
  if (item.disabled) return;

  const selectedSet = new Set(props.modelValue);
  if (selectedSet.has(item.value)) {
    selectedSet.delete(item.value);
  } else {
    selectedSet.add(item.value);
  }

  emit('update:modelValue', Array.from(selectedSet));
  lastClickedIndex.value = index;
};

// Shift+单击 的逻辑
const handleShiftClick = (clickedItem, clickedIndex) => {
  if (clickedItem.disabled) return;

  if (lastClickedIndex.value === -1) {
    handleClick(clickedItem, clickedIndex);
    return;
  }

  const selectedSet = new Set(props.modelValue);
  const start = Math.min(lastClickedIndex.value, clickedIndex);
  const end = Math.max(lastClickedIndex.value, clickedIndex);

  for (let i = start; i <= end; i++) {
    const itemInRange = props.items[i];
    if (itemInRange && !itemInRange.disabled) {
      selectedSet.add(itemInRange.value);
    }
  }

  emit('update:modelValue', Array.from(selectedSet));
};

// 当外部过滤条件变化导致 items 变化时，重置 lastClickedIndex
watch(() => props.items, () => {
  lastClickedIndex.value = -1;
});
</script>

<style scoped>
.advanced-multi-select {
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: white;
}
.list-container {
  height: 250px;
  overflow-y: auto;
  user-select: none; /* 禁止文本选择 */
}
.list-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.15s ease-in-out;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.list-item:hover {
  background-color: #e9f5ff;
}
.list-item.selected {
  background-color: #007bff;
  color: white;
  font-weight: 600;
}
.list-item.selected:hover {
  background-color: #0056b3;
}
.list-item.disabled {
  color: #aaa;
  background-color: #f9f9f9;
  cursor: not-allowed;
}
.list-item.disabled .item-label {
  text-decoration: line-through;
}
.disabled-text {
  font-style: italic;
  font-size: 0.9em;
}
.no-items-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
}
</style>