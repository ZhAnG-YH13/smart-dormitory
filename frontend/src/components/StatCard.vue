<template>
  <div class="stat-card" :style="{ background: bgColor }">
    <div class="stat-info">
      <h3 :style="{ color: valueColor }">
        <span v-if="prefix">{{ prefix }}</span>{{ value }}<span v-if="suffix" style="font-size:14px;font-weight:normal;">{{ suffix }}</span>
      </h3>
      <p>{{ label }}</p>
      <div v-if="extra" style="margin-top:6px;font-size:12px;color:#909399;">{{ extra }}</div>
    </div>
    <div class="stat-icon" :style="{ background: iconBg }">
      <el-icon :size="32"><component :is="icon" /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: String, default: 'DataLine' },
  color: { type: String, default: '#1e3c72' },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  extra: { type: String, default: '' }
})

const valueColor = computed(() => props.color)
const iconBg = computed(() => props.color)
const bgColor = computed(() => '#fff')
</script>
