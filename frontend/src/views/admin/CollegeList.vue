<template>
  <div>
    <div class="page-header">
      <h2>学院管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>新增学院</el-button>
    </div>
    <div class="table-card">
      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="ID" prop="id" width="80" />
        <el-table-column label="学院名称" prop="name" min-width="200" />
        <el-table-column label="学院代码" prop="code" width="160" />
        <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="show" :title="editing ? '编辑学院' : '新增学院'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="代码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
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
import { getColleges, createCollege, updateCollege, deleteCollege } from '@/api/organization'

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const show = ref(false)
const editing = ref(null)
const formRef = ref(null)
const form = reactive({ id: null, name: '', code: '', description: '' })
const rules = { name: [{ required: true, message: '请输入学院名称', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try {
    const res = await getColleges()
    const data = res.data || res
    list.value = Array.isArray(data) ? data : (data.items || data.list || [])
  } catch (e) { /* ignore */ }
  loading.value = false
}

function openCreate() { editing.value = null; Object.assign(form, { id: null, name: '', code: '', description: '' }); show.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); show.value = true }

async function submit() {
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return
  submitting.value = true
  try {
    if (editing.value) await updateCollege(editing.value, form)
    else await createCollege(form)
    ElMessage.success('操作成功'); show.value = false; load()
  } catch (e) { /* ignore */ }
  submitting.value = false
}

function onDelete(row) {
  ElMessageBox.confirm(`确定删除学院 ${row.name} 吗？`, '提示', { type: 'warning' }).then(async () => {
    try { await deleteCollege(row.id); ElMessage.success('删除成功'); load() } catch (e) { /* ignore */ }
  }).catch(() => {})
}

onMounted(load)
</script>
