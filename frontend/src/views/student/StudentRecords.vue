<template>
  <div>
    <div class="page-card record-state">
      <div class="state-left">
        <el-icon :size="34" :color="isPresent ? '#67c23a' : '#e6a23c'"><House /></el-icon>
        <div>
          <div class="state-title">当前在寝状态</div>
          <div class="text-muted">状态由门禁记录自动推断，仅供参考</div>
        </div>
      </div>
      <el-tag :type="stateTag.type" size="large">{{ stateTag.text }}</el-tag>
    </div>

    <div class="page-card mt-16">
      <div class="page-header">
        <h2 class="page-title">我的门禁记录</h2>
        <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
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
        <el-table-column label="识别方式" min-width="110">
          <template #default="{ row }">{{ row.recognition_mode || '-' }}</template>
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
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const dateRange = ref(null)

const query = reactive({ direction: '' })
const presence = ref(null)
const latestRecord = ref(null)

const isPresent = computed(() => {
  if (presence.value) return !!presence.value.is_present
  if (latestRecord.value) return latestRecord.value.direction === 'IN'
  return null
})

const stateTag = computed(() => {
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

function buildParams() {
  const params = {}
  if (query.direction) params.direction = query.direction
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  return params
}

async function loadState() {
  try {
    const [presenceRes, latestRes] = await Promise.all([
      api.get('/presence', { params: { page: 1, limit: 50 } }),
      api.get('/access/records', { params: { page: 1, limit: 1 } })
    ])
    presence.value = (presenceRes?.items || [])[0] || null
    latestRecord.value = (latestRes?.items || [])[0] || null
  } catch (e) {
    presence.value = null
    latestRecord.value = null
  }
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

onMounted(() => {
  loadState()
  loadData()
})
</script>

<style scoped>
.record-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.state-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.state-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 4px;
}
</style>
