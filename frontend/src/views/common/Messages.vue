<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">消息中心</h2>
      <el-button type="primary" plain :disabled="!store.unreadCount" @click="readAll">
        <el-icon><Select /></el-icon>全部标为已读
      </el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :sm="6">
        <div class="page-card">
          <div class="filter-title">筛选</div>
          <el-radio-group v-model="readFilter" class="filter-group" @change="onFilterChange">
            <el-radio label="all">全部</el-radio>
            <el-radio label="unread">未读</el-radio>
          </el-radio-group>
          <el-select
            v-model="messageType"
            placeholder="全部消息类型"
            clearable
            class="mt-16"
            style="width: 100%"
            @change="onFilterChange"
          >
            <el-option v-for="(item, key) in typeMap" :key="key" :label="item.label" :value="key" />
          </el-select>
          <div class="text-muted mt-16">未读消息：{{ store.unreadCount }} 条</div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="18">
        <div class="page-card">
          <div v-loading="loading">
            <el-empty v-if="!list.length" description="暂无消息" />

            <div
              v-for="m in list"
              :key="m.id"
              class="msg-card"
              :class="{ unread: !m.is_read }"
              @click="toggle(m)"
            >
              <div class="msg-head">
                <span v-if="!m.is_read" class="dot"></span>
                <el-tag :type="typeInfo(m.message_type).tag" size="small">
                  {{ typeInfo(m.message_type).label }}
                </el-tag>
                <span class="msg-title">{{ m.title }}</span>
                <span class="msg-time text-muted">{{ fmtTime(m.created_at) }}</span>
              </div>
              <div v-if="expanded.includes(m.id)" class="msg-body">
                <div class="msg-content">{{ m.content || '无详细内容' }}</div>
                <div v-if="m.read_at" class="text-muted mt-16">阅读时间：{{ fmtTime(m.read_at) }}</div>
              </div>
            </div>
          </div>

          <div class="pagination">
            <el-pagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50]"
              :total="total"
              layout="total, sizes, prev, pager, next"
              background
              @size-change="load"
              @current-change="load"
            />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const store = useUserStore()

const typeMap = {
  system_notice: { label: '系统通知', tag: 'info' },
  info_complete_reminder: { label: '信息完善提醒', tag: 'warning' },
  face_register_reminder: { label: '人脸注册提醒', tag: 'warning' },
  device_error: { label: '设备异常', tag: 'danger' },
  face_verify_error: { label: '人脸验证异常', tag: 'danger' },
  access_abnormal: { label: '门禁异常', tag: 'danger' },
  handle_result: { label: '处理结果', tag: 'success' }
}

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const readFilter = ref('all')
const messageType = ref('')
const expanded = ref([])

function typeInfo(type) {
  return typeMap[type] || { label: type || '其他', tag: 'info' }
}

function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (messageType.value) params.message_type = messageType.value
    if (readFilter.value === 'unread') params.is_read = false
    const res = await api.get('/messages', { params })
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.value = false
}

function onFilterChange() {
  page.value = 1
  expanded.value = []
  load()
}

async function toggle(m) {
  const idx = expanded.value.indexOf(m.id)
  if (idx > -1) {
    expanded.value.splice(idx, 1)
    return
  }
  expanded.value.push(m.id)
  if (!m.is_read) {
    try {
      await api.post(`/messages/${m.id}/read`)
      m.is_read = true
      m.read_at = new Date().toISOString()
      store.fetchUnread()
    } catch (e) {
      /* 错误已由请求拦截器提示 */
    }
  }
}

async function readAll() {
  try {
    await api.post('/messages/read-all')
    ElMessage.success('已将全部消息标为已读')
    store.fetchUnread()
    load()
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
}

onMounted(() => {
  load()
  store.fetchUnread()
})
</script>

<style scoped>
.filter-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 12px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.msg-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.msg-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.12);
}

.msg-card.unread {
  background: #fafcff;
}

.msg-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  flex-shrink: 0;
}

.msg-title {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.msg-card.unread .msg-title {
  font-weight: 600;
}

.msg-time {
  flex-shrink: 0;
}

.msg-body {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #ebeef5;
}

.msg-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
