<template>
  <div class="private-securities-fund">
    <!-- 标签页头部 -->
    <div class="tabs-header">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- 产品库 -->
    <ProductLibrary v-if="activeTab === 'products'" />

    <!-- 销售录入 -->
    <SalesEntry v-if="activeTab === 'entry'" />

    <!-- 年度看板 -->
    <AnnualDashboard v-if="activeTab === 'stats'" />

    <!-- 保有统计 -->
    <HoldingStats v-if="activeTab === 'holding'" />

    <!-- 考核管理 -->
    <AssessmentTarget v-if="activeTab === 'assessment'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ProductLibrary from '../components/privateFund/ProductLibrary.vue'
import SalesEntry from '../components/privateFund/SalesEntry.vue'
import AnnualDashboard from '../components/privateFund/AnnualDashboard.vue'
import HoldingStats from '../components/privateFund/HoldingStats.vue'
import AssessmentTarget from '../components/privateFund/AssessmentTarget.vue'

const tabs = [
  { key: 'stats', label: '年度看板' },
  { key: 'holding', label: '保有统计' },
  { key: 'assessment', label: '考核管理' },
  { key: 'entry', label: '销售录入' },
  { key: 'products', label: '产品库' }
]

const activeTab = ref('stats')
</script>

<style scoped>
.private-securities-fund {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: #FAFAFB;
  padding: 0 8px;
}

.tab-item {
  padding: 16px 24px;
  font-size: 15px;
  font-weight: 500;
  color: #6E6E73;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  position: relative;
}

.tab-item:hover {
  color: #1D1D1F;
}

.tab-item.active {
  color: #7C3AED;
  border-bottom-color: #7C3AED;
  background: rgba(124, 58, 237, 0.05);
}
</style>
