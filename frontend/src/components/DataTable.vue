<template>
  <div class="table-card">
    <div v-if="title" class="chart-title">{{ title }}</div>
    <el-table
      :data="tableData"
      v-loading="loading"
      stripe
      border
      style="width: 100%"
      :height="height"
      :max-height="maxHeight"
      :empty-text="emptyText"
      @row-click="onRowClick"
    >
      <el-table-column
        v-for="col in columns"
        :key="col.prop || col.type"
        :type="col.type"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :fixed="col.fixed"
        :align="col.align || 'center'"
        :formatter="col.formatter"
        :sortable="col.sortable"
        :show-overflow-tooltip="col.showOverflow !== false"
      >
        <template #default="scope" v-if="col.slot">
          <slot :name="col.slot" :row="scope.row" :scope="scope" />
        </template>
      </el-table-column>
      <template #empty>
        <div>{{ emptyText }}</div>
      </template>
    </el-table>
    <div v-if="showPagination" style="margin-top: 12px; display: flex; justify-content: flex-end;">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="onSizeChange"
        @current-change="onCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  columns: { type: Array, required: true },
  fetchData: { type: Function, default: null },
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  height: { type: [String, Number], default: undefined },
  maxHeight: { type: [String, Number], default: undefined },
  emptyText: { type: String, default: '暂无数据' },
  showPagination: { type: Boolean, default: true },
  pageSizes: { type: Array, default: () => [10, 20, 50, 100] },
  defaultSort: { type: Object, default: null }
})

const emit = defineEmits(['page-change', 'row-click', 'loaded'])

const tableData = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function loadData() {
  if (props.fetchData) {
    try {
      const params = { page: page.value, limit: pageSize.value }
      const res = await props.fetchData(params)
      const result = res.data || res
      if (Array.isArray(result)) {
        tableData.value = result
        total.value = result.length
      } else {
        tableData.value = result.items || result.list || result.rows || []
        total.value = result.total || 0
      }
      emit('loaded', result)
    } catch (e) {
      tableData.value = []
      total.value = 0
    }
  } else if (Array.isArray(props.data)) {
    tableData.value = props.data
    total.value = props.data.length
  }
}

function onSizeChange(size) {
  pageSize.value = size
  page.value = 1
  loadData()
  emit('page-change', { page: page.value, pageSize: size })
}

function onCurrentChange(cur) {
  page.value = cur
  loadData()
  emit('page-change', { page: cur, pageSize: pageSize.value })
}

function onRowClick(row) {
  emit('row-click', row)
}

watch(() => props.data, (val) => {
  if (!props.fetchData) {
    tableData.value = val || []
    total.value = (val || []).length
  }
}, { deep: true })

onMounted(() => {
  loadData()
})

defineExpose({ load: loadData, tableData, page, pageSize, total })
</script>
