<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand-block">
        <el-icon :size="46"><School /></el-icon>
        <h1>智慧宿舍人脸门禁与学生管理系统</h1>
        <p>人工智能 + 计算机视觉 + Web 全流程业务闭环</p>
        <ul class="feature-list">
          <li><el-icon><Check /></el-icon> 学生信息批量导入与账号自动创建</li>
          <li><el-icon><Check /></el-icon> 人脸检测、质量评估、特征提取与验证</li>
          <li><el-icon><Check /></el-icon> 摄像头 IN / OUT 方向与在寝状态推断</li>
          <li><el-icon><Check /></el-icon> 异常自动检测、反馈与处理闭环</li>
        </ul>
      </div>
    </div>

    <div class="login-right">
      <div class="login-box">
        <h2>系统登录</h2>
        <p class="sub">请使用学号 / 工号登录</p>

        <el-form :model="form" @submit.prevent="onSubmit">
          <el-form-item>
            <el-input v-model="form.username" size="large" placeholder="用户名 / 学号" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              show-password
              placeholder="密码"
              :prefix-icon="Lock"
              @keyup.enter="onSubmit"
            />
          </el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="onSubmit">
            登录
          </el-button>
        </el-form>

        <el-alert
          class="tip"
          title="演示账号"
          type="info"
          :closable="false"
          show-icon
        >
          <div class="demo-line">管理员：admin / admin123</div>
          <div class="demo-line">辅导员：counselor01 / 123456</div>
          <div class="demo-line">学生：20231001 / 123456</div>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const form = ref({ username: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  if (!form.value.username || !form.value.password) {
    return ElMessage.warning('请输入用户名和密码')
  }
  loading.value = true
  try {
    const data = await store.login(form.value.username, form.value.password)
    ElMessage.success(`欢迎回来，${data.user.real_name}`)
    if (data.must_change_password) {
      ElMessage.warning('首次登录，请及时修改初始密码')
    }
    router.push(store.homePath)
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
}

.login-left {
  flex: 1.2;
  background: linear-gradient(135deg, #1f2d3d 0%, #2d4a68 60%, #3a6ea5 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.brand-block {
  max-width: 520px;
}

.brand-block h1 {
  font-size: 30px;
  line-height: 1.4;
  margin: 20px 0 12px;
}

.brand-block p {
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 28px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  color: rgba(255, 255, 255, 0.88);
  font-size: 14px;
}

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.login-box {
  width: 380px;
  background: #fff;
  border-radius: 14px;
  padding: 34px 32px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.login-box h2 {
  margin: 0 0 6px;
  font-size: 22px;
  color: #1f2d3d;
}

.sub {
  color: #909399;
  font-size: 13px;
  margin: 0 0 22px;
}

.tip {
  margin-top: 20px;
}

.demo-line {
  font-size: 12px;
  line-height: 1.8;
  color: #606266;
}
</style>
