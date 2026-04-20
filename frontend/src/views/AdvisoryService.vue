<template>
  <div class="advisory-service">
    <!-- Top-level tabs -->
    <div class="tabs-header top-tabs">
      <div
        v-for="tab in topTabs"
        :key="tab.key"
        class="tab-item top-tab"
        :class="{ active: activeTopTab === tab.key, [tab.theme]: true }"
        @click="activeTopTab = tab.key"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- 本年新增 -->
    <template v-if="activeTopTab === 'new'">
      <div class="sub-tabs-header">
        <div
          v-for="tab in newSubTabs"
          :key="tab.key"
          class="tab-item sub-tab"
          :class="{ active: activeNewSubTab === tab.key }"
          @click="activeNewSubTab = tab.key"
        >
          {{ tab.label }}
        </div>
      </div>
      <div class="tab-content">
        <AdvisoryDashboard v-if="activeNewSubTab === 'dashboard'" scope="new" />
        <AdvisoryGroupView v-if="activeNewSubTab === 'group'" scope="new" />
        <AdvisoryMemberView v-if="activeNewSubTab === 'member'" scope="new" />
        <AdvisoryTarget v-if="activeNewSubTab === 'target'" />
      </div>
    </template>

    <!-- 存量统计 -->
    <template v-if="activeTopTab === 'stock'">
      <div class="sub-tabs-header">
        <div
          v-for="tab in stockSubTabs"
          :key="tab.key"
          class="tab-item sub-tab"
          :class="{ active: activeStockSubTab === tab.key }"
          @click="activeStockSubTab = tab.key"
        >
          {{ tab.label }}
        </div>
      </div>
      <div class="tab-content">
        <AdvisoryDashboard v-if="activeStockSubTab === 'dashboard'" scope="stock" />
        <AdvisoryGroupView v-if="activeStockSubTab === 'group'" scope="stock" />
        <AdvisoryMemberView v-if="activeStockSubTab === 'member'" scope="stock" />
      </div>
    </template>

    <!-- 数据导入 -->
    <template v-if="activeTopTab === 'import'">
      <div class="tab-content">
        <AdvisoryImport />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AdvisoryDashboard from '../components/advisory/AdvisoryDashboard.vue'
import AdvisoryGroupView from '../components/advisory/AdvisoryGroupView.vue'
import AdvisoryMemberView from '../components/advisory/AdvisoryMemberView.vue'
import AdvisoryImport from '../components/advisory/AdvisoryImport.vue'
import AdvisoryTarget from '../components/advisory/AdvisoryTarget.vue'

const topTabs = [
  { key: 'new', label: '本年新增', theme: 'blue' },
  { key: 'stock', label: '存量统计', theme: 'green' },
  { key: 'import', label: '数据导入', theme: 'default' }
]

const newSubTabs = [
  { key: 'dashboard', label: '全公司视图' },
  { key: 'group', label: '营业部视图' },
  { key: 'member', label: '个人视图' },
  { key: 'target', label: '考核管理' }
]

const stockSubTabs = [
  { key: 'dashboard', label: '全公司视图' },
  { key: 'group', label: '营业部视图' },
  { key: 'member', label: '个人视图' }
]

const activeTopTab = ref('new')
const activeNewSubTab = ref('dashboard')
const activeStockSubTab = ref('dashboard')
</script>

<style scoped>
.advisory-service {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

/* Top-level tabs */
.top-tabs {
  display: flex;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: #FAFAFB;
  padding: 0 8px;
}

.top-tab {
  padding: 16px 28px;
  font-size: 15px;
  font-weight: 600;
  color: #6E6E73;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease;
  position: relative;
}

.top-tab:hover {
  color: #1D1D1F;
}

.top-tab.blue.active {
  color: #1EAEDB;
  border-bottom-color: #1EAEDB;
  background: rgba(30, 174, 219, 0.06);
}

.top-tab.green.active {
  color: #10B981;
  border-bottom-color: #10B981;
  background: rgba(16, 185, 129, 0.06);
}

.top-tab.default.active {
  color: #1D1D1F;
  border-bottom-color: #1D1D1F;
  background: rgba(0, 0, 0, 0.04);
}

/* Sub-tabs */
.sub-tabs-header {
  display: flex;
  border-bottom: 1px solid #E5E7EB;
  background: white;
  padding: 0 24px;
}

.sub-tab {
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  margin-right: 4px;
}

.sub-tab:hover {
  color: #374151;
}

.sub-tab.active {
  color: #1EAEDB;
  border-bottom-color: #1EAEDB;
}

.tab-content {
  padding: 24px;
  min-height: 400px;
}
</style>
