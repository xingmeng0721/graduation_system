import apiClient from '../plugins/axios';

// 定义API前缀，方便管理和修改
const ADMIN_BASE = 'admin/';
const STUDENT_BASE = 'student/';
const TEACHER_BASE = 'teacher/';
const TEAM_BASE = 'teams/';

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
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60秒超时
    });
  },
  downloadTemplate() {
    return apiClient.get(`${ADMIN_BASE}register/template/`, {
      responseType: 'blob',
    });
  },
    downloadStudentTemplate() {
    return apiClient.get(`${ADMIN_BASE}students/register/template/`, {
      responseType: 'blob',
    });
  },
  bulkRegisterStudents(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`${ADMIN_BASE}students/register/bulk/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60秒超时
    });
  },
  downloadTeacherTemplate() {
    return apiClient.get(`${ADMIN_BASE}teachers/register/template/`, {
      responseType: 'blob',
    });
  },
  bulkRegisterTeachers(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`${ADMIN_BASE}teachers/register/bulk/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60秒超时
    });
  },
  getUsers() {
    return apiClient.get(`${ADMIN_BASE}users/`);
  },
  getTeachers() {
    return apiClient.get(`${ADMIN_BASE}teachers/`);
  },
  createTeacher(teacherData) {
    return apiClient.post(`${ADMIN_BASE}teachers/`, teacherData);
  },
  updateTeacher(teacherId, teacherData) {
    return apiClient.put(`${ADMIN_BASE}teachers/${teacherId}/`, teacherData);
  },
  deleteTeacher(teacherId) {
    return apiClient.delete(`${ADMIN_BASE}teachers/${teacherId}/`);
  },
  bulkDeleteTeachers(teacherIds) {
    return apiClient.post(`${ADMIN_BASE}teachers/bulk-delete/`, { ids: teacherIds });
  },
  getStudents() {
    return apiClient.get(`${ADMIN_BASE}students/`);
  },
  updateStudent(studentId, studentData) {
    return apiClient.put(`${ADMIN_BASE}students/${studentId}/`, studentData);
  },
  createStudent(studentData) {
    return apiClient.post(`${ADMIN_BASE}students/`, studentData);
  },
  deleteStudent(studentId) {
    return apiClient.delete(`${ADMIN_BASE}students/${studentId}/`);
  },
   bulkDeleteStudents(studentIds) {
    return apiClient.post(`${ADMIN_BASE}students/bulk-delete/`, { ids: studentIds });
  },
  getMajors() {
    return apiClient.get(`${ADMIN_BASE}majors/`);
  },
  getGroups() {
    return apiClient.get(`${ADMIN_BASE}groups/`);
  },
  getMutualSelectionEvents(params = {}) {
    return apiClient.get(`${ADMIN_BASE}mutualselectionevents/`, { params });
  },
  createMutualSelectionEvent(eventData) {
    return apiClient.post(`${ADMIN_BASE}mutualselectionevents/`, eventData);
  },
  updateMutualSelectionEvent(eventId, eventData) {
    return apiClient.put(`${ADMIN_BASE}mutualselectionevents/${eventId}/`, eventData);
  },
  deleteMutualSelectionEvent(eventId) {
    return apiClient.delete(`${ADMIN_BASE}mutualselectionevents/${eventId}/`);
  },
  bulkDeleteMutualSelectionEvents(eventIds) {
    return apiClient.post(`${ADMIN_BASE}mutualselectionevents/bulk-delete/`, { ids: eventIds });
  },
  autoAssignEvent(eventId) {
    return apiClient.post(`${ADMIN_BASE}mutualselectionevents/${eventId}/auto-assign/`);
  },
  studentLogin(credentials) {
    return apiClient.post(`${STUDENT_BASE}login/`, credentials);
  },
  sendStudentResetCode(data) {
    // data 包含 stu_name 和 email
    return apiClient.post(`${STUDENT_BASE}send-reset-code/`, data);
  },
  resetStudentPasswordByCode(data) {
    // data 包含 stu_name, email, code, password
    return apiClient.post(`${STUDENT_BASE}reset-code/`, data);
  },
  getStudentProfile() {
    return apiClient.get(`${STUDENT_BASE}profile/`);
  },
  updateStudentProfile(studentData) {
  return apiClient.put(`${STUDENT_BASE}profile/`, studentData);
  },
  getActiveEventForStudent() {
    // 这个函数会调用我们之前在后端创建的 /api/teams/active-event/ 接口
    return apiClient.get(`${TEAM_BASE}active-event/`);
  },
   getMyTeam() {
    // 删除了多余的 'teams/'
    return apiClient.get(`${TEAM_BASE}my-team/`);
  },
  createTeam(data) {
    // 删除了多余的 'teams/'
    return apiClient.post(`${TEAM_BASE}create-team/`, data);
  },
  joinTeam(groupId) {
    // 删除了多余的 'teams/'
    return apiClient.post(`${TEAM_BASE}${groupId}/join/`);
  },
  leaveTeam() {
    // 删除了多余的 'teams/'
    return apiClient.post(`${TEAM_BASE}leave-team/`);
  },
  getJoinableTeams() {
    // 删除了多余的 'teams/'
    return apiClient.get(`${TEAM_BASE}joinable/`);
  },
  teacherLogin(credentials) {
    return apiClient.post(`${TEACHER_BASE}login/`, credentials);
  },
  getTeacherProfile() {
    return apiClient.get(`${TEACHER_BASE}profile/`);
  },
  updateTeacherProfile(teacherData) {
  return apiClient.put(`${TEACHER_BASE}profile/`, teacherData);
  },
};