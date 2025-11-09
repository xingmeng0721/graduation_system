// src/services/api.js

import apiClient from '../plugins/axios';

const ADMIN_BASE = 'admin/';
const STUDENT_BASE = 'student/';
const TEACHER_BASE = 'teacher/';
const TEAM_BASE = 'teams/';

export default {
  // ========================================
  // 认证相关 (Authentication)
  // ========================================

  // 登录
  login(data) {
    return apiClient.post(`${ADMIN_BASE}login/`, data);
  },

  studentLogin(credentials) {
    return apiClient.post(`${STUDENT_BASE}login/`, credentials);
  },

  teacherLogin(credentials) {
    return apiClient.post(`${TEACHER_BASE}login/`, credentials);
  },

  // Token刷新
  refreshAdminToken(refreshToken) {
    return apiClient.post(`${ADMIN_BASE}token/refresh/`, { refresh: refreshToken });
  },

  refreshStudentToken(refreshToken) {
    return apiClient.post(`${STUDENT_BASE}token/refresh/`, { refresh: refreshToken });
  },

  refreshTeacherToken(refreshToken) {
    return apiClient.post(`${TEACHER_BASE}token/refresh/`, { refresh: refreshToken });
  },

  // 学生密码重置
  sendStudentResetCode(data) {
    return apiClient.post(`${STUDENT_BASE}send-reset-code/`, data);
  },

  resetStudentPasswordByCode(data) {
    return apiClient.post(`${STUDENT_BASE}reset-code/`, data);
  },

  // ========================================
  // 管理员管理 (Admin Management)
  // ========================================

  // 管理员个人信息
  getAdminProfile() {
    return apiClient.get(`${ADMIN_BASE}profile/`);
  },

  updateAdminProfile(adminData) {
    return apiClient.put(`${ADMIN_BASE}profile/`, adminData);
  },

  // 管理员账号管理
  register(data) {
    return apiClient.post(`${ADMIN_BASE}register/`, data);
  },

  getUsers() {
    return apiClient.get(`${ADMIN_BASE}users/`);
  },

  createAdminUser(adminData) {
    return apiClient.post(`${ADMIN_BASE}users/`, adminData);
  },

  updateAdminUser(adminId, adminData) {
    return apiClient.put(`${ADMIN_BASE}users/${adminId}/`, adminData);
  },

  deleteAdminUser(adminId) {
    return apiClient.delete(`${ADMIN_BASE}users/${adminId}/`);
  },

  bulkDeleteAdminUsers(adminIds) {
    return apiClient.post(`${ADMIN_BASE}users/bulk-delete/`, { ids: adminIds });
  },

  // 管理员批量注册
  bulkRegister(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`${ADMIN_BASE}register/bulk/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  },

  downloadTemplate() {
    return apiClient.get(`${ADMIN_BASE}register/template/`, {
      responseType: 'blob',
    });
  },

  // ========================================
  // 学生管理 (Student Management)
  // ========================================

  // 学生个人信息
  getStudentProfile() {
    return apiClient.get(`${STUDENT_BASE}profile/`);
  },

  updateStudentProfile(studentData) {
    return apiClient.put(`${STUDENT_BASE}profile/`, studentData);
  },

  // 学生账号管理
  getStudents() {
    return apiClient.get(`${ADMIN_BASE}students/`);
  },

  createStudent(studentData) {
    return apiClient.post(`${ADMIN_BASE}students/`, studentData);
  },

  updateStudent(studentId, studentData) {
    return apiClient.put(`${ADMIN_BASE}students/${studentId}/`, studentData);
  },

  deleteStudent(studentId) {
    return apiClient.delete(`${ADMIN_BASE}students/${studentId}/`);
  },

  bulkDeleteStudents(studentIds) {
    return apiClient.post(`${ADMIN_BASE}students/bulk-delete/`, { ids: studentIds });
  },

  // 学生批量注册
  bulkRegisterStudents(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`${ADMIN_BASE}students/register/bulk/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  },

  downloadStudentTemplate() {
    return apiClient.get(`${ADMIN_BASE}students/register/template/`, {
      responseType: 'blob',
    });
  },

  // ========================================
  // 教师管理 (Teacher Management)
  // ========================================

  // 教师个人信息
  getTeacherProfile() {
    return apiClient.get(`${TEACHER_BASE}profile/`);
  },

  updateTeacherProfile(teacherData) {
    return apiClient.put(`${TEACHER_BASE}profile/`, teacherData);
  },

  // 教师账号管理
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

  // 教师批量注册
  bulkRegisterTeachers(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`${ADMIN_BASE}teachers/register/bulk/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  },

  downloadTeacherTemplate() {
    return apiClient.get(`${ADMIN_BASE}teachers/register/template/`, {
      responseType: 'blob',
    });
  },

  // ========================================
  // 互选活动管理 (Mutual Selection Events)
  // ========================================

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

  // ========================================
  // 学生端 - 团队管理 (Student Team Management)
  // ========================================

  // 仪表盘
  getDashboard() {
    return apiClient.get(`${TEAM_BASE}dashboard/`);
  },

  // 团队操作
  createTeam(data) {
    return apiClient.post(`${TEAM_BASE}create-team/`, data);
  },

  updateMyTeam(data) {
    return apiClient.put(`${TEAM_BASE}my-team/update/`, data);
  },

  disbandTeam() {
    return apiClient.post(`${TEAM_BASE}my-team/disband/`);
  },

  joinTeam(groupId) {
    return apiClient.post(`${TEAM_BASE}${groupId}/join/`);
  },

  leaveTeam() {
    return apiClient.post(`${TEAM_BASE}leave-team/`);
  },

  // 成员管理
  addMemberByCaptain(data) {
    return apiClient.post(`${TEAM_BASE}my-team/add-member/`, data);
  },

  removeMember(memberId) {
    return apiClient.post(`${TEAM_BASE}my-team/remove-member/`, { student_id: memberId });
  },

  // 可用资源
  getAllTeamsInActiveEvent() {
    return apiClient.get(`${TEAM_BASE}all-teams/`);
  },

  getAvailableTeammates() {
    return apiClient.get(`${TEAM_BASE}available-teammates/`);
  },

  getAvailableAdvisors() {
    return apiClient.get(`${TEAM_BASE}available-teachers/`);
  },

  // 团队详情
  getGroupDetail(groupId) {
    return apiClient.get(`${TEAM_BASE}${groupId}/group-detail/`);
  },

  // 历史记录
  getStudentHistory() {
    return apiClient.get(`${TEAM_BASE}student/history/`);
  },

  getStudentHistoryDetail(eventId) {
    return apiClient.get(`${TEAM_BASE}${eventId}/student/history-detail/`);
  },

  // ========================================
  // 教师端 - 团队管理 (Teacher Team Management)
  // ========================================

  // 仪表盘
  getTeacherDashboard() {
    return apiClient.get(`${TEAM_BASE}teacher/dashboard/`);
  },

  // 志愿设置
  setTeacherPreferences(preferences) {
    return apiClient.post(`${TEAM_BASE}teacher/set-preferences/`, { preferences });
  },

  // 团队详情
  teacherGetGroupDetail(groupId) {
    return apiClient.get(`${TEAM_BASE}${groupId}/teacher/group-detail/`);
  },

  // 指导的团队
  getMyAdvisedGroups() {
    return apiClient.get(`${TEAM_BASE}teacher/my-advised-groups/`);
  },

  getCurrentAdvisedGroups() {
    return apiClient.get(`${TEAM_BASE}teacher/current-advised-groups/`);
  },

  // 历史记录
  getTeacherHistory() {
    return apiClient.get(`${TEAM_BASE}teacher/history/`);
  },

  getTeacherHistoryDetail(eventId) {
    return apiClient.get(`${TEAM_BASE}${eventId}/teacher/history-detail/`);
  },

  // ========================================
  // 管理员 - 分配管理 (Admin Assignment Management)
  // ========================================

  // 自动分配
  autoAssign(eventId) {
    return apiClient.post(`${TEAM_BASE}${eventId}/admin/auto-assign/`);
  },

  // 查看分配结果
  getAssignments(eventId) {
    return apiClient.get(`${TEAM_BASE}${eventId}/admin/get-assignments/`);
  },

  // 手动分配
  manualAssign(eventId, groupId, teacherId) {
    return apiClient.post(`${TEAM_BASE}${eventId}/admin/manual-assign/`, {
      group_id: groupId,
      teacher_id: teacherId
    });
  },

  // 发布结果
  publishAssignments(eventId) {
    return apiClient.post(`${TEAM_BASE}${eventId}/admin/publish/`);
  },

  // 匹配选项
  getMatchOptions(eventId, groupId) {
    return apiClient.get(`${TEAM_BASE}${eventId}/admin/match-options/`, {
      params: { group_id: groupId }
    });
  },

  getAllMatchOptions(eventId) {
    return apiClient.get(`${TEAM_BASE}${eventId}/admin/all-match-options/`);
  },

  // ========================================
  // 其他 (Others)
  // ========================================

  getMajors() {
    return apiClient.get(`${ADMIN_BASE}majors/`);
  },

  getGroups() {
    return apiClient.get(`${ADMIN_BASE}groups/`);
  },
};