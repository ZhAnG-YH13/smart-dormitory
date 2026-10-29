<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">个人中心</h2>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <div class="page-card" v-loading="loading">
          <div class="profile-head">
            <el-avatar :size="72" class="avatar">{{ initial }}</el-avatar>
            <div class="profile-meta">
              <div class="profile-name">{{ profile.real_name || profile.username || '-' }}</div>
              <el-tag size="small" type="info">{{ roleText(profile.role) }}</el-tag>
            </div>
          </div>

          <el-descriptions :column="1" border class="mt-16">
            <el-descriptions-item label="用户名">{{ profile.username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ profile.real_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ roleText(profile.role) }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ profile.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ profile.email || '-' }}</el-descriptions-item>
            <el-descriptions-item v-if="isStudent" label="信息完整度">
              <el-progress :percentage="infoPercent" :stroke-width="14" />
            </el-descriptions-item>
            <el-descriptions-item v-if="isStudent" label="人脸注册">
              <el-tag :type="profile.face_registered ? 'success' : 'warning'" size="small">
                {{ profile.face_registered ? '已注册' : '未注册' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="isCounselor" label="负责班级">
              {{ profile.class_info?.name || '暂未分配' }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="isStudent" class="quick mt-16">
            <el-button type="primary" @click="$router.push('/student/info')">
              <el-icon><Edit /></el-icon>去完善信息
            </el-button>
            <el-button type="success" @click="$router.push('/student/face')">
              <el-icon><Camera /></el-icon>去人脸注册
            </el-button>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :md="10">
        <div class="page-card">
          <div class="card-title">修改密码</div>
          <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 6 位" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm">
              <el-input v-model="pwdForm.confirm" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="submitPwd">保存修改</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const store = useUserStore()

const loading = ref(false)
const submitting = ref(false)
const profile = ref({})

const pwdFormRef = ref(null)
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

const isStudent = computed(() => profile.value.role === 'student')
const isCounselor = computed(() => profile.value.role === 'counselor')
const initial = computed(() => (profile.value.real_name || profile.value.username || 'U').slice(0, 1))
const infoPercent = computed(() => Math.min(100, Math.max(0, Number(profile.value.info_complete) || 0)))

function roleText(role) {
  const map = { admin: '管理员', counselor: '辅导员', student: '学生' }
  return map[role] || role || '-'
}

async function loadProfile() {
  loading.value = true
  try {
    const data = await store.fetchMe()
    profile.value = data || {}
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.value = false
}

async function submitPwd() {
  const ok = await pwdFormRef.value.validate().catch(() => false)
  if (!ok) return
  submitting.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password
    })
    ElMessage.success('密码修改成功')
    pwdFormRef.value.resetFields()
    store.fetchMe().catch(() => {})
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  submitting.value = false
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-head {
  display: flex;
  align-items: center;
  gap: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.avatar {
  background: #1e3c72;
  color: #fff;
  font-size: 28px;
  font-weight: 600;
}

.profile-name {
  font-size: 20px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
  margin: 0 0 16px;
}

.quick {
  display: flex;
  gap: 10px;
}
</style>
