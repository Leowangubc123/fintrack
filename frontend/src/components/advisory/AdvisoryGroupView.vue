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
        <span class="summary-item">
          <span class="summary-label">全辖区合计</span>
          <span class="summary-value">签约户数 {{ formatNumber(totalStats.households) }}户</span>
          <span class="summary-dot">·</span>
          <span class="summary-value">签约资产 {{ formatNumber(totalStats.assets) }}万</span>
          <span class="summary-dot">·</span>
          <span class="summary-value">投顾收入 {{ formatNumber(totalStats.income) }}元</span>
        </span>
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
          <div class="rank" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
          <div class="group-info">
            <div class="group-name">{{ group.group_name }}</div>
            <div class="group-meta">
              <span>签约 {{ group.total_households }}户</span>
              <span class="meta-dot">·</span>
              <span>资产 ¥{{ formatBigAsset(group.total_assets) }}</span>
              <span class="meta-dot">·</span>
              <span>收入 ¥{{ formatNumber(group.total_income) }}万</span>
            </div>
          </div>
          <div class="group-rates">
            <div class="rate-box">
              <div class="rate-value" :class="getProgressClass(group.income_rate)">{{ group.income_rate }}%</div>
              <div class="rate-label">收入完成率</div>
              <div class="rate-bar-mini">
                <div
                  class="rate-bar-mini-fill"
                  :class="getProgressClass(group.income_rate)"
                  :style="{ width: Math.min(group.income_rate, 100) + '%' }"
                />
              </div>
            </div>
            <div class="rate-box">
              <div class="rate-value" :class="getProgressClass(group.households_rate)">{{ group.households_rate }}%</div>
              <div class="rate-label">户数完成率</div>
              <div class="rate-bar-mini">
                <div
                  class="rate-bar-mini-fill"
                  :class="getProgressClass(group.households_rate)"
                  :style="{ width: Math.min(group.households_rate, 100) + '%' }"
                />
              </div>
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
                ¥{{ (group.product_stats[product]?.assets || 0).toFixed(1) }}<span class="unit">万</span>
              </div>
            </div>
          </div>

          <!-- Recent Subscriptions -->
          <div class="recent-section">
            <div class="section-title">最近签约明细</div>
            <div class="subscription-table">
              <div class="table-header">
                <div class="th" style="width: 120px">签约日期</div>
                <div class="th" style="flex: 1">员工</div>
                <div class="th" style="width: 100px">产品</div>
                <div class="th" style="width: 120px" align="right">签约资产</div>
                <div class="th" style="width: 120px" align="right">投顾收入</div>
              </div>
              <div
                v-for="row in group.recent_subscriptions"
                :key="row.id || row.subscription_date + row.member_name"
                class="table-row"
              >
                <div class="td" style="width: 120px">{{ row.subscription_date }}</div>
                <div class="td" style="flex: 1">{{ row.member_name }}</div>
                <div class="td" style="width: 100px">
                  <span class="product-tag">{{ row.product_type }}</span>
                </div>
                <div class="td" style="width: 120px" align="right">¥{{ ((row.asset_amount || 0) / 10000).toFixed(1) }}万</div>
                <div class="td" style="width: 120px" align="right">¥{{ formatNumber(row.advisory_income || 0) }}</div>
              </div>
              <div v-if="group.recent_subscriptions.length === 0" class="table-empty">
                暂无签约明细
              </div>
            </div>
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

const productOrder = ['万2', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT']

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN')
}

const formatBigAsset = (num) => {
  if (num === null || num === undefined) return '0万'
  if (num >= 10000) return (num / 10000).toFixed(1) + '亿'
  return num.toFixed(1) + '万'
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

  subscriptions.value.forEach(sub => {
    const groupId = sub.group_id
    if (!stats[groupId]) return

    const converted = sub.converted_households || 1
    stats[groupId].total_households += converted
    stats[groupId].total_assets += parseFloat(sub.asset_amount || 0) / 10000
    stats[groupId].total_income += parseFloat(sub.advisory_income || 0)

    const product = sub.product_type
    if (stats[groupId].product_stats[product]) {
      stats[groupId].product_stats[product].households += converted
      stats[groupId].product_stats[product].assets += parseFloat(sub.asset_amount || 0) / 10000
    }
  })

  Object.keys(stats).forEach(groupId => {
    const groupSubs = subscriptions.value
      .filter(s => s.group_id === parseInt(groupId))
      .sort((a, b) => new Date(b.subscription_date) - new Date(a.subscription_date))
      .slice(0, 5)
    stats[groupId].recent_subscriptions = groupSubs
  })

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
  font-size: 14px;
}

.summary-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #374151;
}

.summary-label {
  font-weight: 500;
  color: #6B7280;
}

.summary-value {
  font-weight: 600;
  color: #111827;
}

.summary-dot {
  color: #9CA3AF;
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
  padding: 18px 24px;
  cursor: pointer;
  gap: 20px;
}

.rank {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F3F4F6;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  color: #374151;
  flex-shrink: 0;
}

.rank-1 {
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  color: #B45309;
}

.rank-2 {
  background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
  color: #374151;
}

.rank-3 {
  background: linear-gradient(135deg, #FCE7F3 0%, #FBCFE8 100%);
  color: #BE185D;
}

.group-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.group-name {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.group-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
  flex-wrap: wrap;
}

.meta-dot {
  color: #9CA3AF;
}

.group-rates {
  display: flex;
  align-items: center;
  gap: 28px;
  flex-shrink: 0;
}

.rate-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 70px;
}

.rate-value {
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
}

.rate-value.success {
  color: #10B981;
}

.rate-value.warning {
  color: #F59E0B;
}

.rate-value.danger {
  color: #EF4444;
}

.rate-label {
  font-size: 12px;
  color: #6B7280;
}

.rate-bar-mini {
  width: 60px;
  height: 4px;
  background: #F3F4F6;
  border-radius: 2px;
  overflow: hidden;
}

.rate-bar-mini-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.rate-bar-mini-fill.success {
  background: #10B981;
}

.rate-bar-mini-fill.warning {
  background: #F59E0B;
}

.rate-bar-mini-fill.danger {
  background: #EF4444;
}

.expand-icon {
  color: #9CA3AF;
  font-size: 16px;
  flex-shrink: 0;
  margin-left: 8px;
}

.group-detail {
  padding: 24px;
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
  border-radius: 10px;
  padding: 18px 12px;
  text-align: center;
  border: 1px solid #E5E7EB;
}

.product-name {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 10px;
}

.product-households {
  font-size: 22px;
  font-weight: 700;
  color: #1456f0;
  margin-bottom: 6px;
}

.product-assets {
  font-size: 14px;
  font-weight: 500;
  color: #1456f0;
}

.unit {
  font-size: 12px;
  margin-left: 2px;
  opacity: 0.8;
  font-weight: 500;
}

.recent-section {
  background: white;
  border-radius: 10px;
  padding: 20px;
  border: 1px solid #E5E7EB;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

.subscription-table {
  width: 100%;
}

.table-header {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #F3F4F6;
  font-size: 13px;
  font-weight: 600;
  color: #6B7280;
}

.table-row {
  display: flex;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid #F3F4F6;
  font-size: 14px;
  color: #111827;
  transition: background 0.15s ease;
}

.table-row:hover {
  background: #FAFAFB;
}

.table-row:last-child {
  border-bottom: none;
}

.th,
.td {
  padding: 0 8px;
}

.th:first-child,
.td:first-child {
  padding-left: 0;
}

.th:last-child,
.td:last-child {
  padding-right: 0;
}

.product-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  background: #EFF6FF;
  color: #1456f0;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.table-empty {
  padding: 24px 0;
  text-align: center;
  color: #9CA3AF;
  font-size: 14px;
}

@media (max-width: 1200px) {
  .detail-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .group-rates {
    gap: 16px;
  }
}

@media (max-width: 900px) {
  .group-summary {
    flex-wrap: wrap;
    gap: 12px 16px;
  }

  .group-info {
    width: 100%;
  }

  .group-rates {
    width: 100%;
    justify-content: flex-end;
    margin-left: 56px;
  }

  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .table-header,
  .table-row {
    font-size: 13px;
  }
}
</style>
