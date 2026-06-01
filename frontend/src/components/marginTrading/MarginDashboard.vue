<template>
  <div class="margin-dashboard">
    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card primary">
        <div class="kpi-label">辖区时点余额</div>
        <div class="kpi-value">{{ formatBigNumber(stats.spot_balance) }}</div>
        <div class="kpi-change" :class="stats.spot_change >= 0 ? 'up' : 'down'">
          较上周 {{ stats.spot_change >= 0 ? '+' : '' }}{{ formatNumber(stats.spot_change) }}万 {{ stats.spot_change >= 0 ? '↑' : '↓' }}
        </div>
        <div class="kpi-update">最近更新：{{ stats.last_update_date || '-' }}</div>
      </div>
      <div class="kpi-card secondary">
        <div class="kpi-label">辖区日均余额</div>
        <div class="kpi-value">{{ formatBigNumber(stats.daily_balance) }}</div>
        <div class="kpi-change" :class="stats.daily_change >= 0 ? 'up' : 'down'">
          较上周 {{ stats.daily_change >= 0 ? '+' : '' }}{{ formatNumber(stats.daily_change) }}万 {{ stats.daily_change >= 0 ? '↑' : '↓' }}
        </div>
        <div class="kpi-update">最近更新：{{ stats.last_update_date || '-' }}</div>
      </div>
      <div class="kpi-card info">
        <div class="kpi-label">今年开户数量</div>
        <div class="kpi-value">{{ stats.new_account_count }}户</div>
        <div class="kpi-change" :class="stats.account_change >= 0 ? 'up' : 'down'">
          较上周 {{ stats.account_change >= 0 ? '+' : '' }}{{ stats.account_change }}户 {{ stats.account_change >= 0 ? '↑' : '↓' }}
        </div>
        <div class="kpi-update">最近更新：{{ stats.last_update_date || '-' }}</div>
      </div>
      <div class="kpi-card accent">
        <div class="kpi-label">息费收入</div>
        <div class="kpi-value">{{ formatNumber(stats.income_total) }}万</div>
        <div class="kpi-change" :class="stats.income_change >= 0 ? 'up' : 'down'">
          较上周 {{ stats.income_change >= 0 ? '+' : '' }}{{ formatNumber(stats.income_change) }}万 {{ stats.income_change >= 0 ? '↑' : '↓' }}
        </div>
        <div class="kpi-update">最近更新：{{ stats.last_update_date || '-' }}</div>
      </div>
    </div>

    <!-- Charts Row 1 -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">各营业部时点余额分布</div>
        </div>
        <div ref="spotPieChart" class="chart-content" style="height: 280px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">各营业部日均余额分布</div>
        </div>
        <div ref="dailyPieChart" class="chart-content" style="height: 280px;"></div>
      </div>
    </div>

    <!-- Charts Row 2 -->
    <div class="charts-grid" style="margin-top: 20px;">
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">本年两融开户趋势</div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div>
            <div class="chart-subtitle">周度趋势</div>
            <div ref="weeklyChart" class="chart-content" style="height: 200px;"></div>
          </div>
          <div>
            <div class="chart-subtitle">月度趋势</div>
            <div ref="monthlyChart" class="chart-content" style="height: 200px;"></div>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">本年度营业部息费收入分布</div>
        </div>
        <div ref="incomePieChart" class="chart-content" style="height: 280px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { marginTradingApi } from '../../api/marginTrading.js'

const stats = ref({
  spot_balance: 0,
  daily_balance: 0,
  new_account_count: 0,
  income_total: 0,
  spot_change: 0,
  daily_change: 0,
  account_change: 0,
  income_change: 0,
  last_update_date: null,
  group_distribution: [],
  income_distribution: [],
  weekly_account_trend: [],
  monthly_account_trend: []
})

const spotPieChart = ref(null)
const dailyPieChart = ref(null)
const incomePieChart = ref(null)
const weeklyChart = ref(null)
const monthlyChart = ref(null)

let spotPieInstance = null
let dailyPieInstance = null
let incomePieInstance = null
let weeklyInstance = null
let monthlyInstance = null

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN')
}

const formatBigNumber = (num) => {
  if (num === null || num === undefined) return '0'
  if (num >= 10000) return (num / 10000).toFixed(2) + '亿'
  return num.toLocaleString('zh-CN') + '万'
}

const fetchStats = async () => {
  try {
    const res = await marginTradingApi.getStats({ year: new Date().getFullYear() })
    stats.value = res
    nextTick(() => updateCharts())
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    ElMessage.error('获取统计数据失败')
  }
}

const initCharts = () => {
  if (spotPieChart.value) spotPieInstance = echarts.init(spotPieChart.value)
  if (dailyPieChart.value) dailyPieInstance = echarts.init(dailyPieChart.value)
  if (incomePieChart.value) incomePieInstance = echarts.init(incomePieChart.value)
  if (weeklyChart.value) weeklyInstance = echarts.init(weeklyChart.value)
  if (monthlyChart.value) monthlyInstance = echarts.init(monthlyChart.value)
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  spotPieInstance?.resize()
  dailyPieInstance?.resize()
  incomePieInstance?.resize()
  weeklyInstance?.resize()
  monthlyInstance?.resize()
}

const updateCharts = () => {
  updatePieChart(spotPieInstance, stats.value.group_distribution, 'spot_balance', '时点余额')
  updatePieChart(dailyPieInstance, stats.value.group_distribution, 'daily_balance', '日均余额')
  updatePieChart(incomePieInstance, stats.value.income_distribution, 'income', '息费收入')
  updateWeeklyChart()
  updateMonthlyChart()
}

const updatePieChart = (instance, data, valueKey, name) => {
  if (!instance || !data || data.length === 0) return
  const colors = ['#EA580C', '#FB923C', '#FDBA74', '#FED7AA', '#FFEDD5', '#FFF7ED']
  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}万 ({d}%)' },
    color: colors,
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' }
      },
      data: data.map((item, idx) => ({
        name: item.group_name,
        value: item[valueKey] || 0,
        itemStyle: { color: colors[idx % colors.length] }
      }))
    }]
  }
  instance.setOption(option, true)
}

const updateWeeklyChart = () => {
  if (!weeklyInstance) return
  const trend = stats.value.weekly_account_trend || []
  if (trend.length === 0) return
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: trend.map(t => t.week.split('-W')[1] + '周'),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    series: [{
      type: 'bar',
      data: trend.map(t => t.count),
      itemStyle: { color: '#EA580C', borderRadius: [4, 4, 0, 0] },
      barWidth: '50%'
    }]
  }
  weeklyInstance.setOption(option, true)
}

const updateMonthlyChart = () => {
  if (!monthlyInstance) return
  const trend = stats.value.monthly_account_trend || []
  if (trend.length === 0) return
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: trend.map(t => t.month + '月'),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    series: [{
      type: 'bar',
      data: trend.map(t => t.count),
      itemStyle: { color: '#FB923C', borderRadius: [4, 4, 0, 0] },
      barWidth: '50%'
    }]
  }
  monthlyInstance.setOption(option, true)
}

const onDataImported = () => {
  fetchStats()
}

onMounted(() => {
  fetchStats()
  initCharts()
  window.addEventListener('margin-data-imported', onDataImported)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('margin-data-imported', onDataImported)
  spotPieInstance?.dispose()
  dailyPieInstance?.dispose()
  incomePieInstance?.dispose()
  weeklyInstance?.dispose()
  monthlyInstance?.dispose()
})
</script>

<style scoped>
.margin-dashboard {
  padding: 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.kpi-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.kpi-card.primary::before {
  background: linear-gradient(90deg, #EA580C, #FB923C);
}

.kpi-card.secondary::before {
  background: linear-gradient(90deg, #FB923C, #FDBA74);
}

.kpi-card.info::before {
  background: linear-gradient(90deg, #10B981, #34D399);
}

.kpi-card.accent::before {
  background: linear-gradient(90deg, #F59E0B, #FB923C);
}

.kpi-label {
  font-size: 13px;
  color: #6B7280;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 8px;
}

.kpi-change {
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
}

.kpi-change.up { color: #EF4444; }
.kpi-change.down { color: #10B981; }

.kpi-update {
  font-size: 11px;
  color: #9CA3AF;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #E5E7EB;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.chart-subtitle {
  font-size: 12px;
  color: #9CA3AF;
  margin-bottom: 8px;
}

.chart-content {
  width: 100%;
}

@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
