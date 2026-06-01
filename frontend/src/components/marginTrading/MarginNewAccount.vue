<template>
  <div class="margin-newaccount">
    <div class="annotation">
      按自然年统计两融新开户数据，展示本年累计开户数及周度/月度开户趋势。
    </div>

    <div class="filter-bar">
      <el-select v-model="selectedYear" style="width: 120px">
        <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
      </el-select>
      <el-button type="primary" @click="exportToExcel">
        <el-icon><Download /></el-icon>导出Excel
      </el-button>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card primary">
        <div class="kpi-label">本年累计开户</div>
        <div class="kpi-value">{{ stats.total }}户</div>
        <div class="kpi-change">数据截至：{{ selectedYear }}年</div>
      </div>
      <div class="kpi-card secondary">
        <div class="kpi-label">本周新增开户</div>
        <div class="kpi-value">{{ stats.thisWeek }}户</div>
        <div class="kpi-change">较上周 {{ stats.weekChange >= 0 ? '+' : '' }}{{ stats.weekChange }}户</div>
      </div>
      <div class="kpi-card accent">
        <div class="kpi-label">本月新增开户</div>
        <div class="kpi-value">{{ stats.thisMonth }}户</div>
        <div class="kpi-change">较上月 {{ stats.monthChange >= 0 ? '+' : '' }}{{ stats.monthChange }}户</div>
      </div>
      <div class="kpi-card info">
        <div class="kpi-label">日均新增开户</div>
        <div class="kpi-value">{{ stats.dailyAvg }}户</div>
        <div class="kpi-change">本年数据</div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">周度开户趋势（本年）</div>
        <div ref="weeklyChart" class="chart-content" style="height: 240px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">月度开户趋势（本年）</div>
        <div ref="monthlyChart" class="chart-content" style="height: 240px;"></div>
      </div>
    </div>

    <div class="table-container" style="margin-top: 20px;">
      <div class="section-title">近期开户明细</div>
      <el-table :data="accountList" stripe v-loading="loading" max-height="500">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="account_date" label="开户日期" width="120" />
        <el-table-column prop="customer_name" label="客户姓名" width="120" />
        <el-table-column prop="member_name" label="所属员工" width="120" />
        <el-table-column prop="group_name" label="营业部" width="120" />
        <el-table-column prop="asset_amount" label="开户资产(万)" align="right" width="130">
          <template #default="{ row }">
            {{ formatNumber(row.asset_amount) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import { marginTradingApi } from '../../api/marginTrading.js'

const accountList = ref([])
const loading = ref(false)
const selectedYear = ref(new Date().getFullYear())

const weeklyChart = ref(null)
const monthlyChart = ref(null)
let weeklyInstance = null
let monthlyInstance = null

const yearOptions = computed(() => {
  const current = new Date().getFullYear()
  return [current, current - 1]
})

const stats = computed(() => {
  const total = accountList.value.length
  const now = new Date()
  const currentWeek = getWeekNumber(now)
  const currentMonth = now.getMonth() + 1
  const prevMonth = currentMonth === 1 ? 12 : currentMonth - 1

  const thisWeek = accountList.value.filter(a => a.record_week === currentWeek).length
  const prevWeekCount = accountList.value.filter(a => {
    const parts = a.record_week.split('-W')
    const w = parseInt(parts[1])
    return w === (parseInt(currentWeek.split('-W')[1]) - 1)
  }).length

  const thisMonth = accountList.value.filter(a => {
    const d = new Date(a.account_date)
    return d.getMonth() + 1 === currentMonth
  }).length
  const prevMonthCount = accountList.value.filter(a => {
    const d = new Date(a.account_date)
    return d.getMonth() + 1 === prevMonth
  }).length

  const daysPassed = now.getDate()
  const dailyAvg = daysPassed > 0 ? (thisMonth / daysPassed).toFixed(1) : '0'

  return {
    total,
    thisWeek,
    weekChange: thisWeek - prevWeekCount,
    thisMonth,
    monthChange: thisMonth - prevMonthCount,
    dailyAvg
  }
})

const getWeekNumber = (d) => {
  const year = d.getFullYear()
  const oneJan = new Date(year, 0, 1)
  const weekNum = Math.ceil((((d - oneJan) / 86400000) + oneJan.getDay() + 1) / 7)
  return `${year}-W${String(weekNum).padStart(2, '0')}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await marginTradingApi.getNewAccounts({ year: selectedYear.value })
    accountList.value = res
    nextTick(() => updateCharts())
  } catch (error) {
    console.error('Failed to fetch new accounts:', error)
    ElMessage.error('获取新开户数据失败')
  } finally {
    loading.value = false
  }
}

const initCharts = () => {
  if (weeklyChart.value) weeklyInstance = echarts.init(weeklyChart.value)
  if (monthlyChart.value) monthlyInstance = echarts.init(monthlyChart.value)
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  weeklyInstance?.resize()
  monthlyInstance?.resize()
}

const updateCharts = () => {
  if (!weeklyInstance || !monthlyInstance) return

  // Weekly trend
  const weeklyMap = {}
  accountList.value.forEach(a => {
    if (!weeklyMap[a.record_week]) weeklyMap[a.record_week] = 0
    weeklyMap[a.record_week]++
  })
  const sortedWeeks = Object.keys(weeklyMap).sort()

  weeklyInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: sortedWeeks.map(w => w.split('-W')[1] + '周'),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    yAxis: {
      type: 'value', axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    series: [{
      type: 'bar', data: sortedWeeks.map(w => weeklyMap[w]),
      itemStyle: { color: '#EA580C', borderRadius: [4, 4, 0, 0] },
      barWidth: '50%'
    }]
  }, true)

  // Monthly trend
  const monthlyMap = {}
  accountList.value.forEach(a => {
    const d = new Date(a.account_date)
    const key = d.getMonth() + 1
    if (!monthlyMap[key]) monthlyMap[key] = 0
    monthlyMap[key]++
  })
  const months = Array.from({ length: 12 }, (_, i) => i + 1)

  monthlyInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category', data: months.map(m => m + '月'),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    yAxis: {
      type: 'value', axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    series: [{
      type: 'bar', data: months.map(m => monthlyMap[m] || 0),
      itemStyle: { color: '#FB923C', borderRadius: [4, 4, 0, 0] },
      barWidth: '50%'
    }]
  }, true)
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return parseFloat(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const exportToExcel = () => {
  const exportData = accountList.value.map(row => ({
    '开户日期': row.account_date,
    '客户姓名': row.customer_name,
    '所属员工': row.member_name,
    '营业部': row.group_name,
    '开户资产(万)': row.asset_amount
  }))
  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '新开户明细')
  XLSX.writeFile(wb, `两融新开户明细_${selectedYear.value}.xlsx`)
  ElMessage.success('导出成功')
}

watch(selectedYear, () => {
  fetchData()
})

const onDataImported = () => {
  fetchData()
}

onMounted(() => {
  fetchData()
  initCharts()
  window.addEventListener('margin-data-imported', onDataImported)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('margin-data-imported', onDataImported)
  weeklyInstance?.dispose()
  monthlyInstance?.dispose()
})
</script>

<style scoped>
.margin-newaccount { padding: 0; }
.annotation {
  background: #FFF7ED; border-left: 3px solid #EA580C;
  padding: 12px 16px; border-radius: 0 8px 8px 0;
  margin-bottom: 20px; font-size: 13px; color: #9A3412;
}
.filter-bar {
  display: flex; gap: 12px; margin-bottom: 20px; align-items: center;
}
.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;
  margin-bottom: 24px;
}
.kpi-card {
  background: white; border-radius: 16px; padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  position: relative; overflow: hidden;
}
.kpi-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.kpi-card.primary::before {
  background: linear-gradient(90deg, #EA580C, #FB923C);
}
.kpi-card.secondary::before {
  background: linear-gradient(90deg, #FB923C, #FDBA74);
}
.kpi-card.accent::before {
  background: linear-gradient(90deg, #F59E0B, #FB923C);
}
.kpi-card.info::before {
  background: linear-gradient(90deg, #10B981, #34D399);
}
.kpi-label { font-size: 13px; color: #6B7280; margin-bottom: 8px; }
.kpi-value {
  font-size: 28px; font-weight: 700; color: #111827; margin-bottom: 8px;
}
.kpi-change { font-size: 12px; color: #9CA3AF; }
.charts-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
}
.chart-card {
  background: white; border-radius: 12px; padding: 20px;
  border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.chart-title { font-size: 15px; font-weight: 600; color: #111827; margin-bottom: 16px; }
.chart-content { width: 100%; }
.table-container {
  background: white; border-radius: 12px; border: 1px solid #E5E7EB; overflow: hidden;
}
.section-title {
  font-size: 15px; font-weight: 600; color: #111827;
  padding: 16px 20px 0;
}
:deep(.el-button--primary) { background: #EA580C; border-color: #EA580C; }
@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}
</style>