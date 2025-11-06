import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const userType = ref(null) // 'admin', 'student', 'teacher'

  const isLoggedIn = computed(() => !!userInfo.value)

  const setUser = (info, type) => {
    userInfo.value = info
    userType.value = type
  }

  const clearUser = () => {
    userInfo.value = null
    userType.value = null

    // 清除所有token
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('studentAccessToken')
    localStorage.removeItem('studentRefreshToken')
    localStorage.removeItem('teacherAccessToken')
    localStorage.removeItem('teacherRefreshToken')
  }

  const getToken = () => {
    if (userType.value === 'student') {
      return localStorage.getItem('studentAccessToken')
    } else if (userType.value === 'teacher') {
      return localStorage.getItem('teacherAccessToken')
    } else {
      return localStorage.getItem('accessToken')
    }
  }

  return {
    userInfo,
    userType,
    isLoggedIn,
    setUser,
    clearUser,
    getToken
  }
})