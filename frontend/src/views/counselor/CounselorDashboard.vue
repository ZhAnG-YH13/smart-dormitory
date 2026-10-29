<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">首页概览</h2>
      <span class="text-muted">欢迎回来，{{ store.user?.real_name || '' }}</span>
    </div>

    <div class="stat-grid">
      <div v-for="c in cards" :key="c.label" class="stat-card">
        <div class="label">{{ c.label }}</div>
        <div class="value">{{ c.value }}<small v-if="c.unit">{{ c.unit }}</small></div>
      </div>
    </div>

    <div class="page-card mt-16">
      <div class="page-header">
        <h2 class="page-title">我的班级</h2>
        <span class="text-muted">共 {{ classes.length }} 个班级</span>
      </div>

      <el-empty v-if="!classes.length && !loading" description="暂未负责班级" :image-size="90" />

      <div v-else v-loading="loading" class="class-grid">
        <div v-for="c in classes" :key="c.class_id" class="class-item">
          <div class="class-head">
            <span class="class-name">{{ c.class_name }}</span>
            <el-tag size="small" :type="rateTagType(c.face_register_rate)">
              {{ pct(c.face_register_rate) }}%
            </el-tag>
          </div>
          <div class="class-meta text-muted">
            学生 {{ c.total_students }} 人 · 已注册 {{ c.face_registered }} 人
          </div>
          <el-progress
            :percentage="pct(c.face_register_rate)"
            :stroke-width="10"
            :status="c.face_register_rate >= 1 ? 'success' : undefined"
          />
        </div>
      </div>
    </div>

    <div class="page-card mt-16">
      <h2 class="page-title">快捷入口</h2>
      <div class="quick-actions">
        <el-button type="primary" plain @click="$router.push('/counselor/students')">
          <el-icon><User /></el-icon>我的班级
        </el-button>
        <el-button type="success" plain @click="$router.push('/counselor/presence')">
          <el-icon><House /></el-icon>在寝情况
        </el-button>
        <el-button type="warning" plain @click="$router.push('/counselor/abnormals')">
          <el-icon><WarningFilled /></el-icon>异常记录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const stats = ref({})
const classes = ref([])
const loading = ref(false)

const cards = computed(() => {
  const s = stats.value
  const total = s.total_students ?? 0
  const registered = s.face_registered ?? 0
  return [
    { label: '本班学生数', value: total, unit: '人' },
    { label: '当前在寝', value: s.present_count ?? 0, unit: '人' },
    { label: '今日通行', value: s.today_total ?? 0, unit: '次' },
    { label: '未注册人脸数', value: Math.max(total - registered, 0), unit: '人' },
    { label: '待处理异常', value: s.pending_abnormal ?? 0, unit: '条' }
  ]
})

function pct(rate) {
  const n = Number(rate || 0) * 100
  return Math.round(n * 10) / 10
}

function rateTagType(rate) {
  if (rate >= 0.9) return 'success'
  if (rate >= 0.6) return 'warning'
  return 'danger'
}

async function loadData() {
  loading.value = true
  try {
    const [dashboard, classRes] = await Promise.all([
      api.get('/stats/dashboard'),
      api.get('/stats/classes')
    ])
    stats.value = dashboard || {}
    classes.value = classRes?.classes || []
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.class-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 16px;
}

.class-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.class-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
}

.class-meta {
  margin-bottom: 10px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 14px;
}
</style>
