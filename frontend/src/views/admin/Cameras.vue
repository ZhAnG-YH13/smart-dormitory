<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">摄像头管理</h2>
      <div>
        <el-button @click="loadList"><el-icon><Refresh /></el-icon>刷新</el-button>
        <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>新增摄像头</el-button>
      </div>
    </div>

    <div class="page-card">
      <div class="toolbar">
        <el-input
          v-model="query.keyword"
          placeholder="编号 / 名称"
          clearable
          style="width: 200px"
          @keyup.enter="onSearch"
        />
        <el-select v-model="query.building_id" placeholder="全部宿舍楼" clearable style="width: 180px">
          <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="b.id" />
        </el-select>
        <el-select v-model="query.device_status" placeholder="全部设备状态" clearable style="width: 160px">
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
          <el-option label="异常" value="error" />
          <el-option label="维护" value="maintenance" />
        </el-select>
        <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>搜索</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="编号" prop="camera_code" width="120" />
        <el-table-column label="名称" prop="name" min-width="130" />
        <el-table-column label="位置" prop="location" min-width="140" show-overflow-tooltip />
        <el-table-column label="宿舍楼" prop="building_name" min-width="110" />
        <el-table-column label="方向" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'IN' ? 'success' : 'warning'" size="small">
              {{ row.direction === 'IN' ? '进入' : '离开' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="设备状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.device_status)" size="small">
              {{ statusLabel(row.device_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="FPS" width="80" align="center">
          <template #default="{ row }">{{ row.fps ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="识别成功率" width="110" align="center">
          <template #default="{ row }">{{ percent(row.recognition_success_rate) }}</template>
        </el-table-column>
        <el-table-column label="健康度" min-width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="healthPercent(row.health_score)"
              :stroke-width="8"
              :color="healthColor(row.health_score)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openStatus(row)">查看状态</el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
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

    <el-dialog v-model="formVisible" :title="editingId ? '编辑摄像头' : '新增摄像头'" width="580px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="编号" prop="camera_code">
              <el-input v-model="form.camera_code" placeholder="如 CAM001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input v-model="form.name" placeholder="如 1号楼大厅入口" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="宿舍楼">
              <el-select v-model="form.building_id" placeholder="请选择" clearable style="width: 100%">
                <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="b.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="方向" prop="direction">
              <el-select v-model="form.direction" style="width: 100%">
                <el-option label="进入 (IN)" value="IN" />
                <el-option label="离开 (OUT)" value="OUT" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="位置">
              <el-input v-model="form.location" placeholder="如 1号楼一层大厅" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="视频流地址">
              <el-input v-model="form.stream_url" placeholder="rtsp://..." />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备状态">
              <el-select v-model="form.device_status" style="width: 100%">
                <el-option label="在线" value="online" />
                <el-option label="离线" value="offline" />
                <el-option label="异常" value="error" />
                <el-option label="维护" value="maintenance" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="statusVisible" title="摄像头运行状态" width="620px">
      <div v-loading="statusLoading">
        <template v-if="status.camera">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="编号">{{ status.camera.camera_code }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ status.camera.name }}</el-descriptions-item>
            <el-descriptions-item label="位置">{{ status.camera.location || '-' }}</el-descriptions-item>
            <el-descriptions-item label="宿舍楼">{{ status.camera.building_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="方向">
              <el-tag :type="status.camera.direction === 'IN' ? 'success' : 'warning'" size="small">
                {{ status.camera.direction === 'IN' ? '进入' : '离开' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="设备状态">
              <el-tag :type="statusTagType(status.camera.device_status)" size="small">
                {{ statusLabel(status.camera.device_status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="心跳">
              <el-tag :type="status.heartbeat_ok ? 'success' : 'danger'" size="small">
                {{ status.heartbeat_ok ? '正常' : '超时' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="健康度">{{ status.health_score ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="识别成功率">{{ percent(status.camera.recognition_success_rate) }}</el-descriptions-item>
            <el-descriptions-item label="最后心跳">
              {{ formatTime(status.camera.last_heartbeat) }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="stat-grid mt-16">
            <div class="stat-card">
              <div class="label">今日通行</div>
              <div class="value">{{ status.today_total ?? 0 }}<small>次</small></div>
            </div>
            <div class="stat-card" style="border-left-color: #67c23a">
              <div class="label">今日成功</div>
              <div class="value">{{ status.today_success ?? 0 }}<small>次</small></div>
            </div>
            <div class="stat-card" style="border-left-color: #f56c6c">
              <div class="label">今日失败</div>
              <div class="value">{{ status.today_failed ?? 0 }}<small>次</small></div>
            </div>
            <div class="stat-card" style="border-left-color: #e6a23c">
              <div class="label">今日识别成功率</div>
              <div class="value">{{ percent(status.recognition_success_rate_today) }}</div>
            </div>
          </div>
        </template>
        <el-empty v-else description="暂无状态数据" :image-size="80" />
      </div>
      <template #footer>
        <el-button @click="statusVisible = false">关闭</el-button>
        <el-button type="primary" @click="loadStatus">刷新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const buildings = ref([])
const query = reactive({ keyword: '', building_id: '', device_status: '' })

const formVisible = ref(false)
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)
const form = reactive({
  camera_code: '',
  name: '',
  location: '',
  direction: 'IN',
  building_id: null,
  stream_url: '',
  device_status: 'online'
})
const rules = {
  camera_code: [{ required: true, message: '请输入摄像头编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入摄像头名称', trigger: 'blur' }],
  direction: [{ required: true, message: '请选择方向', trigger: 'change' }]
}

const statusVisible = ref(false)
const statusLoading = ref(false)
const status = ref({})
const statusCameraId = ref(null)

const statusMap = {
  online: { label: '在线', type: 'success' },
  offline: { label: '离线', type: 'danger' },
  error: { label: '异常', type: 'danger' },
  maintenance: { label: '维护', type: 'info' }
}

function statusLabel(v) {
  return statusMap[v]?.label || v || '-'
}
function statusTagType(v) {
  return statusMap[v]?.type || 'info'
}
function percent(v) {
  if (v === null || v === undefined || v === '') return '-'
  return `${(Number(v) * 100).toFixed(1)}%`
}
function healthPercent(v) {
  const n = Number(v)
  if (Number.isNaN(n)) return 0
  return Math.max(0, Math.min(100, Math.round(n)))
}
function healthColor(v) {
  const n = Number(v) || 0
  if (n >= 80) return '#67c23a'
  if (n >= 60) return '#e6a23c'
  return '#f56c6c'
}
function formatTime(v) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

async function loadBuildings() {
  try {
    const res = await api.get('/buildings')
    buildings.value = Array.isArray(res) ? res : (res.items || [])
  } catch (e) {
    buildings.value = []
  }
}

async function loadList() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.keyword) params.keyword = query.keyword
    if (query.building_id) params.building_id = query.building_id
    if (query.device_status) params.device_status = query.device_status
    const res = await api.get('/cameras', { params })
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
  Object.assign(query, { keyword: '', building_id: '', device_status: '' })
  onSearch()
}

function resetForm() {
  Object.assign(form, {
    camera_code: '',
    name: '',
    location: '',
    direction: 'IN',
    building_id: null,
    stream_url: '',
    device_status: 'online'
  })
}
function openCreate() {
  editingId.value = null
  resetForm()
  formVisible.value = true
}
function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    camera_code: row.camera_code || '',
    name: row.name || '',
    location: row.location || '',
    direction: row.direction || 'IN',
    building_id: row.building_id ?? null,
    stream_url: row.stream_url || '',
    device_status: row.device_status || 'online'
  })
  formVisible.value = true
}

async function submitForm() {
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return
  submitting.value = true
  try {
    const payload = { ...form }
    if (editingId.value) {
      await api.put(`/cameras/${editingId.value}`, payload)
      ElMessage.success('摄像头更新成功')
    } else {
      await api.post('/cameras', payload)
      ElMessage.success('摄像头创建成功')
    }
    formVisible.value = false
    loadList()
  } catch (e) {
    /* 错误提示由拦截器处理 */
  } finally {
    submitting.value = false
  }
}

function onDelete(row) {
  ElMessageBox.confirm(`确定删除摄像头「${row.name}」吗？删除后不可恢复。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        await api.delete(`/cameras/${row.id}`)
        ElMessage.success('删除成功')
        if (list.value.length === 1 && page.value > 1) page.value -= 1
        loadList()
      } catch (e) {
        /* 忽略 */
      }
    })
    .catch(() => {})
}

async function loadStatus() {
  if (!statusCameraId.value) return
  statusLoading.value = true
  try {
    status.value = await api.get(`/cameras/${statusCameraId.value}/status`)
  } catch (e) {
    status.value = {}
  } finally {
    statusLoading.value = false
  }
}
function openStatus(row) {
  statusCameraId.value = row.id
  status.value = {}
  statusVisible.value = true
  loadStatus()
}

onMounted(() => {
  loadBuildings()
  loadList()
})
</script>

<style scoped>
.toolbar :deep(.el-input__wrapper) {
  width: 100%;
}
</style>
