<template>
  <div>
    <div class="presence-cards">
      <div
        class="presence-card in"
        :class="{ active: query.is_present === 'true' }"
        @click="toggleFilter('true')"
      >
        <div class="card-label">当前在寝</div>
        <div class="card-value">{{ inCount }} <small>人</small></div>
        <div class="card-hint">点击查看在寝名单</div>
      </div>
      <div
        class="presence-card out"
        :class="{ active: query.is_present === 'false' }"
        @click="toggleFilter('false')"
      >
        <div class="card-label">当前不在寝</div>
        <div class="card-value">{{ outCount }} <small>人</small></div>
        <div class="card-hint">点击查看不在寝名单</div>
      </div>
    </div>

    <div class="page-card mt-16">
      <div class="page-header">
        <h2 class="page-title">在寝情况</h2>
        <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
      </div>

      <el-alert
        class="tip"
        type="info"
        :closable="false"
        show-icon
        title="不在寝状态为系统根据门禁记录推断，不代表学生实际位置"
      />

      <div class="toolbar mt-16">
        <el-select v-model="query.is_present" placeholder="全部状态" clearable style="width: 160px" @change="onSearch">
          <el-option label="在寝" value="true" />
          <el-option label="不在寝" value="false" />
        </el-select>
        <el-button @click="clearFilter">查看全部</el-button>
      </div>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column label="学号" prop="student_no" width="140" />
        <el-table-column label="姓名" prop="student_name" width="100" />
        <el-table-column label="班级" prop="class_name" min-width="140" show-overflow-tooltip />
        <el-table-column label="宿舍房间" prop="room_number" width="110" />
        <el-table-column label="当前状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_present ? 'success' : 'warning'" size="small">
              {{ row.is_present ? '在寝' : '不在寝' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最近方向" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.last_direction" :type="row.last_direction === 'IN' ? 'success' : 'info'" size="small">
              {{ row.last_direction === 'IN' ? '进入' : '离开' }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="最近门禁时间" min-width="170">
          <template #default="{ row }">{{ formatTime(row.last_access_time) }}</template>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const inCount = ref(0)
const outCount = ref(0)

const query = reactive({ is_present: '' })

function formatTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.is_present) params.is_present = query.is_present
    const res = await api.get('/presence', { params })
    list.value = res?.items || []
    total.value = res?.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function loadCounts() {
  try {
    const [inRes, outRes] = await Promise.all([
      api.get('/presence', { params: { is_present: true, page: 1, limit: 1 } }),
      api.get('/presence', { params: { is_present: false, page: 1, limit: 1 } })
    ])
    inCount.value = inRes?.total || 0
    outCount.value = outRes?.total || 0
  } catch (e) {
    inCount.value = 0
    outCount.value = 0
  }
}

function onSearch() {
  page.value = 1
  loadData()
}

function toggleFilter(value) {
  query.is_present = query.is_present === value ? '' : value
  onSearch()
}

function clearFilter() {
  query.is_present = ''
  onSearch()
}

onMounted(() => {
  loadCounts()
  loadData()
})
</script>

<style scoped>
.presence-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.presence-card {
  cursor: pointer;
  border-radius: 10px;
  padding: 22px 24px;
  color: #fff;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 2px solid transparent;
}

.presence-card.in {
  background: linear-gradient(135deg, #3a8ee6, #6fb3f2);
}

.presence-card.out {
  background: linear-gradient(135deg, #e6a23c, #f0bd6a);
}

.presence-card:hover {
  transform: translateY(-2px);
}

.presence-card.active {
  border-color: #1f2d3d;
  box-shadow: 0 4px 14px rgba(31, 45, 61, 0.2);
}

.card-label {
  font-size: 14px;
  opacity: 0.9;
}

.card-value {
  font-size: 34px;
  font-weight: 700;
  margin: 8px 0 6px;
}

.card-value small {
  font-size: 14px;
  font-weight: 400;
}

.card-hint {
  font-size: 12px;
  opacity: 0.8;
}

.tip {
  margin-bottom: 4px;
}
</style>
