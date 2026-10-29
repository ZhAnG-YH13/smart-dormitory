import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

import MainLayout from '@/layouts/MainLayout.vue'
import Login from '@/views/Login.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { public: true } },
  {
    path: '/',
    component: MainLayout,
    redirect: () => {
      const store = useUserStore()
      return store.homePath
    },
    children: [
      // ============ 管理员 ============
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/admin/Dashboard.vue'), meta: { roles: ['admin'] } },
      { path: 'students', name: 'Students', component: () => import('@/views/admin/Students.vue'), meta: { roles: ['admin'] } },
      { path: 'students/import', name: 'StudentImport', component: () => import('@/views/admin/StudentImport.vue'), meta: { roles: ['admin'] } },
      { path: 'organization', name: 'Organization', component: () => import('@/views/admin/Organization.vue'), meta: { roles: ['admin'] } },
      { path: 'dormitory', name: 'Dormitory', component: () => import('@/views/admin/Dormitory.vue'), meta: { roles: ['admin'] } },
      { path: 'cameras', name: 'Cameras', component: () => import('@/views/admin/Cameras.vue'), meta: { roles: ['admin'] } },
      { path: 'gate', name: 'GateSimulator', component: () => import('@/views/admin/GateSimulator.vue'), meta: { roles: ['admin'] } },
      { path: 'faces', name: 'FaceManage', component: () => import('@/views/admin/FaceManage.vue'), meta: { roles: ['admin'] } },
      { path: 'access', name: 'AccessRecords', component: () => import('@/views/admin/AccessRecords.vue'), meta: { roles: ['admin'] } },
      { path: 'abnormals', name: 'AbnormalCenter', component: () => import('@/views/admin/AbnormalCenter.vue'), meta: { roles: ['admin'] } },
      { path: 'statistics', name: 'Statistics', component: () => import('@/views/admin/Statistics.vue'), meta: { roles: ['admin'] } },
      { path: 'users', name: 'Users', component: () => import('@/views/admin/Users.vue'), meta: { roles: ['admin'] } },
      { path: 'logs', name: 'Logs', component: () => import('@/views/admin/Logs.vue'), meta: { roles: ['admin'] } },

      // ============ 辅导员 ============
      { path: 'counselor/dashboard', name: 'CounselorDashboard', component: () => import('@/views/counselor/CounselorDashboard.vue'), meta: { roles: ['counselor'] } },
      { path: 'counselor/students', name: 'CounselorStudents', component: () => import('@/views/counselor/CounselorStudents.vue'), meta: { roles: ['counselor'] } },
      { path: 'counselor/presence', name: 'CounselorPresence', component: () => import('@/views/counselor/CounselorPresence.vue'), meta: { roles: ['counselor'] } },
      { path: 'counselor/access', name: 'CounselorAccess', component: () => import('@/views/counselor/CounselorAccess.vue'), meta: { roles: ['counselor'] } },
      { path: 'counselor/abnormals', name: 'CounselorAbnormals', component: () => import('@/views/counselor/CounselorAbnormals.vue'), meta: { roles: ['counselor'] } },

      // ============ 学生 ============
      { path: 'student/home', name: 'StudentHome', component: () => import('@/views/student/StudentHome.vue'), meta: { roles: ['student'] } },
      { path: 'student/info', name: 'StudentInfo', component: () => import('@/views/student/StudentInfo.vue'), meta: { roles: ['student'] } },
      { path: 'student/face', name: 'StudentFace', component: () => import('@/views/student/StudentFace.vue'), meta: { roles: ['student'] } },
      { path: 'student/records', name: 'StudentRecords', component: () => import('@/views/student/StudentRecords.vue'), meta: { roles: ['student'] } },

      // ============ 公共 ============
      { path: 'messages', name: 'Messages', component: () => import('@/views/common/Messages.vue'), meta: { roles: ['admin', 'counselor', 'student'] } },
      { path: 'profile', name: 'Profile', component: () => import('@/views/common/Profile.vue'), meta: { roles: ['admin', 'counselor', 'student'] } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const store = useUserStore()

  if (to.meta.public) {
    if (store.isLogin && to.path === '/login') {
      return next(store.homePath)
    }
    return next()
  }

  if (!store.isLogin) {
    return next('/login')
  }

  // 角色校验（前端仅做导航控制，真实权限由后端校验）
  const roles = to.meta.roles
  if (roles && roles.length && !roles.includes(store.role)) {
    return next(store.homePath)
  }

  next()
})

export default router
