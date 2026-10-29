<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-title">智慧宿舍人脸门禁系统</div>
      <div class="login-subtitle">Smart Dormitory Access Control</div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password :prefix-icon="Lock" @keyup.enter="submit" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%;" :loading="loading" @click="submit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <el-alert type="info" :closable="false" show-icon title="测试账号" style="margin-top:10px;">
        <template #default>
          <div style="font-size:13px;line-height:1.8;">
            <div><el-tag type="danger" size="small">管理员</el-tag> admin / admin123</div>
            <div><el-tag type="warning" size="small">辅导员</el-tag> counselor / counselor123</div>
            <div><el-tag type="success" size="small">学生</el-tag> student / student123</div>
          </div>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    if (redirect) {
      router.replace(redirect)
    } else {
      const role = userStore.role
      if (role === 'admin') router.replace('/admin/dashboard')
      else if (role === 'counselor') router.replace('/counselor/dashboard')
      else if (role === 'student') router.replace('/student/dashboard')
      else router.replace('/login')
    }
  } catch (e) {
    // 错误已在 request 拦截器提示
  } finally {
    loading.value = false
  }
}
</script>
