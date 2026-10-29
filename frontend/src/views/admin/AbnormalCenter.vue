<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">异常中心</h2>
      <div>
        <el-button type="warning" :loading="simulating" @click="simulateAbnormal">
          <el-icon><WarningFilled /></el-icon>模拟生成异常
        </el-button>
        <el-button @click="loadAll"><el-icon><Refresh /></el-icon>刷新</el-button>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="异常闭环：产生 → 记录 → 自动反馈 → 处理 → 关闭。系统检测到异常后自动记录并通知管理员，处理过程全程留痕。"
    />

    <div class="stat-grid mt-16">
      <div class="stat-card">
        <div class="label">异常总数</div>
        <div class="value">{{ stats.total ?? 0 }}<small>条</small></div>
      </div>
      <div class="stat-card" style="border-left-color: #f56c6c">
        <div class="label">待处理</div>
        <div class="value">{{ stats.pending ?? 0 }}<small>条</small></div>
      </div>
      <div class="stat-card" style="border-left-color: #e6a23c">
        <div class="label">处理中</div>
        <div class="value">{{ stats.processing ?? 0 }}<small>条</small></div>
      </div>
      <div class="stat-card" style="border-left-color: #67c23a">
        <div class="label">已解决</div>
        <div class="value">{{ stats.resolved ?? 0 }}<small>条</small></div>
      </div>
    </div>

    <div class="page-card mt-16">
      <div class="resolve-head">
        <span class="resolve-label">异常解决率</span>
        <b class="resolve-value">{{ percent(stats.resolve_rate) }}</b>
      </div>
      <el-progress
        :percentage="ratePercent(stats.resolve_rate)"
        :stroke-width="14"
        :color="rateColor(stats.resolve_rate)"
      />
      <div class="text-muted" style="margin-top: 6px">
        已解决与已关闭的异常占比，已关闭 {{ stats.closed ?? 0 }} 条
      </div>
    </div>

    <div class="page-card mt-16">
      <div class="toolbar">
        <el-select v-model="query.event_type" placeholder="全部异常类型" clearable style="width: 170px">
          <el-option label="设备异常" value="device_error" />
          <el-option label="图像质量异常" value="image_quality" />
          <el-option label="AI识别异常" value="ai_recognition" />
          <el-option label="业务异常" value="business" />
        </el-select>
        <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 150px">
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="已解决" value="resolved" />
          <el-option label="已关闭" value="closed" />
          <el-option label="自动恢复" value="auto_recovered" />
        </el-select>
        <el-select v-model="query.severity" placeholder="全部等级" clearable style="width: 130px">
          <el-option label="低" :value="1" />
          <el-option label="中" :value="2" />
          <el-option label="高" :value="3" />
        </el-select>
        <el-input
          v-model="query.keyword"
          placeholder="异常编号 / 原因 / 摄像头 / 学号"
          clearable
          style="width: 240px"
          @keyup.enter="onSearch"
        />
        <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>搜索</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>

      <el-table :data="displayList" v-loading="loading" stripe border>
        <el-table-column label="异常编号" prop="event_no" width="180" />
        <el-table-column label="类型" width="140" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.event_type)" size="small">{{ typeLabel(row.event_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="异常原因" prop="event_reason" min-width="160" show-overflow-tooltip />
        <el-table-column label="摄像头" prop="camera_code" width="110" />
        <el-table-column label="学号" width="130">
          <template #default="{ row }">{{ row.student_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="等级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="自动反馈" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.auto_feedback_sent ? 'success' : 'info'" size="small">
              {{ row.auto_feedback_sent ? '已通知' : '未通知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发生时间" width="170">
          <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column label="处理数" prop="handles_count" width="80" align="center" />
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button
              v-if="row.status !== 'resolved' && row.status !== 'closed'"
              link
              type="warning"
              @click="openHandle(row)"
            >
              处理
            </el-button>
            <el-button v-if="row.status !== 'closed'" link type="danger" @click="onClose(row)">关闭</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="异常详情" width="760px">
      <div v-loading="detailLoading">
        <template v-if="detail.id">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="异常编号">{{ detail.event_no }}</el-descriptions-item>
            <el-descriptions-item label="异常类型">
              <el-tag :type="typeTagType(detail.event_type)" size="small">{{ typeLabel(detail.event_type) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="等级">
              <el-tag :type="severityTagType(detail.severity)" size="small">{{ severityLabel(detail.severity) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTagType(detail.status)" size="small">{{ statusLabel(detail.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="摄像头">{{ detail.camera_code || '-' }}</el-descriptions-item>
            <el-descriptions-item label="学号">{{ detail.student_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="自动反馈">
              <el-tag :type="detail.auto_feedback_sent ? 'success' : 'info'" size="small">
                {{ detail.auto_feedback_sent ? '已自动通知管理员' : '未通知' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="发生时间">{{ formatTime(detail.occurred_at) }}</el-descriptions-item>
            <el-descriptions-item label="异常原因" :span="2">{{ detail.event_reason || '-' }}</el-descriptions-item>
            <el-descriptions-item label="详细描述" :span="2">{{ detail.event_detail || '-' }}</el-descriptions-item>
          </el-descriptions>

          <div class="section-title mt-16">处理记录（{{ detailHandles.length }}）</div>
          <el-table :data="detailHandles" border size="small" max-height="260">
            <el-table-column label="处理人" prop="handler_name" width="100" />
            <el-table-column label="处理方式" prop="handle_type" width="100" />
            <el-table-column label="处理结果" prop="handle_result" width="120" />
            <el-table-column label="说明" prop="handle_note" min-width="160" show-overflow-tooltip />
            <el-table-column label="处理时间" width="160">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </template>
        <el-empty v-else description="暂无详情" :image-size="80" />
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="handleVisible" title="处理异常" width="520px">
      <el-form label-width="90px">
        <el-form-item label="处理结果">
          <el-select v-model="handleForm.handle_result" style="width: 100%">
            <el-option label="已恢复" value="已恢复" />
            <el-option label="已重启设备" value="已重启设备" />
            <el-option label="已调整设备" value="已调整设备" />
            <el-option label="已通知维修" value="已通知维修" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input
            v-model="handleForm.handle_note"
            type="textarea"
            :rows="4"
            placeholder="请填写处理过程或说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleVisible = false">取消</el-button>
        <el-button type="primary" :loading="handleLoading" @click="submitHandle">提交处理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const stats = ref({})
const query = reactive({ event_type: '', status: '', severity: '', keyword: '' })
const simulating = ref(false)

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref({})
const detailHandles = ref([])

const handleVisible = ref(false)
const handleLoading = ref(false)
const handleForm = reactive({ event_id: null, handle_result: '已恢复', handle_note: '' })

const typeMap = {
  device_error: { label: '设备异常', type: 'danger' },
  image_quality: { label: '图像质量异常', type: 'warning' },
  ai_recognition: { label: 'AI识别异常', type: 'warning' },
  business: { label: '业务异常', type: 'info' }
}
const statusMap = {
  pending: { label: '待处理', type: 'danger' },
  processing: { label: '处理中', type: 'warning' },
  resolved: { label: '已解决', type: 'success' },
  closed: { label: '已关闭', type: 'info' },
  auto_recovered: { label: '自动恢复', type: 'success' }
}
const severityMap = {
  1: { label: '低', type: 'info' },
  2: { label: '中', type: 'warning' },
  3: { label: '高', type: 'danger' }
}

function typeLabel(v) {
  return typeMap[v]?.label || v || '-'
}
function typeTagType(v) {
  return typeMap[v]?.type || 'info'
}
function statusLabel(v) {
  return statusMap[v]?.label || v || '-'
}
function statusTagType(v) {
  return statusMap[v]?.type || 'info'
}
function severityLabel(v) {
  return severityMap[Number(v)]?.label || '-'
}
function severityTagType(v) {
  return severityMap[Number(v)]?.type || 'info'
}
function percent(v) {
  if (v === null || v === undefined || v === '') return '-'
  return `${(Number(v) * 100).toFixed(1)}%`
}
function ratePercent(v) {
  const n = Number(v)
  if (Number.isNaN(n)) return 0
  return Math.max(0, Math.min(100, Math.round(n * 100)))
}
function rateColor(v) {
  const n = Number(v) || 0
  if (n >= 0.8) return '#67c23a'
  if (n >= 0.5) return '#e6a23c'
  return '#f56c6c'
}
function formatTime(v) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

const displayList = computed(() => {
  const kw = (query.keyword || '').trim().toLowerCase()
  if (!kw) return list.value
  return list.value.filter(e =>
    [e.event_no, e.event_reason, e.event_detail, e.camera_code, e.student_no]
      .some(v => String(v || '').toLowerCase().includes(kw))
  )
})

async function loadStats() {
  try {
    stats.value = await api.get('/stats/abnormals')
  } catch (e) {
    stats.value = {}
  }
}

async function loadList() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.event_type) params.event_type = query.event_type
    if (query.status) params.status = query.status
    if (query.severity) params.severity = query.severity
    if (query.keyword) params.keyword = query.keyword
    const res = await api.get('/abnormals', { params })
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  loadList()
}
function onReset() {
  Object.assign(query, { event_type: '', status: '', severity: '', keyword: '' })
  onSearch()
}

async function openDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = {}
  detailHandles.value = []
  try {
    const res = await api.get(`/abnormals/${row.id}`)
    const ev = res.event || res
    detail.value = ev
    detailHandles.value = res.handles || res.details || ev.handles || ev.details || []
  } catch (e) {
    detail.value = {}
  } finally {
    detailLoading.value = false
  }
}

function openHandle(row) {
  handleForm.event_id = row.id
  handleForm.handle_result = '已恢复'
  handleForm.handle_note = ''
  handleVisible.value = true
}

async function submitHandle() {
  if (!handleForm.event_id) return
  handleLoading.value = true
  try {
    await api.post(`/abnormals/${handleForm.event_id}/handle`, {
      handle_result: handleForm.handle_result,
      handle_note: handleForm.handle_note
    })
    ElMessage.success('异常已处理')
    handleVisible.value = false
    loadAll()
    if (detailVisible.value) openDetail({ id: handleForm.event_id })
  } catch (e) {
    /* 错误提示由拦截器处理 */
  } finally {
    handleLoading.value = false
  }
}

function onClose(row) {
  ElMessageBox.confirm(
    `确定关闭异常「${row.event_no}」吗？关闭后不可再处理。`,
    '关闭确认',
    { type: 'warning', confirmButtonText: '确定关闭', cancelButtonText: '取消' }
  )
    .then(async () => {
      try {
        await api.post(`/abnormals/${row.id}/close`, {
          handle_note: '管理员手动关闭',
          note: '管理员手动关闭'
        })
        ElMessage.success('异常已关闭')
        loadAll()
        if (detailVisible.value && detail.value.id === row.id) openDetail(row)
      } catch (e) {
        /* 忽略 */
      }
    })
    .catch(() => {})
}

async function simulateAbnormal() {
  simulating.value = true
  try {
    await api.post('/abnormals', {
      event_type: 'device_error',
      event_reason: '连续60秒未收到视频帧',
      camera_code: 'CAM001',
      severity: 3,
      event_detail: 'CAM001 视频流中断，系统自动检测'
    })
    ElMessage.success('已生成异常并自动通知管理员')
    loadAll()
  } catch (e) {
    /* 错误提示由拦截器处理 */
  } finally {
    simulating.value = false
  }
}

function loadAll() {
  loadStats()
  loadList()
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.resolve-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.resolve-label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
}

.resolve-value {
  font-size: 20px;
  color: #409eff;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 10px;
}
</style>
