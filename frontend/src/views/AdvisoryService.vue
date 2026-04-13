<template>
  <div class="advisory-service">
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

    <!-- 年度看板 -->
    <div v-if="activeTab === 'annual-dashboard'" class="tab-content">
      <AdvisoryDashboard />
    </div>

    <!-- 营业部视图 -->
    <div v-if="activeTab === 'group-view'" class="tab-content">
      <AdvisoryGroupView />
    </div>

    <!-- 个人视图 -->
    <div v-if="activeTab === 'member-view'" class="tab-content">
      <AdvisoryMemberView />
    </div>

    <!-- 数据导入 -->
    <div v-if="activeTab === 'import'" class="tab-content">
      数据导入
    </div>

    <!-- 考核管理 -->
    <div v-if="activeTab === 'target'" class="tab-content">
      考核管理
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AdvisoryDashboard from '../components/advisory/AdvisoryDashboard.vue'
import AdvisoryGroupView from '../components/advisory/AdvisoryGroupView.vue'
import AdvisoryMemberView from '../components/advisory/AdvisoryMemberView.vue'

const tabs = [
  { key: 'annual-dashboard', label: '年度看板' },
  { key: 'group-view', label: '营业部视图' },
  { key: 'member-view', label: '个人视图' },
  { key: 'import', label: '数据导入' },
  { key: 'target', label: '考核管理' }
]

const activeTab = ref('annual-dashboard')
</script>

<style scoped>
.advisory-service {
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
  color: #0891B2;
  border-bottom-color: #0891B2;
  background: rgba(8, 145, 178, 0.05);
}

.tab-content {
  padding: 24px;
  min-height: 400px;
}
</style>
