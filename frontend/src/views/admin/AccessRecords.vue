<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">门禁记录</h2>
      <div>
        <el-button @click="loadAll"><el-icon><Refresh /></el-icon>刷新</el-button>
        <el-button type="success" :disabled="!list.length" @click="exportCsv">
          <el-icon><Download /></el-icon>导出 CSV
        </el-button>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">今日通行总数</div>
        <div class="value">{{ stats.today_total ?? 0 }}<small>次</small></div>
      </div>
      <div class="stat-card" style="border-left-color: #67c23a">
        <div class="label">今日进入</div>
        <div class="value">{{ stats.today_in ?? 0 }}<small>次</small></div>
      </div>
      <div class="stat-card" style="border-left-color: #e6a23c">
        <div class="label">今日离开</div>
        <div class="value">{{ stats.today_out ?? 0 }}<small>次</small></div>
      </div>
    </div>

    <div class="page-card mt-16">
      <div class="toolbar">
        <el-select
          v-model="query.student_id"
          filterable
          remote
          clearable
          reserve-keyword
          :remote-method="searchStudents"
          :loading="studentLoading"
          placeholder="搜索学生（学号 / 姓名）"
          style="width: 220px"
        >
          <el-option
            v-for="s in studentOptions"
            :key="s.id"
            :label="`${s.student_no} ${s.name}`"
            :value="s.id"
          />
        </el-select>
        <el-select v-model="query.camera_id" placeholder="全部摄像头" clearable style="width: 180px">
          <el-option
            v-for="c in cameras"
            :key="c.id"
            :label="`${c.camera_code} ${c.name}`"
            :value="c.id"
          />
        </el-select>
        <el-select v-model="query.direction" placeholder="全部方向" clearable style="width: 140px">
          <el-option label="进入 (IN)" value="IN" />
          <el-option label="离开 (OUT)" value="OUT" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          unlink-panels
          style="width: 260px"
        />
        <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>搜索</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="130" />
        <el-table-column label="姓名" prop="student_name" width="100" />
        <el-table-column label="宿舍楼" prop="building_name" min-width="110" />
        <el-table-column label="摄像头" prop="camera_code" width="120" />
        <el-table-column label="方向" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'IN' ? 'success' : 'warning'" size="small">
              {{ row.direction === 'IN' ? '进入' : '离开' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="相似度" width="100" align="center">
          <template #default="{ row }">{{ similarityText(row.similarity) }}</template>
        </el-table-column>
        <el-table-column label="验证结果" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.verify_result === 'success' ? 'success' : 'danger'" size="small">
              {{ row.verify_result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="识别方式" width="110" align="center">
          <template #default="{ row }">{{ modeLabel(row.recognition_mode) }}</template>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const query = reactive({ student_id: null, camera_id: '', direction: '' })
const dateRange = ref([])
const stats = ref({})
const cameras = ref([])
const studentOptions = ref([])
const studentLoading = ref(false)

const modeMap = {
  simulate: '模拟通行',
  realtime: '实时识别',
  manual: '人工处理',
  batch: '批量识别'
}

function modeLabel(v) {
  return modeMap[v] || v || '-'
}
function similarityText(v) {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  return Number.isNaN(n) ? '-' : n.toFixed(3)
}
function formatTime(v) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

async function loadStats() {
  try {
    stats.value = await api.get('/stats/dashboard')
  } catch (e) {
    stats.value = {}
  }
}

async function loadCameras() {
  try {
    const res = await api.get('/cameras', { params: { limit: 200 } })
    cameras.value = res.items || []
  } catch (e) {
    cameras.value = []
  }
}

async function searchStudents(keyword) {
  if (!keyword) {
    studentOptions.value = []
    return
  }
  studentLoading.value = true
  try {
    const res = await api.get('/students', { params: { keyword, limit: 20 } })
    studentOptions.value = res.items || []
  } catch (e) {
    studentOptions.value = []
  } finally {
    studentLoading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.student_id) params.student_id = query.student_id
    if (query.camera_id) params.camera_id = query.camera_id
    if (query.direction) params.direction = query.direction
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await api.get('/access/records', { params })
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
  Object.assign(query, { student_id: null, camera_id: '', direction: '' })
  dateRange.value = []
  onSearch()
}

function exportCsv() {
  if (!list.value.length) {
    ElMessage.warning('当前没有可导出的记录')
    return
  }
  const headers = ['时间', '学号', '姓名', '宿舍楼', '摄像头', '方向', '相似度', '验证结果', '识别方式']
  const rows = list.value.map(r => [
    formatTime(r.occurred_at),
    r.student_no,
    r.student_name,
    r.building_name,
    r.camera_code,
    r.direction === 'IN' ? '进入' : '离开',
    similarityText(r.similarity),
    r.verify_result === 'success' ? '成功' : '失败',
    modeLabel(r.recognition_mode)
  ])
  const escapeCell = v => `"${String(v ?? '').replace(/"/g, '""')}"`
  const csv = [headers, ...rows].map(row => row.map(escapeCell).join(',')).join('\r\n')
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `门禁记录_${new Date().toLocaleString('zh-CN', { hour12: false }).replace(/[/: ]/g, '')}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('CSV 已导出')
}

function loadAll() {
  loadStats()
  loadCameras()
  loadList()
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.stat-grid {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}
</style>
