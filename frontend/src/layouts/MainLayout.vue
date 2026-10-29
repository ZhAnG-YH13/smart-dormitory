<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="brand">
        <el-icon :size="22"><School /></el-icon>
        <span v-show="!collapsed" class="brand-text">智慧宿舍门禁</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        router
        background-color="#1f2d3d"
        text-color="#c0c4cc"
        active-text-color="#409eff"
        class="menu"
      >
        <template v-for="item in menus" :key="item.path">
          <el-sub-menu v-if="item.children" :index="item.path">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item v-for="c in item.children" :key="c.path" :index="c.path">
              {{ c.title }}
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <span class="page-name">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <el-badge :value="store.unreadCount" :hidden="!store.unreadCount" class="msg-badge">
            <el-icon :size="20" class="icon-btn" @click="$router.push('/messages')"><Bell /></el-icon>
          </el-badge>
          <el-dropdown @command="onCommand">
            <span class="user-info">
              <el-avatar :size="30">{{ (store.user?.real_name || '?').slice(0, 1) }}</el-avatar>
              <span class="user-name">{{ store.user?.real_name }}</span>
              <el-tag size="small" type="info">{{ store.roleName }}</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>

  <el-dialog v-model="pwdVisible" title="修改密码" width="420px">
    <el-form :model="pwdForm" label-width="90px">
      <el-form-item label="原密码">
        <el-input v-model="pwdForm.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少6位" />
      </el-form-item>
      <el-form-item label="确认密码">
        <el-input v-model="pwdForm.confirm" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwdVisible = false">取消</el-button>
      <el-button type="primary" :loading="pwdLoading" @click="submitPassword">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/api'

const store = useUserStore()
const route = useRoute()
const router = useRouter()

const collapsed = ref(false)
const pwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdForm = ref({ old_password: '', new_password: '', confirm: '' })

const adminMenus = [
  { path: '/dashboard', title: '首页', icon: 'HomeFilled' },
  {
    path: '/students-group', title: '学生管理', icon: 'User',
    children: [
      { path: '/students', title: '学生列表' },
      { path: '/students/import', title: '批量导入' },
      { path: '/faces', title: '人脸注册情况' }
    ]
  },
  { path: '/organization', title: '组织管理', icon: 'OfficeBuilding' },
  { path: '/dormitory', title: '宿舍管理', icon: 'House' },
  {
    path: '/gate-group', title: '门禁管理', icon: 'VideoCamera',
    children: [
      { path: '/cameras', title: '摄像头' },
      { path: '/gate', title: '实时门禁/模拟' }
    ]
  },
  { path: '/access', title: '门禁记录', icon: 'Tickets' },
  { path: '/abnormals', title: '异常中心', icon: 'WarningFilled' },
  { path: '/statistics', title: '数据统计', icon: 'DataAnalysis' },
  {
    path: '/system-group', title: '系统管理', icon: 'Setting',
    children: [
      { path: '/users', title: '用户管理' },
      { path: '/logs', title: '操作日志' }
    ]
  },
  { path: '/messages', title: '消息中心', icon: 'ChatDotRound' }
]

const counselorMenus = [
  { path: '/counselor/dashboard', title: '首页', icon: 'HomeFilled' },
  { path: '/counselor/students', title: '我的班级', icon: 'User' },
  { path: '/counselor/presence', title: '在寝情况', icon: 'House' },
  { path: '/counselor/access', title: '门禁记录', icon: 'Tickets' },
  { path: '/counselor/abnormals', title: '异常记录', icon: 'WarningFilled' },
  { path: '/messages', title: '消息中心', icon: 'ChatDotRound' }
]

const studentMenus = [
  { path: '/student/home', title: '首页', icon: 'HomeFilled' },
  { path: '/student/info', title: '我的信息', icon: 'User' },
  { path: '/student/face', title: '人脸注册', icon: 'Avatar' },
  { path: '/student/records', title: '我的门禁记录', icon: 'Tickets' },
  { path: '/messages', title: '消息中心', icon: 'ChatDotRound' }
]

const menus = computed(() => {
  if (store.role === 'admin') return adminMenus
  if (store.role === 'counselor') return counselorMenus
  return studentMenus
})

const activeMenu = computed(() => route.path)

const titleMap = {
  '/dashboard': '首页',
  '/students': '学生列表',
  '/students/import': '批量导入学生',
  '/organization': '组织管理',
  '/dormitory': '宿舍管理',
  '/cameras': '摄像头管理',
  '/gate': '实时门禁 / 模拟通行',
  '/faces': '人脸注册情况',
  '/access': '门禁记录',
  '/abnormals': '异常中心',
  '/statistics': '数据统计',
  '/users': '用户管理',
  '/logs': '操作日志',
  '/messages': '消息中心',
  '/profile': '个人中心',
  '/counselor/dashboard': '首页',
  '/counselor/students': '我的班级',
  '/counselor/presence': '在寝情况',
  '/counselor/access': '门禁记录',
  '/counselor/abnormals': '异常记录',
  '/student/home': '首页',
  '/student/info': '我的信息',
  '/student/face': '人脸注册',
  '/student/records': '我的门禁记录'
}

const currentTitle = computed(() => titleMap[route.path] || '智慧宿舍管理系统')

function onCommand(cmd) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
      .then(() => {
        store.logout()
        router.push('/login')
      })
      .catch(() => {})
  } else if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'password') {
    pwdForm.value = { old_password: '', new_password: '', confirm: '' }
    pwdVisible.value = true
  }
}

async function submitPassword() {
  if (!pwdForm.value.old_password || !pwdForm.value.new_password) {
    return ElMessage.warning('请填写完整')
  }
  if (pwdForm.value.new_password.length < 6) {
    return ElMessage.warning('新密码至少6位')
  }
  if (pwdForm.value.new_password !== pwdForm.value.confirm) {
    return ElMessage.warning('两次密码不一致')
  }
  pwdLoading.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: pwdForm.value.old_password,
      new_password: pwdForm.value.new_password
    })
    ElMessage.success('密码修改成功')
    pwdVisible.value = false
  } finally {
    pwdLoading.value = false
  }
}

onMounted(() => {
  store.fetchMe().catch(() => {})
  store.fetchUnread()
})
</script>

<style scoped>
.layout {
  height: 100%;
}

.aside {
  background: #1f2d3d;
  transition: width 0.25s;
  overflow-x: hidden;
}

.brand {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px;
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-text {
  font-size: 15px;
}

.menu {
  border-right: none;
}

.header {
  height: 56px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.page-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.icon-btn {
  cursor: pointer;
  color: #606266;
}

.msg-badge {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.user-name {
  font-size: 14px;
  color: #303133;
}

.main {
  padding: 18px;
  background: #f5f7fa;
  overflow-y: auto;
}
</style>
