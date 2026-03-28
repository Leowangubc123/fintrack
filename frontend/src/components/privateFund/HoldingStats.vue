<template>
  <div class="holding-stats">
    <!-- 保有概览卡片 -->
    <div class="holding-summary">
      <div class="holding-card actual">
        <div class="holding-card-icon">💰</div>
        <div class="holding-card-label">实际保有量</div>
        <div class="holding-card-value">{{ formatNumber(stats.total_holding) }}万</div>
        <div class="holding-card-hint">累计买入 - 累计赎回</div>
      </div>
      <div class="holding-card coeff">
        <div class="holding-card-icon">⚖️</div>
        <div class="holding-card-label">加权平均保有系数</div>
        <div class="holding-card-value">{{ stats.avg_holding_coeff?.toFixed(2) || '0.00' }}</div>
        <div class="holding-card-hint">按保有量加权计算</div>
      </div>
      <div class="holding-card assessed">
        <div class="holding-card-icon">🎯</div>
        <div class="holding-card-label">考核保有量</div>
        <div class="holding-card-value assessed">{{ formatNumber(stats.total_assessed_holding) }}万</div>
        <div class="holding-card-hint">实际保有量 × 保有系数</div>
      </div>
    </div>

    <!-- 考核保有量趋势图 -->
    <div class="chart-card">
      <div class="chart-header">
        <div>
          <div class="chart-title">考核保有量趋势</div>
          <div class="chart-subtitle">按周期统计考核保有量变化</div>
        </div>
        <div class="period-tabs">
          <div
            class="period-tab"
            :class="{ active: period === 'week' }"
            @click="changePeriod('week')"
          >周度</div>
          <div
            class="period-tab"
            :class="{ active: period === 'month' }"
            @click="changePeriod('month')"
          >月度</div>
          <div
            class="period-tab"
            :class="{ active: period === 'quarter' }"
            @click="changePeriod('quarter')"
          >季度</div>
        </div>
      </div>
      <div ref="trendChart" class="chart-content" style="height: 300px;"></div>
    </div>

    <!-- 营业部保有明细 -->
    <div class="holding-table-container">
      <div class="table-header">
        <div class="table-title">营业部保有明细</div>
        <div class="table-subtitle">各营业部私募产品保有情况统计</div>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>营业部</th>
              <th>实际保有量(万)</th>
              <th>保有系数</th>
              <th>考核保有量(万)</th>
              <th>产品数量</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in groupHoldings" :key="item.group_id">
              <td class="group-name">{{ item.group_name }}</td>
              <td>{{ formatNumber(item.holding_amount) }}万</td>
              <td>
                <span class="coefficient-cell">{{ item.avg_holding_coeff.toFixed(2) }}</span>
              </td>
              <td class="assessed-highlight">{{ formatNumber(item.assessed_holding) }}万</td>
              <td>{{ item.product_count }}</td>
            </tr>
            <tr v-if="groupHoldings.length === 0">
              <td colspan="5" class="empty-row">暂无保有数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { privateFundApi } from '../../api'

const stats = ref({
  total_holding: 0,
  avg_holding_coeff: 0,
  total_assessed_holding: 0
})

const transactions = ref([])
const products = ref([])
const period = ref('week')
const trendChart = ref(null)

let trendChartInstance = null

// 计算各营业部保有数据
const groupHoldings = computed(() => {
  // 按营业部统计
  const groupStats = {}

  transactions.value.forEach(t => {
    if (t.transaction_type !== 'sale') return // 只统计销售

    const groupId = t.group_id || 'unknown'
    const groupName = t.group_name || '未知营业部'

    if (!groupStats[groupId]) {
      groupStats[groupId] = {
        group_id: groupId,
        group_name: groupName,
        total_holding: 0,
        total_coeff: 0,
        product_count: 0,
        products: new Set()
      }
    }

    // 计算该交易的当前保有（销售 - 赎回）
    const netHolding = calculateNetHolding(t.product_id, t.member_id)
    if (netHolding > 0) {
      groupStats[groupId].total_holding += netHolding
      groupStats[groupId].total_coeff += netHolding * (t.holding_coefficient || 1.0)
      groupStats[groupId].products.add(t.product_id)
    }
  })

  // 转换为数组并计算考核保有量
  return Object.values(groupStats)
    .map(g => {
      const avgCoeff = g.total_holding > 0 ? g.total_coeff / g.total_holding : 1.0
      return {
        group_id: g.group_id,
        group_name: g.group_name,
        holding_amount: g.total_holding,
        avg_holding_coeff: avgCoeff,
        assessed_holding: g.total_holding * avgCoeff,
        product_count: g.products.size
      }
    })
    .sort((a, b) => b.assessed_holding - a.assessed_holding)
})

// 计算某个产品的净保有（简化计算）
function calculateNetHolding(productId, memberId) {
  let holding = 0
  transactions.value
    .filter(t => t.product_id === productId && t.member_id === memberId)
    .forEach(t => {
      if (t.transaction_type === 'sale') {
        holding += t.amount
      } else {
        holding -= t.amount
      }
    })
  return Math.max(0, holding)
}

const formatNumber = (num) => {
  if (!num) return '0'
  return parseFloat(num).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 1 })
}

const initTrendChart = (data) => {
  if (!trendChart.value) return

  trendChartInstance = echarts.init(trendChart.value)

  const xAxisData = data.map(d => d.period)
  const seriesData = data.map(d => d.assessed_holding)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>考核保有量: {c}万'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData
    },
    yAxis: {
      type: 'value',
      name: '考核保有量(万)'
    },
    series: [{
      name: '考核保有量',
      type: 'line',
      smooth: true,
      data: seriesData,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 122, 255, 0.3)' },
          { offset: 1, color: 'rgba(0, 122, 255, 0.05)' }
        ])
      },
      lineStyle: {
        color: '#007AFF',
        width: 3
      },
      itemStyle: {
        color: '#007AFF'
      }
    }]
  }

  trendChartInstance.setOption(option)
}

const loadStats = async () => {
  try {
    const res = await privateFundApi.getHoldingStats()
    stats.value = res
  } catch (error) {
    ElMessage.error('加载保有统计失败')
  }
}

const loadTransactions = async () => {
  try {
    // 获取所有交易记录
    const res = await privateFundApi.getRecentTransactions(1000)
    transactions.value = res
  } catch (error) {
    ElMessage.error('加载交易记录失败')
  }
}

const loadTrendData = async () => {
  try {
    const res = await privateFundApi.getHoldingTrend(period.value)
    initTrendChart(res)
  } catch (error) {
    ElMessage.error('加载趋势数据失败')
  }
}

const changePeriod = (newPeriod) => {
  period.value = newPeriod
  loadTrendData()
}

const handleResize = () => {
  trendChartInstance?.resize()
}

onMounted(() => {
  loadStats()
  loadTransactions()
  loadTrendData()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.holding-stats {
  padding: 24px;
}

.holding-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.holding-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  text-align: center;
}

.holding-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  font-size: 24px;
}

.holding-card.actual .holding-card-icon {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
}

.holding-card.coeff .holding-card-icon {
  background: linear-gradient(135deg, rgba(255, 149, 0, 0.1) 0%, rgba(255, 107, 53, 0.1) 100%);
}

.holding-card.assessed .holding-card-icon {
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.1) 0%, rgba(88, 86, 214, 0.1) 100%);
}

.holding-card-label {
  font-size: 13px;
  color: #6E6E73;
  margin-bottom: 8px;
}

.holding-card-value {
  font-size: 32px;
  font-weight: 700;
  color: #1D1D1F;
}

.holding-card-value.assessed {
  background: linear-gradient(135deg, #007AFF, #5856D6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.holding-card-hint {
  font-size: 12px;
  color: #8E8E93;
  margin-top: 4px;
}

.chart-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-bottom: 24px;
}

.chart-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.chart-subtitle {
  font-size: 13px;
  color: #8E8E93;
}

.chart-content {
  padding: 20px;
}

.period-tabs {
  display: flex;
  gap: 8px;
  padding: 4px;
  background: #F5F5F7;
  border-radius: 10px;
}

.period-tab {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  color: #6E6E73;
}

.period-tab:hover {
  color: #1D1D1F;
}

.period-tab.active {
  background: white;
  color: #7C3AED;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.holding-table-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.table-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.table-subtitle {
  font-size: 13px;
  color: #8E8E93;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #FAFAFB;
  padding: 14px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #6E6E73;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.data-table td {
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 14px;
  color: #1D1D1F;
}

.data-table tr:hover {
  background: #FAFAFB;
}

.group-name {
  font-weight: 600;
  color: #1D1D1F;
}

.coefficient-cell {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(255, 149, 0, 0.1);
  color: #FF9500;
  border-radius: 6px;
  font-weight: 600;
}

.assessed-highlight {
  color: #007AFF;
  font-weight: 700;
}

.empty-row {
  text-align: center;
  color: #8E8E93;
  padding: 40px;
}
</style>
