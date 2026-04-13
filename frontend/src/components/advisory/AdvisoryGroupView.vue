<template>
  <div class="advisory-group-view">
    <!-- Header with year selector -->
    <div class="view-header">
      <div class="year-selector">
        <el-select v-model="selectedYear" style="width: 120px">
          <el-option v-for="year in years" :key="year" :label="year + '年'" :value="year" />
        </el-select>
      </div>
      <div class="summary-stats" v-if="totalStats">
        <span>全辖区合计：签约户数 {{ formatNumber(totalStats.households) }}户</span>
        <span>签约资产 {{ formatNumber(totalStats.assets) }}万</span>
        <span>投顾收入 {{ formatNumber(totalStats.income) }}元</span>
      </div>
    </div>

    <!-- Groups List -->
    <div class="groups-list">
      <div
        v-for="(group, index) in groupStats"
        :key="group.group_id"
        class="group-item"
        :class="{ expanded: expandedGroup === group.group_id }"
      >
        <!-- Summary Row -->
        <div class="group-summary" @click="toggleExpand(group.group_id)">
          <div class="rank">{{ index + 1 }}</div>
          <div class="group-name">{{ group.group_name }}</div>
          <div class="group-summary-stats">
            <span>{{ group.total_households }}户</span>
            <span>{{ group.total_assets }}万</span>
          </div>
          <div class="progress-section">
            <div class="progress-item">
              <span class="progress-label">收入完成率</span>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :class="getProgressClass(group.income_rate)"
                  :style="{ width: Math.min(group.income_rate, 100) + '%' }"
                />
              </div>
              <span class="progress-value" :class="getProgressClass(group.income_rate)">
                {{ group.income_rate }}%
              </span>
            </div>
            <div class="progress-item">
              <span class="progress-label">户数完成率</span>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :class="getProgressClass(group.households_rate)"
                  :style="{ width: Math.min(group.households_rate, 100) + '%' }"
                />
              </div>
              <span class="progress-value" :class="getProgressClass(group.households_rate)">
                {{ group.households_rate }}%
              </span>
            </div>
          </div>
          <div class="expand-icon">
            <el-icon><ArrowDown v-if="expandedGroup !== group.group_id" /><ArrowUp v-else /></el-icon>
          </div>
        </div>

        <!-- Expanded Detail -->
        <div v-if="expandedGroup === group.group_id" class="group-detail">
          <div class="detail-grid">
            <div
              v-for="product in productOrder"
              :key="product"
              class="product-cell"
            >
              <div class="product-name">{{ product }}</div>
              <div class="product-households">
                {{ group.product_stats[product]?.households || 0 }}<span class="unit">户</span>
              </div>
              <div class="product-assets">
                {{ group.product_stats[product]?.assets || 0 }}<span class="unit">万</span>
              </div>
            </div>
          </div>

          <!-- Recent Subscriptions -->
          <div class="recent-section">
            <div class="section-title">最近签约明细</div>
            <el-table :data="group.recent_subscriptions" size="small" stripe>
              <el-table-column prop="subscription_date" label="签约日期" width="120" />
              <el-table-column prop="member_name" label="员工" width="100" />
              <el-table-column prop="product_type" label="产品" width="100" />
              <el-table-column prop="asset_amount" label="资产(万)" width="100">
                <template #default="{ row }">{{ row.asset_amount }}万</template>
              </el-table-column>
              <el-table-column prop="advisory_income" label="收入(元)" width="100">
                <template #default="{ row }">{{ row.advisory_income }}元</template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { advisoryApi } from '../../api/advisory.js'
import { groupsApi } from '../../api/index.js'

const selectedYear = ref(new Date().getFullYear())
const years = computed(() => {
  const current = new Date().getFullYear()
  return [current, current - 1]
})

const groups = ref([])
const subscriptions = ref([])
const targets = ref([])
const expandedGroup = ref(null)

const productOrder = ['千1', '千3', '万2', '网格', '量化T', 'GWT']

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN')
}

const fetchGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchSubscriptions = async () => {
  try {
    const res = await advisoryApi.getSubscriptions({
      year: selectedYear.value,
      page_size: 1000
    })
    subscriptions.value = res.items || []
  } catch (error) {
    console.error('Failed to fetch subscriptions:', error)
    ElMessage.error('获取签约数据失败')
  }
}

const fetchTargets = async () => {
  try {
    const res = await advisoryApi.getTargets({
      year: selectedYear.value
    })
    targets.value = res || []
  } catch (error) {
    console.error('Failed to fetch targets:', error)
  }
}

const groupStats = computed(() => {
  const stats = {}

  // Initialize stats for all groups
  groups.value.forEach(group => {
    stats[group.id] = {
      group_id: group.id,
      group_name: group.name,
      total_households: 0,
      total_assets: 0,
      total_income: 0,
      product_stats: {},
      recent_subscriptions: []
    }
    productOrder.forEach(p => {
      stats[group.id].product_stats[p] = { households: 0, assets: 0 }
    })
  })

  // Aggregate subscription data
  subscriptions.value.forEach(sub => {
    const groupId = sub.group_id
    if (!stats[groupId]) return

    const converted = sub.converted_households || 1
    stats[groupId].total_households += converted
    stats[groupId].total_assets += parseFloat(sub.asset_amount || 0)
    stats[groupId].total_income += parseFloat(sub.advisory_income || 0)

    const product = sub.product_type
    if (stats[groupId].product_stats[product]) {
      stats[groupId].product_stats[product].households += converted
      stats[groupId].product_stats[product].assets += parseFloat(sub.asset_amount || 0)
    }
  })

  // Add recent subscriptions (top 5 per group)
  Object.keys(stats).forEach(groupId => {
    const groupSubs = subscriptions.value
      .filter(s => s.group_id === parseInt(groupId))
      .sort((a, b) => new Date(b.subscription_date) - new Date(a.subscription_date))
      .slice(0, 5)
    stats[groupId].recent_subscriptions = groupSubs
  })

  // Calculate completion rates
  Object.values(stats).forEach(group => {
    const target = targets.value.find(t => t.group_id === group.group_id)
    if (target) {
      group.income_rate = target.income_target > 0
        ? Math.round((group.total_income / (target.income_target * 10000)) * 100)
        : 0
      group.households_rate = target.households_target > 0
        ? Math.round((group.total_households / target.households_target) * 100)
        : 0
    } else {
      group.income_rate = 0
      group.households_rate = 0
    }
  })

  // Sort by total households desc
  return Object.values(stats).sort((a, b) => b.total_households - a.total_households)
})

const totalStats = computed(() => {
  return groupStats.value.reduce((acc, group) => ({
    households: acc.households + group.total_households,
    assets: acc.assets + group.total_assets,
    income: acc.income + group.total_income
  }), { households: 0, assets: 0, income: 0 })
})

const toggleExpand = (groupId) => {
  expandedGroup.value = expandedGroup.value === groupId ? null : groupId
}

const getProgressClass = (rate) => {
  if (rate >= 100) return 'success'
  if (rate >= 50) return 'warning'
  return 'danger'
}

const loadData = async () => {
  await Promise.all([
    fetchSubscriptions(),
    fetchTargets()
  ])
}

watch(selectedYear, () => {
  loadData()
})

onMounted(() => {
  fetchGroups()
  loadData()
})
</script>

<style scoped>
.advisory-group-view {
  padding: 0;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.summary-stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: #6B7280;
}

.summary-stats span {
  font-weight: 500;
  color: #111827;
}

.groups-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-item {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  overflow: hidden;
  transition: all 0.2s ease;
}

.group-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.group-summary {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  gap: 16px;
}

.rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F3F4F6;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 600;
  color: #6B7280;
}

.group-item:nth-child(1) .rank {
  background: #FEF3C7;
  color: #D97706;
}

.group-item:nth-child(2) .rank {
  background: #E5E7EB;
  color: #4B5563;
}

.group-item:nth-child(3) .rank {
  background: #FCE7F3;
  color: #BE185D;
}

.group-name {
  flex: 0 0 150px;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.group-summary-stats {
  flex: 0 0 180px;
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #6B7280;
}

.progress-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-label {
  font-size: 12px;
  color: #9CA3AF;
  width: 70px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #F3F4F6;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-fill.success {
  background: #10B981;
}

.progress-fill.warning {
  background: #F59E0B;
}

.progress-fill.danger {
  background: #EF4444;
}

.progress-value {
  font-size: 12px;
  font-weight: 600;
  width: 45px;
  text-align: right;
}

.progress-value.success {
  color: #10B981;
}

.progress-value.warning {
  color: #F59E0B;
}

.progress-value.danger {
  color: #EF4444;
}

.expand-icon {
  color: #9CA3AF;
  font-size: 16px;
}

.group-detail {
  padding: 20px;
  background: #FAFAFB;
  border-top: 1px solid #E5E7EB;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.product-cell {
  background: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #E5E7EB;
}

.product-name {
  font-size: 14px;
  font-weight: 600;
  color: #6B7280;
  margin-bottom: 8px;
}

.product-households {
  font-size: 20px;
  font-weight: 600;
  color: #0891B2;
  margin-bottom: 4px;
}

.product-assets {
  font-size: 14px;
  color: #0891B2;
}

.unit {
  font-size: 12px;
  margin-left: 2px;
  opacity: 0.8;
}

.recent-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

@media (max-width: 1200px) {
  .detail-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .group-summary {
    flex-wrap: wrap;
  }

  .progress-section {
    width: 100%;
    margin-top: 8px;
  }

  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
