<template>
  <div class="margin-trading">
    <!-- Top Tabs -->
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

    <!-- Tab Content -->
    <div class="tab-content">
      <MarginDashboard v-if="activeTab === 'dashboard'" />
      <MarginPersonalBalance v-if="activeTab === 'personal'" />
      <MarginGroupBalance v-if="activeTab === 'group'" />
      <MarginIncome v-if="activeTab === 'income'" />
      <MarginNewAccount v-if="activeTab === 'newaccount'" />
      <MarginTarget v-if="activeTab === 'target'" />
      <MarginImport v-if="activeTab === 'import'" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MarginDashboard from '../components/marginTrading/MarginDashboard.vue'
import MarginPersonalBalance from '../components/marginTrading/MarginPersonalBalance.vue'
import MarginGroupBalance from '../components/marginTrading/MarginGroupBalance.vue'
import MarginIncome from '../components/marginTrading/MarginIncome.vue'
import MarginNewAccount from '../components/marginTrading/MarginNewAccount.vue'
import MarginTarget from '../components/marginTrading/MarginTarget.vue'
import MarginImport from '../components/marginTrading/MarginImport.vue'

const tabs = [
  { key: 'dashboard', label: '年度看板' },
  { key: 'personal', label: '个人余额' },
  { key: 'group', label: '营业部余额' },
  { key: 'income', label: '息费收入' },
  { key: 'newaccount', label: '新开户统计' },
  { key: 'target', label: '考核管理' },
  { key: 'import', label: '数据导入' }
]

const activeTab = ref('dashboard')
</script>

<style scoped>
.margin-trading {
  padding: 20px;
}

.tabs-header {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid #F3F4F6;
  padding-bottom: 2px;
}

.tab-item {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
  border-radius: 8px 8px 0 0;
}

.tab-item:hover {
  color: #7C3AED;
  background: #F3E8FF;
}

.tab-item.active {
  color: #7C3AED;
  border-bottom-color: #7C3AED;
  background: #F3E8FF;
  font-weight: 600;
}

.tab-content {
  min-height: 400px;
}
</style>
