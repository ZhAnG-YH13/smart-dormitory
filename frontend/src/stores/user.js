import { defineStore } from 'pinia'
import api from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    infoComplete: 100,
    faceRegistered: false,
    unreadCount: 0
  }),

  getters: {
    isLogin: state => !!state.token,
    role: state => state.user?.role || '',
    roleName: state => {
      const map = { admin: '学校管理员', counselor: '辅导员', student: '学生' }
      return map[state.user?.role] || ''
    },
    homePath: state => {
      const map = {
        admin: '/dashboard',
        counselor: '/counselor/dashboard',
        student: '/student/home'
      }
      return map[state.user?.role] || '/login'
    }
  },

  actions: {
    async login(username, password) {
      const data = await api.post('/auth/login', { username, password })
      this.token = data.token
      this.user = data.user
      this.infoComplete = data.info_complete ?? 100
      this.faceRegistered = !!data.face_registered
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user))
      return data
    },

    async fetchMe() {
      const data = await api.get('/auth/me')
      this.user = {
        id: data.id,
        username: data.username,
        real_name: data.real_name,
        role: data.role,
        phone: data.phone,
        email: data.email
      }
      this.infoComplete = data.info_complete ?? 100
      this.faceRegistered = !!data.face_registered
      localStorage.setItem('user', JSON.stringify(this.user))
      return data
    },

    async fetchUnread() {
      try {
        const d = await api.get('/messages/unread-count')
        this.unreadCount = d.unread_count ?? d.count ?? 0
      } catch (e) {
        this.unreadCount = 0
      }
    },

    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
