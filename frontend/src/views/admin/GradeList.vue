<template>
  <div>
    <div class="page-header">
      <h2>年级管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>新增年级</el-button>
    </div>
    <div class="table-card">
      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="ID" prop="id" width="80" />
        <el-table-column label="年级名称" prop="name" min-width="200" />
        <el-table-column label="年份" prop="year" width="120" />
        <el-table-column label="描述" prop="description" min-width="200" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="show" :title="editing ? '编辑年级' : '新增年级'" width="420px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" placeholder="如：2023级" /></el-form-item>
        <el-form-item label="年份" prop="year"><el-input-number v-model="form.year" :min="2000" :max="2100" style="width:100%;" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
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
import { getGrades, createGrade, updateGrade, deleteGrade } from '@/api/organization'

const loading = ref(false); const submitting = ref(false); const list = ref([])
const show = ref(false); const editing = ref(null); const formRef = ref(null)
const form = reactive({ id: null, name: '', year: new Date().getFullYear(), description: '' })
const rules = { name: [{ required: true, message: '请输入年级名称', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try {
    const res = await getGrades()
    const data = res.data || res
    list.value = Array.isArray(data) ? data : (data.items || data.list || [])
  } catch (e) { /* ignore */ }
  loading.value = false
}

function openCreate() { editing.value = null; Object.assign(form, { id: null, name: '', year: new Date().getFullYear(), description: '' }); show.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); show.value = true }

async function submit() {
  const ok = await formRef.value.validate().catch(() => false); if (!ok) return
  submitting.value = true
  try {
    if (editing.value) await updateGrade(editing.value, form)
    else await createGrade(form)
    ElMessage.success('操作成功'); show.value = false; load()
  } catch (e) { /* ignore */ }
  submitting.value = false
}

function onDelete(row) {
  ElMessageBox.confirm(`确定删除年级 ${row.name} 吗？`, '提示', { type: 'warning' }).then(async () => {
    try { await deleteGrade(row.id); ElMessage.success('删除成功'); load() } catch (e) { /* ignore */ }
  }).catch(() => {})
}

onMounted(load)
</script>
