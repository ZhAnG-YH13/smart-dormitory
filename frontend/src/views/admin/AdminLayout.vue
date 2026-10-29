<template>
  <div class="layout-container">
    <aside class="sidebar">
      <div class="sidebar-logo">智慧宿舍</div>
      <el-menu
        :default-active="activeMenu"
        background-color="#001529"
        text-color="rgba(255,255,255,0.7)"
        active-text-color="#fff"
        router
        :collapse="collapse"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><Odometer /></el-icon><span>首页概览</span>
        </el-menu-item>

        <el-sub-menu index="student">
          <template #title><el-icon><User /></el-icon><span>学生管理</span></template>
          <el-menu-item index="/admin/students">学生列表</el-menu-item>
          <el-menu-item index="/admin/students/import">学生导入</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="org">
          <template #title><el-icon><OfficeBuilding /></el-icon><span>组织架构</span></template>
          <el-menu-item index="/admin/colleges">学院管理</el-menu-item>
          <el-menu-item index="/admin/majors">专业管理</el-menu-item>
          <el-menu-item index="/admin/grades">年级管理</el-menu-item>
          <el-menu-item index="/admin/classes">班级管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="dorm">
          <template #title><el-icon><House /></el-icon><span>宿舍管理</span></template>
          <el-menu-item index="/admin/buildings">楼栋管理</el-menu-item>
          <el-menu-item index="/admin/rooms">房间管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="device">
          <template #title><el-icon><VideoCamera /></el-icon><span>设备管理</span></template>
          <el-menu-item index="/admin/cameras">摄像头列表</el-menu-item>
          <el-menu-item index="/admin/cameras/monitor">实时监控</el-menu-item>
          <el-menu-item index="/admin/faces">人脸库</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="access">
          <template #title><el-icon><Key /></el-icon><span>门禁与异常</span></template>
          <el-menu-item index="/admin/access">门禁记录</el-menu-item>
          <el-menu-item index="/admin/abnormals">异常告警</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/admin/stats">
          <el-icon><DataAnalysis /></el-icon><span>数据统计</span>
        </el-menu-item>

        <el-sub-menu index="sys">
          <template #title><el-icon><Setting /></el-icon><span>系统管理</span></template>
          <el-menu-item index="/admin/users">用户管理</el-menu-item>
          <el-menu-item index="/admin/messages">消息通知</el-menu-item>
          <el-menu-item index="/admin/logs">操作日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </aside>

    <div class="main-wrapper">
      <header class="header">
        <div style="display:flex;align-items:center;gap:12px;">
          <el-icon :size="20" style="cursor:pointer;" @click="collapse = !collapse"><Fold v-if="!collapse" /><Expand v-else /></el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>管理后台</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div style="display:flex;align-items:center;gap:16px;">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="item" @click="router.push('/admin/messages')">
            <el-icon :size="20" style="cursor:pointer;"><Bell /></el-icon>
          </el-badge>
          <el-dropdown>
            <span style="cursor:pointer;display:flex;align-items:center;gap:8px;">
              <el-avatar :size="32" :style="{background:'#1e3c72'}">{{ userStore.realName.charAt(0) }}</el-avatar>
              <span>{{ userStore.realName }}</span>
              <el-tag size="small" type="danger">管理员</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="showChangePwd = true">
                  <el-icon><Lock /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided @click="onLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>

    <el-dialog v-model="showChangePwd" title="修改密码" width="420px">
      <el-form ref="pwdRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePwd = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitPwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { changePassword } from '@/api/auth'
import { getUnreadCount } from '@/api/messages'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapse = ref(false)
const activeMenu = computed(() => route.path)

const unreadCount = ref(0)
async function loadUnread() {
  try {
    const res = await getUnreadCount()
    const data = res.data ?? res
    unreadCount.value = typeof data === 'number' ? data : (data.count || 0)
  } catch (e) { /* ignore */ }
}

const showChangePwd = ref(false)
const pwdRef = ref(null)
const pwdLoading = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '' })
const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [{ required: true, min: 6, message: '新密码至少6位', trigger: 'blur' }]
}

async function submitPwd() {
  const ok = await pwdRef.value.validate().catch(() => false)
  if (!ok) return
  pwdLoading.value = true
  try {
    await changePassword(pwdForm)
    ElMessage.success('密码修改成功，请重新登录')
    showChangePwd.value = false
    onLogout()
  } catch (e) { /* ignore */ }
  pwdLoading.value = false
}

function onLogout() {
  ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' }).then(() => {
    userStore.logout()
    router.replace('/login')
  }).catch(() => {})
}

onMounted(() => loadUnread())
</script>
