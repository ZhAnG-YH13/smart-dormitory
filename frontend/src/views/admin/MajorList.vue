<template>
  <div>
    <div class="page-header">
      <h2>专业管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>新增专业</el-button>
    </div>
    <div class="search-bar">
      <el-select v-model="query.college_id" placeholder="按学院筛选" clearable style="width:220px;">
        <el-option v-for="c in colleges" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button style="margin-left:8px;" @click="load">筛选</el-button>
    </div>
    <div class="table-card">
      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="ID" prop="id" width="80" />
        <el-table-column label="专业名称" prop="name" min-width="180" />
        <el-table-column label="学院" prop="college_name" min-width="180" />
        <el-table-column label="代码" prop="code" width="140" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="show" :title="editing ? '编辑专业' : '新增专业'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="学院" prop="college_id">
          <el-select v-model="form.college_id" placeholder="请选择学院" style="width:100%;">
            <el-option v-for="c in colleges" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="代码"><el-input v-model="form.code" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="show = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getColleges, getMajors, createMajor, updateMajor, deleteMajor } from '@/api/organization'

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const colleges = ref([])
const show = ref(false)
const editing = ref(null)
const formRef = ref(null)
const query = reactive({ college_id: null })
const form = reactive({ id: null, name: '', college_id: null, code: '' })
const rules = {
  name: [{ required: true, message: '请输入专业名称', trigger: 'blur' }],
  college_id: [{ required: true, message: '请选择学院', trigger: 'change' }]
}

async function load() {
  loading.value = true
  try {
    const params = {}
    if (query.college_id) params.college_id = query.college_id
    const res = await getMajors(params)
    const data = res.data || res
    list.value = Array.isArray(data) ? data : (data.items || data.list || [])
  } catch (e) { /* ignore */ }
  loading.value = false
}

async function loadColleges() {
  try {
    const res = await getColleges()
    const data = res.data || res
    colleges.value = Array.isArray(data) ? data : (data.items || data.list || [])
  } catch (e) { /* ignore */ }
}

function openCreate() { editing.value = null; Object.assign(form, { id: null, name: '', college_id: null, code: '' }); show.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); show.value = true }

async function submit() {
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return
  submitting.value = true
  try {
    if (editing.value) await updateMajor(editing.value, form)
    else await createMajor(form)
    ElMessage.success('操作成功'); show.value = false; load()
  } catch (e) { /* ignore */ }
  submitting.value = false
}

function onDelete(row) {
  ElMessageBox.confirm(`确定删除专业 ${row.name} 吗？`, '提示', { type: 'warning' }).then(async () => {
    try { await deleteMajor(row.id); ElMessage.success('删除成功'); load() } catch (e) { /* ignore */ }
  }).catch(() => {})
}

onMounted(() => { loadColleges(); load() })
</script>
