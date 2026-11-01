<template>
  <div class="side-menu">
    <div class="brand">
      <el-icon :size="22"><School /></el-icon>
      <span v-show="!collapsed" class="brand-text">智慧宿舍门禁</span>
    </div>
    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      router
      background-color="#1f2d3d"
      text-color="#c0c4cc"
      active-text-color="#409eff"
      class="menu"
      @select="$emit('select')"
    >
      <template v-for="item in menus" :key="item.path">
        <el-sub-menu v-if="item.children" :index="item.path">
          <template #title>
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </template>
          <el-menu-item v-for="c in item.children" :key="c.path" :index="c.path">
            {{ c.title }}
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item v-else :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </template>
    </el-menu>
  </div>
</template>

<script setup>
defineProps({
  menus: { type: Array, default: () => [] },
  activeMenu: { type: String, default: '' },
  collapsed: { type: Boolean, default: false }
})
defineEmits(['select'])
</script>

<style scoped>
.side-menu {
  height: 100%;
  background: #1f2d3d;
  overflow-x: hidden;
}

.brand {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px;
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-text {
  font-size: 15px;
}

.menu {
  border-right: none;
}
</style>
