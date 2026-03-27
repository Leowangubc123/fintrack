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

    <!-- 保有产品明细 -->
    <div class="holding-table-container">
      <div class="table-header">
        <div class="table-title">保有产品明细</div>
        <div class="strategy-filter">
          <span
            class="strategy-tag"
            :class="{ active: selectedStrategy === '' }"
            @click="selectedStrategy = ''"
          >全部</span>
          <span
            v-for="strategy in strategyTypes"
            :key="strategy"
            class="strategy-tag"
            :class="{ active: selectedStrategy === strategy }"
            @click="selectedStrategy = strategy"
          >{{ strategy }}</span>
        </div>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>产品名称</th>
              <th>策略类型</th>
              <th>风险等级</th>
              <th>管理人</th>
              <th>实际保有量(万)</th>
              <th>保有系数</th>
              <th>考核保有量(万)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredHoldings" :key="item.product_id">
              <td>{{ item.product_name }}</td>
              <td>{{ item.strategy_type }}</td>
              <td>
                <span class="risk-badge" :class="'risk-' + item.risk_level?.toLowerCase()">
                  {{ item.risk_level }}
                </span>
              </td>
              <td>{{ item.manager }}</td>
              <td>{{ formatNumber(item.holding_amount) }}万</td>
              <td>
                <span class="coefficient-cell">{{ item.holding_coefficient }}</span>
              </td>
              <td class="assessed-highlight">{{ formatNumber(item.assessed_holding) }}万</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { privateFundApi } from '../../api'

const stats = ref({
  total_holding: 0,
  avg_holding_coeff: 0,
  total_assessed_holding: 0
})

const holdings = ref([])
const period = ref('week')
const selectedStrategy = ref('')
const trendChart = ref(null)

let trendChartInstance = null

const strategyTypes = ['量化指增', '量化选股', '主观多头', '量化中性', '量化套利', '全天候策略', '其他']

const filteredHoldings = computed(() => {
  if (!selectedStrategy.value) return holdings.value
  return holdings.value.filter(h => h.strategy_type === selectedStrategy.value)
})

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

const loadHoldings = async () => {
  try {
    const res = await privateFundApi.getProductHoldings()
    holdings.value = res
  } catch (error) {
    ElMessage.error('加载保有明细失败')
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
  loadHoldings()
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.strategy-filter {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.strategy-tag {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  background: #F5F5F7;
  color: #6E6E73;
  transition: all 0.2s;
}

.strategy-tag:hover {
  background: #E5E5EA;
}

.strategy-tag.active {
  background: #7C3AED;
  color: white;
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

.risk-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
}

.risk-r3 {
  background: #E3F5E8;
  color: #1A9E3F;
}

.risk-r4 {
  background: #FFF4E0;
  color: #FF9500;
}

.risk-r5 {
  background: #FFF0EF;
  color: #FF3B30;
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
</style>
