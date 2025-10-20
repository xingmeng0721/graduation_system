import apiClient from '../plugins/axios';

// 定义API前缀，方便管理和修改
const ADMIN_BASE = 'admin/';
const STUDENT_BASE = 'student/';

export default {
  login(data) {
    return apiClient.post(`${ADMIN_BASE}login/`, data);
  },
  register(data) {
    return apiClient.post(`${ADMIN_BASE}register/`, data);
  },
  bulkRegister(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`${ADMIN_BASE}register/bulk/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  downloadTemplate() {
    return apiClient.get(`${ADMIN_BASE}register/template/`, {
      responseType: 'blob',
    });
  },
  getUsers() {
    return apiClient.get(`${ADMIN_BASE}users/`);
  },
  getStudents() {
    return apiClient.get(`${ADMIN_BASE}students/`);
  },
  createStudent(studentData) {
    return apiClient.post(`${ADMIN_BASE}students/`, studentData);
  },
  getMajors() {
    return apiClient.get(`${ADMIN_BASE}majors/`);
  },
  getGroups() {
    return apiClient.get(`${ADMIN_BASE}groups/`);
  },

  studentLogin(credentials) {
    return apiClient.post(`${STUDENT_BASE}login/`, credentials);
  },
  getStudentProfile() {
    return apiClient.get(`${STUDENT_BASE}profile/`);
  }
};