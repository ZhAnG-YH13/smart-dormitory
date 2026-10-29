<template>
  <div class="page-card">
    <div class="page-header">
      <h2 class="page-title">门禁记录</h2>
      <div>
        <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
        <el-button type="success" :loading="exporting" @click="exportCsv">
          <el-icon><Download /></el-icon>导出 CSV
        </el-button>
      </div>
    </div>

    <div class="toolbar">
      <el-select v-model="query.direction" placeholder="全部方向" clearable style="width: 140px">
        <el-option label="进入 (IN)" value="IN" />
        <el-option label="离开 (OUT)" value="OUT" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        style="width: 260px"
      />
      <el-button type="primary" @click="onSearch">
        <el-icon><Search /></el-icon>查询
      </el-button>
      <el-button @click="onReset">重置</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe border>
      <el-table-column label="时间" width="170">
        <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
      </el-table-column>
      <el-table-column label="学号" prop="student_no" width="140" />
      <el-table-column label="姓名" prop="student_name" width="100" />
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

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const exporting = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const dateRange = ref(null)

const query = reactive({ direction: '' })

function formatTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

function similarityText(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return `${(n * 100).toFixed(1)}%`
}

function buildParams() {
  const params = {}
  if (query.direction) params.direction = query.direction
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  return params
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.get('/access/records', {
      params: { ...buildParams(), page: page.value, limit: pageSize.value }
    })
    list.value = res?.items || []
    total.value = res?.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  loadData()
}

function onReset() {
  query.direction = ''
  dateRange.value = null
  onSearch()
}

function csvCell(value) {
  const s = value === null || value === undefined ? '' : String(value)
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

async function exportCsv() {
  exporting.value = true
  try {
    const base = buildParams()
    const limit = 200
    let currentPage = 1
    let all = []
    while (currentPage <= 50) {
      const res = await api.get('/access/records', {
        params: { ...base, page: currentPage, limit }
      })
      const items = res?.items || []
      all = all.concat(items)
      if (items.length === 0 || all.length >= (res?.total || 0)) break
      currentPage++
    }

    if (!all.length) {
      ElMessage.warning('暂无可导出的数据')
      return
    }

    const header = ['时间', '学号', '姓名', '宿舍楼', '摄像头', '方向', '相似度', '验证结果', '识别方式']
    const rows = all.map(r => [
      formatTime(r.occurred_at),
      r.student_no || '',
      r.student_name || '',
      r.building_name || '',
      r.camera_code || '',
      r.direction === 'IN' ? '进入' : '离开',
      similarityText(r.similarity),
      r.verify_result === 'success' ? '通过' : '未通过',
      r.recognition_mode || ''
    ])
    const csv = '\ufeff' + [header, ...rows].map(cols => cols.map(csvCell).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const stamp = new Date().toISOString().slice(0, 10)
    link.href = url
    link.download = `门禁记录_${stamp}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success(`已导出 ${all.length} 条记录`)
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    exporting.value = false
  }
}

onMounted(loadData)
</script>
