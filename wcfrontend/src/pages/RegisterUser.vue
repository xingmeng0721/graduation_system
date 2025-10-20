<template>
  <div>
    <h1>注册新用户</h1>
    <div class="register-container">
      <!-- 单用户注册 -->
      <div class="register-card">
        <h2>手动添加用户</h2>
        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label for="name">名称</label>
            <input type="text" id="name" v-model="admin_name" required>
          </div>
          <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" v-model="admin_username" required>
          </div>
          <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" v-model="password" required>
          </div>
          <div v-if="error" class="error-message">{{ error }}</div>
          <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
          <button type="submit" class="btn-submit">添加用户</button>
        </form>
      </div>

      <!-- 批量注册 -->
      <div class="register-card">
        <h2>通过 Excel 批量添加</h2>
        <p class="description">下载模板，填写后上传。</p>
       <button @click="handleDownloadTemplate" class="btn-secondary">下载模板</button>
        <div class="upload-area" @click="triggerFileUpload">
          <input type="file" ref="fileInput" @change="handleFileChange" accept=".xlsx, .xls" style="display: none;" />
          <p v-if="!selectedFile">点击或拖拽文件上传</p>
          <p v-else>已选择: {{ selectedFile.name }}</p>
        </div>
        <div v-if="bulkError" class="error-message">{{ bulkError }}</div>
        <div v-if="bulkSuccessMessage" class="success-message">{{ bulkSuccessMessage }}</div>
        <button @click="handleBulkRegister" class="btn-submit" :disabled="!selectedFile">上传并注册</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import api from '../services/api';

// --- 单用户注册逻辑 ---
const admin_name = ref('');
const admin_username = ref('');
const password = ref('');
const error = ref(null);
const successMessage = ref(null);

const handleRegister = async () => {
    error.value = null;
    successMessage.value = null;
    try {
        await api.register({
            admin_name: admin_name.value,
            admin_username: admin_username.value,
            admin_password: password.value
        });
        successMessage.value = '用户添加成功！';
        // 成功后清空表单
        admin_name.value = '';
        admin_username.value = '';
        password.value = '';
    } catch (err) {
        successMessage.value = null;
        if (err.response && err.response.data) {
          const backendErrors = err.response.data;
          let errorMessage = '';
          for (const field in backendErrors) {
            errorMessage += `${field}: ${backendErrors[field].join(', ')} `;
          }
          error.value = errorMessage || '添加失败，请检查输入。';
        } else {
            error.value = '发生网络错误或未知问题。';
        }
        console.error('Register failed:', err);
    }
};

// --- 批量注册逻辑 ---
const fileInput = ref(null);
const selectedFile = ref(null);
const bulkError = ref(null);
const bulkSuccessMessage = ref(null);

const handleDownloadTemplate = async () => {
  bulkError.value = null;
  bulkSuccessMessage.value = null;
  try {
    // 1. 调用我们新的API方法，这将通过axios发起一个带Token的请求
    const response = await api.downloadTemplate();

    // 2. 创建一个指向返回的Blob数据的URL
    const url = window.URL.createObjectURL(new Blob([response.data]));

    // 3. 创建一个临时的 <a> 标签来触发下载
    const link = document.createElement('a');
    link.href = url;

    // 尝试从响应头中获取文件名，否则使用默认名
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'bulk_register_template.xlsx'; // 默认文件名
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1];
      }
    }
    link.setAttribute('download', filename);

    // 4. 模拟点击并清理
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

  } catch (error) {
    console.error('Failed to download template:', error);
    bulkError.value = '模板下载失败，请稍后重试。';
  }
};


const triggerFileUpload = () => {
    fileInput.value.click();
};

const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
        selectedFile.value = file;
        bulkError.value = null;
        bulkSuccessMessage.value = null;
    }
};

const handleBulkRegister = async () => {
    if (!selectedFile.value) {
      bulkError.value = "请先选择一个文件。";
      return;
    }
  bulkError.value = null;
  bulkSuccessMessage.value = '正在上传处理中...';
  try {
    const response = await api.bulkRegister(selectedFile.value);
    bulkSuccessMessage.value = response.data.message;
    selectedFile.value = null;
    if (fileInput.value) {
      fileInput.value.value = ''; // 清空<input>的值，以便可以再次上传同名文件
    }
  } catch (err) {
    bulkSuccessMessage.value = null;
    if (err.response && err.response.data && err.response.data.error) {
      bulkError.value = err.response.data.error;
    } else {
      bulkError.value = '上传失败，发生未知错误。';
    }
    console.error('Bulk register failed:', err);
  }
};
</script>

<style scoped>
.register-container {
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
}

.register-card {
  flex: 1;
  min-width: 350px;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h1 {
  margin-bottom: 20px;
}

h2 {
  margin-bottom: 20px;
  text-align: center;
}

.description {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
  text-align: center;
}

.btn-secondary {
  display: block;
  text-align: center;
  padding: 12px;
  background-color: #6c757d;
  color: white;
  border-radius: 4px;
  text-decoration: none;
  margin-bottom: 20px;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 20px;
}

.upload-area:hover {
  border-color: #007bff;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

.btn-submit {
  width: 100%;
  padding: 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 10px;
}

.btn-submit:disabled {
  background-color: #a0cffa;
  cursor: not-allowed;
}

.error-message {
  color: #dc3545;
  margin-bottom: 15px;
  text-align: center;
  word-break: break-all;
}

.success-message {
  color: #28a745;
  margin-bottom: 15px;
  text-align: center;
}
</style>