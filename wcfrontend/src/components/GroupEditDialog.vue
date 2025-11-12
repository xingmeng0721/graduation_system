<template>
  <el-dialog v-model="visible" :title="isEditMode ? '编辑团队信息' : '创建新团队'" width="600px" @close="handleClose">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="团队名称" prop="group_name">
        <el-input v-model="form.group_name" placeholder="请输入团队名称" />
      </el-form-item>
      <el-form-item label="项目标题" prop="project_title">
        <el-input v-model="form.project_title" placeholder="请输入项目标题" />
      </el-form-item>
      <el-form-item label="项目简介" prop="project_description">
        <el-input v-model="form.project_description" type="textarea" :rows="3" placeholder="请输入项目简介" />
      </el-form-item>
      <el-form-item label="选择成员" prop="members">
        <el-select v-model="form.members" multiple filterable remote :remote-method="searchStudents"
          :loading="studentSearchLoading" :placeholder="selectPlaceholder" style="width: 100%;">
          <el-option v-for="student in studentOptions" :key="student.stu_id"
            :label="`${student.stu_name} (${student.stu_no})`" :value="student.stu_id" />
        </el-select>
      </el-form-item>
      <el-form-item label="指定队长" prop="captain_id">
        <el-select v-model="form.captain_id" placeholder="从已选成员中指定队长" style="width: 100%;">
          <el-option v-for="memberId in form.members" :key="memberId" :label="getStudentNameById(memberId)"
            :value="memberId" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">确认提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../services/api';

const props = defineProps({ modelValue: Boolean, groupData: Object, eventData: Object });
const emit = defineEmits(['update:modelValue', 'submitted']);

const visible = ref(false);
const formRef = ref(null);
const isSubmitting = ref(false);
const studentSearchLoading = ref(false);
const studentOptions = ref([]);
const form = ref({ group_name: '', project_title: '', project_description: '', members: [], captain_id: null });
const rules = {
  group_name: [{ required: true, message: '团队名称不能为空', trigger: 'blur' }],
  members: [{ required: true, type: 'array', min: 1, message: '至少选择一名成员', trigger: 'change' }],
  captain_id: [{ required: true, message: '必须从成员中指定一位队长', trigger: 'change' }],
};

const isEditMode = computed(() => !!props.groupData);

const studentPool = computed(() => {
  if (!props.eventData) return [];
  if (isEditMode.value) {
    return props.eventData.event.students || [];
  }
  return props.eventData.ungrouped_students_list || [];
});

const selectPlaceholder = computed(() => {
    return isEditMode.value ? '可从所有参与学生中调整' : '请从未分组学生中选择';
});

watch(() => props.modelValue, (val) => {
  visible.value = val;
  if (val) {
    studentOptions.value = studentPool.value;
    if (isEditMode.value) {
      form.value = {
        group_name: props.groupData.group_name,
        project_title: props.groupData.project_title,
        project_description: props.groupData.project_description,
        members: props.groupData.members.map(m => m.stu_id),
        captain_id: props.groupData.captain.stu_id,
      };
    } else {
      resetForm();
    }
  }
});

const getStudentNameById = (id) => {
  const student = props.eventData?.event.students.find(s => s.stu_id === id);
  return student ? `${student.stu_name} (${student.stu_no})` : '';
};

const searchStudents = (query) => {
  studentSearchLoading.value = true;
  setTimeout(() => {
    if (query) {
      studentOptions.value = studentPool.value.filter(s =>
        s.stu_name.toLowerCase().includes(query.toLowerCase()) || s.stu_no.includes(query)
      );
    } else {
      studentOptions.value = studentPool.value;
    }
    studentSearchLoading.value = false;
  }, 200);
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();
  isSubmitting.value = true;
  try {
    const payload = {...form.value, event_id: props.eventData.event.event_id};
    if (isEditMode.value) {
      await api.adminUpdateGroup(props.groupData.group_id, payload);
      ElMessage.success('团队信息更新成功！');
    } else {
      await api.adminCreateGroup(payload);
      ElMessage.success('新团队创建成功！');
    }
    emit('submitted');
    handleClose();
  } catch (error) {
    ElMessage.error(`操作失败: ${error.response?.data?.error || '请检查输入'}`);
  } finally {
    isSubmitting.value = false;
  }
};

const resetForm = () => {
  if (formRef.value) formRef.value.resetFields();
};
const handleClose = () => {
  emit('update:modelValue', false);
};
</script>