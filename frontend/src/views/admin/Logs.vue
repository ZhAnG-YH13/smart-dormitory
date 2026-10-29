<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
    </div>

    <div class="page-card">
      <div class="toolbar">
        <el-input
          v-model="query.action"
          placeholder="操作类型，如 LOGIN"
          clearable
          style="width: 200px"
          @keyup.enter="onSearch"
        />
        <el-input
          v-model="query.keyword"
          placeholder="操作人 / 对象 / 详情"
          clearable
          style="width: 240px"
          @keyup.enter="onSearch"
        />
        <el-button type="primary" @click="onSearch">搜索</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="时间" min-width="170">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作人" prop="username" min-width="120" />
        <el-table-column label="操作类型" min-width="150">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small">{{ row.action || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="对象" prop="target" min-width="160" show-overflow-tooltip />
        <el-table-column label="详情" prop="detail" min-width="240" show-overflow-tooltip />
        <el-table-column label="IP 地址" prop="ip_address" min-width="140" />
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="load"
          @current-change="load"
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
const pageSize = ref(50)

const query = reactive({ action: '', keyword: '' })

function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

function actionTagType(action) {
  const a = String(action || '').toUpperCase()
  if (a.includes('FAILED') || a.includes('DELETE')) return 'danger'
  if (a.includes('RESET') || a.includes('UPDATE')) return 'warning'
  if (a.includes('LOGIN') || a.includes('CREATE')) return 'success'
  return 'info'
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.action) params.action = query.action
    if (query.keyword) params.keyword = query.keyword
    const res = await api.get('/logs', { params })
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.value = false
}

function onSearch() {
  page.value = 1
  load()
}

function onReset() {
  query.action = ''
  query.keyword = ''
  onSearch()
}

onMounted(load)
</script>
