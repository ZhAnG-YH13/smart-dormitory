<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">宿舍管理</h2>
      <el-button :loading="loadingBuilding || loadingRoom" @click="reload">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <div class="page-card">
      <el-tabs v-model="tab">
        <el-tab-pane label="宿舍楼" name="building">
          <div class="toolbar">
            <el-button type="primary" @click="openBuildingDialog()">
              <el-icon><Plus /></el-icon>新增宿舍楼
            </el-button>
            <span class="text-muted">共 {{ buildings.length }} 栋宿舍楼</span>
          </div>
          <el-table v-loading="loadingBuilding" :data="buildings" border stripe>
            <el-table-column prop="name" label="宿舍楼名称" min-width="160" />
            <el-table-column prop="code" label="楼栋编码" width="140">
              <template #default="{ row }">{{ row.code || '-' }}</template>
            </el-table-column>
            <el-table-column prop="floors" label="楼层数" width="110" align="center" />
            <el-table-column prop="room_count" label="房间数" width="110" align="center" />
            <el-table-column prop="student_count" label="入住学生数" width="130" align="center" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openBuildingDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="onDeleteBuilding(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="宿舍房间" name="room">
          <div class="toolbar">
            <el-select
              v-model="roomBuildingId"
              placeholder="全部宿舍楼"
              clearable
              filterable
              style="width: 200px"
              @change="onRoomFilter"
            >
              <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="b.id" />
            </el-select>
            <el-button type="primary" @click="openRoomDialog()">
              <el-icon><Plus /></el-icon>新增房间
            </el-button>
            <span class="text-muted">共 {{ roomTotal }} 个房间</span>
          </div>
          <el-table v-loading="loadingRoom" :data="rooms" border stripe>
            <el-table-column prop="building_name" label="所属宿舍楼" min-width="150" />
            <el-table-column prop="room_number" label="房间号" width="130" />
            <el-table-column prop="capacity" label="床位数" width="100" align="center" />
            <el-table-column label="已住人数" width="110" align="center">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  :type="(row.current_count || 0) >= (row.capacity || 0) ? 'danger' : 'success'"
                >
                  {{ row.current_count || 0 }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="入住率" min-width="160">
              <template #default="{ row }">
                <el-progress
                  :percentage="roomUsage(row)"
                  :stroke-width="9"
                  :color="roomUsage(row) >= 100 ? '#f56c6c' : '#409eff'"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openRoomDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="onDeleteRoom(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :total="roomTotal"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              background
              @size-change="loadRooms"
              @current-change="loadRooms"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="buildingDialogVisible" :title="buildingEditId ? '编辑宿舍楼' : '新增宿舍楼'" width="460px">
      <el-form ref="buildingFormRef" :model="buildingForm" :rules="buildingRules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="buildingForm.name" placeholder="如 1号楼" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="buildingForm.code" placeholder="如 B01，选填" />
        </el-form-item>
        <el-form-item label="楼层数">
          <el-input-number v-model="buildingForm.floors" :min="1" :max="50" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="buildingDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBuilding">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="roomDialogVisible" :title="roomEditId ? '编辑房间' : '新增房间'" width="460px">
      <el-form ref="roomFormRef" :model="roomForm" :rules="roomRules" label-width="90px">
        <el-form-item label="宿舍楼" prop="building_id">
          <el-select v-model="roomForm.building_id" placeholder="请选择宿舍楼" filterable style="width: 100%">
            <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="房间号" prop="room_number">
          <el-input v-model="roomForm.room_number" placeholder="如 301" />
        </el-form-item>
        <el-form-item label="床位数">
          <el-input-number v-model="roomForm.capacity" :min="1" :max="20" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roomDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitRoom">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const tab = ref('building')
const buildings = ref([])
const rooms = ref([])
const roomTotal = ref(0)
const page = ref(1)
const pageSize = ref(20)
const roomBuildingId = ref(null)

const loadingBuilding = ref(false)
const loadingRoom = ref(false)
const submitting = ref(false)

const buildingDialogVisible = ref(false)
const buildingEditId = ref(null)
const buildingFormRef = ref(null)
const buildingForm = reactive({ name: '', code: '', floors: 6 })
const buildingRules = {
  name: [{ required: true, message: '请输入宿舍楼名称', trigger: 'blur' }]
}

const roomDialogVisible = ref(false)
const roomEditId = ref(null)
const roomFormRef = ref(null)
const roomForm = reactive({ building_id: null, room_number: '', capacity: 4 })
const roomRules = {
  building_id: [{ required: true, message: '请选择宿舍楼', trigger: 'change' }],
  room_number: [{ required: true, message: '请输入房间号', trigger: 'blur' }]
}

function pickItems(res) {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  if (res?.data) return pickItems(res.data)
  return []
}

function roomUsage(row) {
  const capacity = Number(row.capacity) || 0
  if (!capacity) return 0
  return Math.min(Math.round(((Number(row.current_count) || 0) / capacity) * 100), 100)
}

async function loadBuildings() {
  loadingBuilding.value = true
  try {
    buildings.value = pickItems(await api.get('/buildings'))
  } catch (e) {
    buildings.value = []
  } finally {
    loadingBuilding.value = false
  }
}

async function loadRooms() {
  loadingRoom.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (roomBuildingId.value) params.building_id = roomBuildingId.value
    const res = await api.get('/rooms', { params })
    rooms.value = res.items || []
    roomTotal.value = res.total || 0
  } catch (e) {
    rooms.value = []
    roomTotal.value = 0
  } finally {
    loadingRoom.value = false
  }
}

function reload() {
  loadBuildings()
  loadRooms()
}

function onRoomFilter() {
  page.value = 1
  loadRooms()
}

function openBuildingDialog(row = null) {
  buildingEditId.value = row?.id || null
  buildingForm.name = row?.name || ''
  buildingForm.code = row?.code || ''
  buildingForm.floors = row?.floors || 6
  buildingDialogVisible.value = true
}

function openRoomDialog(row = null) {
  if (!buildings.value.length) {
    ElMessage.warning('请先新增宿舍楼')
    return
  }
  roomEditId.value = row?.id || null
  roomForm.building_id = row?.building_id || roomBuildingId.value || buildings.value[0].id
  roomForm.room_number = row?.room_number || ''
  roomForm.capacity = row?.capacity || 4
  roomDialogVisible.value = true
}

async function submitBuilding() {
  const valid = await buildingFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = {
      name: buildingForm.name,
      code: buildingForm.code || null,
      floors: buildingForm.floors || 6
    }
    if (buildingEditId.value) {
      await api.put(`/buildings/${buildingEditId.value}`, payload)
      ElMessage.success('宿舍楼已更新')
    } else {
      await api.post('/buildings', payload)
      ElMessage.success('宿舍楼已创建')
    }
    buildingDialogVisible.value = false
    await loadBuildings()
    await loadRooms()
  } catch (e) {
    /* 错误提示已由拦截器处理 */
  } finally {
    submitting.value = false
  }
}

async function submitRoom() {
  const valid = await roomFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = {
      building_id: roomForm.building_id,
      room_number: roomForm.room_number,
      capacity: roomForm.capacity || 4
    }
    if (roomEditId.value) {
      await api.put(`/rooms/${roomEditId.value}`, payload)
      ElMessage.success('房间已更新')
    } else {
      await api.post('/rooms', payload)
      ElMessage.success('房间已创建')
    }
    roomDialogVisible.value = false
    await loadBuildings()
    await loadRooms()
  } catch (e) {
    /* 错误提示已由拦截器处理 */
  } finally {
    submitting.value = false
  }
}

function onDeleteBuilding(row) {
  ElMessageBox.confirm(`确定删除宿舍楼「${row.name}」吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        await api.delete(`/buildings/${row.id}`)
        ElMessage.success('删除成功')
        if (roomBuildingId.value === row.id) roomBuildingId.value = null
        await loadBuildings()
        await loadRooms()
      } catch (e) {
        /* ignore */
      }
    })
    .catch(() => {})
}

function onDeleteRoom(row) {
  ElMessageBox.confirm(
    `确定删除「${row.building_name || ''} ${row.room_number}」房间吗？`,
    '删除确认',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  )
    .then(async () => {
      try {
        await api.delete(`/rooms/${row.id}`)
        ElMessage.success('删除成功')
        await loadBuildings()
        await loadRooms()
      } catch (e) {
        /* ignore */
      }
    })
    .catch(() => {})
}

onMounted(() => {
  loadBuildings()
  loadRooms()
})
</script>
