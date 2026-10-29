<template>
  <div class="page-card">
    <div class="page-header">
      <h2 class="page-title">异常记录</h2>
      <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="待处理" name="pending" />
      <el-tab-pane label="处理中" name="processing" />
      <el-tab-pane label="已解决" name="resolved" />
      <el-tab-pane label="已关闭" name="closed" />
    </el-tabs>

    <div class="toolbar">
      <el-select v-model="query.event_type" placeholder="全部类型" clearable style="width: 160px">
        <el-option v-for="(v, k) in typeMap" :key="k" :label="v" :value="k" />
      </el-select>
      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 140px">
        <el-option v-for="(v, k) in statusMap" :key="k" :label="v" :value="k" />
      </el-select>
      <el-button type="primary" @click="onSearch">
        <el-icon><Search /></el-icon>查询
      </el-button>
      <el-button @click="onReset">重置</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe border>
      <el-table-column label="事件编号" prop="event_no" width="170" show-overflow-tooltip />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">{{ typeMap[row.event_type] || row.event_type || '-' }}</template>
      </el-table-column>
      <el-table-column label="原因" prop="event_reason" min-width="130" show-overflow-tooltip />
      <el-table-column label="摄像头" prop="camera_code" min-width="120" show-overflow-tooltip />
      <el-table-column label="学号" prop="student_no" width="120" />
      <el-table-column label="严重程度" width="100">
        <template #default="{ row }">
          <el-tag :type="severityTag(row.severity)" size="small">{{ severityMap[row.severity] || '未知' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ statusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发生时间" width="170">
        <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
      </el-table-column>
      <el-table-column label="处理记录" width="90" align="center">
        <template #default="{ row }">{{ row.handles_count || 0 }} 条</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <el-dialog v-model="detailVisible" title="异常详情" width="780px">
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="事件编号">{{ detail.event_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="事件类型">
            {{ typeMap[detail.event_type] || detail.event_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="事件原因">{{ detail.event_reason || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联学号">{{ detail.student_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="摄像头">{{ detail.camera_code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="severityTag(detail.severity)" size="small">
              {{ severityMap[detail.severity] || '未知' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detail.status)" size="small">
              {{ statusMap[detail.status] || detail.status || '-' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ formatTime(detail.occurred_at) }}</el-descriptions-item>
          <el-descriptions-item label="事件详情" :span="2">{{ detail.event_detail || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">处理历史</div>
        <el-table v-if="handles.length" :data="handles" size="small" border>
          <el-table-column label="处理人" prop="handler_name" width="110" />
          <el-table-column label="处理方式" prop="handle_type" width="120" />
          <el-table-column label="处理结果" prop="handle_result" min-width="130" show-overflow-tooltip />
          <el-table-column label="处理说明" prop="handle_note" min-width="160" show-overflow-tooltip />
          <el-table-column label="处理时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无处理记录" :image-size="80" />
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'

const typeMap = {
  device_error: '设备异常',
  image_quality: '图像质量异常',
  ai_recognition: 'AI识别异常',
  business: '业务异常'
}

const statusMap = {
  pending: '待处理',
  processing: '处理中',
  resolved: '已解决',
  closed: '已关闭',
  auto_recovered: '自动恢复'
}

const severityMap = {
  1: '低',
  2: '中',
  3: '高'
}

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const activeTab = ref('all')

const query = reactive({ event_type: '', status: '' })

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref({})
const handles = ref([])

function formatTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

function severityTag(sev) {
  if (sev === 3) return 'danger'
  if (sev === 2) return 'warning'
  return 'info'
}

function statusTag(status) {
  const map = {
    pending: 'danger',
    processing: 'warning',
    resolved: 'success',
    closed: 'info',
    auto_recovered: 'info'
  }
  return map[status] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.event_type) params.event_type = query.event_type
    if (query.status) params.status = query.status
    const res = await api.get('/abnormals', { params })
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

function onTabChange() {
  query.status = activeTab.value === 'all' ? '' : activeTab.value
  onSearch()
}

function onReset() {
  query.event_type = ''
  query.status = ''
  activeTab.value = 'all'
  onSearch()
}

async function openDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = row
  handles.value = []
  try {
    const res = await api.get(`/abnormals/${row.id}`)
    detail.value = res?.event || row
    handles.value = res?.handles || []
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    detailLoading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin: 18px 0 10px;
}
</style>
