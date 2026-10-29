<template>
  <div>
    <div class="welcome-card">
      <div class="welcome-left">
        <el-avatar :size="52" class="avatar">{{ (me.real_name || store.user?.real_name || '?').slice(0, 1) }}</el-avatar>
        <div>
          <div class="welcome-title">欢迎，{{ me.real_name || store.user?.real_name || '' }} 同学</div>
          <div class="welcome-sub">学号：{{ studentNo }}</div>
        </div>
      </div>
      <div class="welcome-right">
        <el-button type="primary" plain @click="$router.push('/messages')">
          <el-icon><Bell /></el-icon>未读消息 {{ unread }}
        </el-button>
      </div>
    </div>

    <el-alert
      v-if="needGuide"
      class="mt-16"
      type="warning"
      :closable="false"
      show-icon
      title="请完善个人信息与人脸注册，以便正常使用门禁通行"
    >
      <div class="guide-line">
        <span v-if="infoPercent < 100">
          信息完整度 {{ infoPercent }}%，请前往
          <el-link type="primary" :underline="false" @click="$router.push('/student/info')">我的信息</el-link>
          补充资料。
        </span>
        <span v-if="!me.face_registered">
          尚未注册人脸，请前往
          <el-link type="primary" :underline="false" @click="$router.push('/student/face')">人脸注册</el-link>
          完成采集。
        </span>
      </div>
    </el-alert>

    <div class="status-grid mt-16">
      <div class="status-card" @click="$router.push('/student/info')">
        <div class="status-head">
          <el-icon :size="20" color="#409eff"><User /></el-icon>
          <span>信息完整度</span>
        </div>
        <el-progress
          :percentage="infoPercent"
          :stroke-width="12"
          :status="infoPercent >= 100 ? 'success' : undefined"
        />
        <div class="status-hint text-muted">点击前往我的信息</div>
      </div>

      <div class="status-card" @click="$router.push('/student/face')">
        <div class="status-head">
          <el-icon :size="20" color="#67c23a"><Avatar /></el-icon>
          <span>人脸注册状态</span>
        </div>
        <div class="face-status-line">
          <el-tag :type="faceTag.type" size="large">{{ faceTag.text }}</el-tag>
        </div>
        <div class="status-hint text-muted">点击前往人脸注册</div>
      </div>

      <div class="status-card">
        <div class="status-head">
          <el-icon :size="20" color="#e6a23c"><House /></el-icon>
          <span>当前在寝状态</span>
        </div>
        <div class="face-status-line">
          <el-tag :type="presentTag.type" size="large">{{ presentTag.text }}</el-tag>
        </div>
        <div class="status-hint text-muted">状态依据门禁记录推断</div>
      </div>
    </div>

    <div class="page-card mt-16">
      <div class="page-header">
        <h2 class="page-title">最近门禁记录</h2>
        <el-button link type="primary" @click="$router.push('/student/records')">查看全部</el-button>
      </div>

      <el-table v-loading="loading" :data="records" stripe border>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column label="宿舍楼" prop="building_name" min-width="110" show-overflow-tooltip />
        <el-table-column label="摄像头" prop="camera_code" min-width="130" show-overflow-tooltip />
        <el-table-column label="方向" width="90">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'IN' ? 'success' : 'warning'" size="small">
              {{ row.direction === 'IN' ? '进入' : '离开' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="相似度" width="100">
          <template #default="{ row }">{{ similarityText(row.similarity) }}</template>
        </el-table-column>
        <el-table-column label="验证结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.verify_result === 'success' ? 'success' : 'danger'" size="small">
              {{ row.verify_result === 'success' ? '通过' : '未通过' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const me = ref({})
const student = ref(null)
const records = ref([])
const presence = ref(null)
const unread = ref(0)
const loading = ref(false)

const FACE_MAP = {
  registered: { text: '已注册', type: 'success' },
  unregistered: { text: '未注册', type: 'info' },
  registering: { text: '注册中', type: 'warning' },
  failed: { text: '注册失败', type: 'danger' },
  cancelled: { text: '已注销', type: 'info' }
}

const studentNo = computed(() => student.value?.student_no || me.value.username || store.user?.username || '-')
const infoPercent = computed(() => Number(me.value.info_complete ?? 0))
const needGuide = computed(() => infoPercent.value < 100 || !me.value.face_registered)

const faceTag = computed(() => {
  if (me.value.face_registered) return FACE_MAP.registered
  return student.value?.face_status ? (FACE_MAP[student.value.face_status] || FACE_MAP.unregistered) : FACE_MAP.unregistered
})

const isPresent = computed(() => {
  if (presence.value) return !!presence.value.is_present
  if (records.value.length) return records.value[0].direction === 'IN'
  return null
})

const presentTag = computed(() => {
  if (isPresent.value === true) return { text: '在寝', type: 'success' }
  if (isPresent.value === false) return { text: '不在寝', type: 'warning' }
  return { text: '暂无记录', type: 'info' }
})

function formatTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

function similarityText(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return `${(n * 100).toFixed(1)}%`
}

async function loadData() {
  loading.value = true
  try {
    const [meRes, studentRes, recordsRes, presenceRes] = await Promise.allSettled([
      api.get('/auth/me'),
      api.get('/students', { params: { page: 1, limit: 1 } }),
      api.get('/access/records', { params: { page: 1, limit: 10 } }),
      api.get('/presence', { params: { page: 1, limit: 50 } })
    ])

    if (meRes.status === 'fulfilled') me.value = meRes.value || {}
    if (studentRes.status === 'fulfilled') student.value = (studentRes.value?.items || [])[0] || null
    if (recordsRes.status === 'fulfilled') records.value = recordsRes.value?.items || []
    if (presenceRes.status === 'fulfilled') presence.value = (presenceRes.value?.items || [])[0] || null

    try {
      const unreadRes = await api.get('/messages/unread-count')
      unread.value = unreadRes?.unread_count ?? unreadRes?.count ?? 0
    } catch (e) {
      unread.value = 0
    }

    if (me.value.info_complete !== undefined) store.infoComplete = me.value.info_complete
    if (me.value.face_registered !== undefined) store.faceRegistered = !!me.value.face_registered
    store.unreadCount = unread.value
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.welcome-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
  background: linear-gradient(135deg, #1f2d3d 0%, #2d4a68 60%, #3a6ea5 100%);
  color: #fff;
  border-radius: 12px;
  padding: 24px 26px;
}

.welcome-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  background: rgba(255, 255, 255, 0.25);
  font-size: 22px;
}

.welcome-title {
  font-size: 20px;
  font-weight: 600;
}

.welcome-sub {
  font-size: 13px;
  opacity: 0.8;
  margin-top: 6px;
}

.guide-line {
  font-size: 13px;
  line-height: 1.8;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.status-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.status-card:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

.status-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 14px;
}

.face-status-line {
  min-height: 40px;
  display: flex;
  align-items: center;
}

.status-hint {
  margin-top: 10px;
}
</style>
