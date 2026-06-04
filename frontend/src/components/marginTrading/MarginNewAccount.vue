<template>
  <div class="margin-newaccount">
    <div class="annotation">
      按自然年统计两融新开户数据，展示本年累计开户数及周度/月度开户趋势。
    </div>

    <div class="filter-bar">
      <el-select v-model="selectedYear" style="width: 120px">
        <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
      </el-select>
      <el-select v-model="selectedWeek" placeholder="选择导入周" clearable style="width: 200px">
        <el-option v-for="w in weekOptions" :key="w" :label="w" :value="w" />
      </el-select>
      <el-button type="primary" @click="exportToExcel">
        <el-icon><Download /></el-icon>导出Excel
      </el-button>
      <el-button type="danger" plain @click="handleDeleteWeek">
        <el-icon><Delete /></el-icon>删除本周数据
      </el-button>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card primary">
        <div class="kpi-label">本年总开户数</div>
        <div class="kpi-value">{{ stats.total }}户</div>
        <div class="kpi-change">数据截至：{{ stats.lastUpdate }}</div>
      </div>
      <div class="kpi-card secondary">
        <div class="kpi-label">本周新开户</div>
        <div class="kpi-value">{{ stats.thisWeek }}户</div>
        <div class="kpi-change">{{ weekRangeText }}</div>
      </div>
      <div class="kpi-card accent">
        <div class="kpi-label">本月新开户</div>
        <div class="kpi-value">{{ stats.thisMonth }}户</div>
        <div class="kpi-change">{{ monthRangeText }}</div>
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

    <!-- 各营业部开户统计 -->
    <div class="table-container" style="margin-top: 20px;">
      <div class="section-title">各营业部本周开户统计</div>
      <el-table :data="groupStats" stripe v-loading="loading" max-height="400" style="width: 100%">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="group_name" label="营业部" min-width="120" />
        <el-table-column prop="thisWeekCount" label="本周开户数" align="center" width="120">
          <template #default="{ row }">
            <strong>{{ row.thisWeekCount }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="prevWeekCount" label="上周开户数" align="center" width="120" />
        <el-table-column label="周度增量" align="center" width="120">
          <template #default="{ row }">
            <span :class="getChangeClass(row.weekChange)">
              {{ row.weekChange >= 0 ? '+' : '' }}{{ row.weekChange }}户
            </span>
          </template>
        </el-table-column>
        <el-table-column label="占全公司" align="center" width="120">
          <template #default="{ row }">
            {{ row.percentage }}%
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 员工排名 + 开户明细 -->
    <div class="tables-grid" style="margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div class="table-container">
        <div class="section-title">员工本年度开户排名</div>
        <el-table :data="memberRanking" stripe v-loading="loading" max-height="500" style="width: 100%">
          <el-table-column type="index" label="排名" width="60" align="center" />
          <el-table-column prop="member_name" label="员工姓名" min-width="120" />
          <el-table-column prop="group_name" label="所属营业部" min-width="120" />
          <el-table-column prop="count" label="开户数量" align="center" width="100">
            <template #default="{ row }">
              <strong>{{ row.count }}户</strong>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="table-container">
        <div class="section-title">近期开户明细</div>
        <el-table :data="accountList" stripe v-loading="loading" max-height="500" style="width: 100%">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="account_date" label="开户日期" width="120" />
          <el-table-column prop="member_name" label="所属员工" width="120" />
          <el-table-column prop="group_name" label="营业部" width="120" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import { marginTradingApi } from '../../api/marginTrading.js'

const accountList = ref([])
const loading = ref(false)
const selectedYear = ref(new Date().getFullYear())
const selectedWeek = ref('')

// 营业部固定排序顺序
const GROUP_ORDER = { '上一': 1, '上二': 2, '上三': 3, '上四': 4, '上五': 5, '上六': 6, '上海分公司': 7 }

const weekOptions = computed(() => {
  const weeks = new Set(accountList.value.map(a => a.record_week))
  return Array.from(weeks).sort().reverse()
})

const weeklyChart = ref(null)
const monthlyChart = ref(null)
let weeklyInstance = null
let monthlyInstance = null

const yearOptions = computed(() => {
  const current = new Date().getFullYear()
  return [current, current - 1]
})

// 获取日期所在周的范围（周一至周日）
const getWeekRange = (date) => {
  const d = new Date(date)
  const day = d.getDay() || 7 // 1=周一, ..., 7=周日
  const monday = new Date(d)
  monday.setDate(d.getDate() - day + 1)
  monday.setHours(0, 0, 0, 0)
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  sunday.setHours(23, 59, 59, 999)
  return { start: monday, end: sunday }
}

// 获取日期所在周的 ISO 格式键
const getWeekKey = (dateStr) => {
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const oneJan = new Date(year, 0, 1)
  const dayOfYear = Math.floor((d - oneJan) / 86400000) + 1
  const weekNum = Math.ceil((dayOfYear + oneJan.getDay()) / 7)
  return `${year}-W${String(weekNum).padStart(2, '0')}`
}

// 获取数据中最新的日期
const latestDate = computed(() => {
  const dates = accountList.value.map(a => new Date(a.account_date))
  return dates.length > 0 ? new Date(Math.max(...dates)) : null
})

const stats = computed(() => {
  const total = accountList.value.length

  if (!latestDate.value) {
    return { total: 0, thisWeek: 0, thisMonth: 0, lastUpdate: '-' }
  }

  // 本周范围基于数据最新日期（周一至周日）
  const { start: weekStart, end: weekEnd } = getWeekRange(latestDate.value)

  // 本月范围基于数据最新日期
  const latestYear = latestDate.value.getFullYear()
  const latestMonth = latestDate.value.getMonth()
  const monthStart = new Date(latestYear, latestMonth, 1)
  const monthEnd = new Date(latestYear, latestMonth + 1, 0)
  monthEnd.setHours(23, 59, 59, 999)

  const thisWeek = accountList.value.filter(a => {
    const d = new Date(a.account_date)
    return d >= weekStart && d <= weekEnd
  }).length

  const thisMonth = accountList.value.filter(a => {
    const d = new Date(a.account_date)
    return d >= monthStart && d <= monthEnd
  }).length

  const lastUpdate = latestDate.value.toLocaleDateString('zh-CN')

  return {
    total,
    thisWeek,
    thisMonth,
    lastUpdate
  }
})

const weekRangeText = computed(() => {
  if (!latestDate.value) return '-'
  const { start, end } = getWeekRange(latestDate.value)
  const fmt = (d) => `${d.getMonth() + 1}月${d.getDate()}日`
  return `${fmt(start)} - ${fmt(end)}`
})

const monthRangeText = computed(() => {
  if (!latestDate.value) return '-'
  return `${latestDate.value.getFullYear()}年${latestDate.value.getMonth() + 1}月`
})

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

  // Weekly trend - 按 account_date 的自然周分组
  const weeklyMap = {}
  accountList.value.forEach(a => {
    const weekKey = getWeekKey(a.account_date)
    if (!weeklyMap[weekKey]) weeklyMap[weekKey] = 0
    weeklyMap[weekKey]++
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

  // Monthly trend - 按 account_date 的月份分组
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

const memberRanking = computed(() => {
  const memberMap = {}
  accountList.value.forEach(a => {
    const key = `${a.member_name}-${a.group_name}`
    if (!memberMap[key]) {
      memberMap[key] = { member_name: a.member_name, group_name: a.group_name, count: 0 }
    }
    memberMap[key].count++
  })
  return Object.values(memberMap).sort((a, b) => b.count - a.count)
})

const groupStats = computed(() => {
  if (!latestDate.value) return []

  // 本周范围基于数据最新日期
  const { start: weekStart, end: weekEnd } = getWeekRange(latestDate.value)

  const prevWeekDate = new Date(weekStart)
  prevWeekDate.setDate(prevWeekDate.getDate() - 1)
  const { start: prevWeekStart, end: prevWeekEnd } = getWeekRange(prevWeekDate)

  const groupMap = {}
  accountList.value.forEach(a => {
    const g = a.group_name
    if (!groupMap[g]) {
      groupMap[g] = { group_name: g, thisWeekCount: 0, prevWeekCount: 0 }
    }
    const d = new Date(a.account_date)
    if (d >= weekStart && d <= weekEnd) {
      groupMap[g].thisWeekCount++
    }
    if (d >= prevWeekStart && d <= prevWeekEnd) {
      groupMap[g].prevWeekCount++
    }
  })

  const totalThisWeek = Object.values(groupMap).reduce((sum, g) => sum + g.thisWeekCount, 0)

  const result = Object.values(groupMap).map(g => ({
    ...g,
    weekChange: g.thisWeekCount - g.prevWeekCount,
    percentage: totalThisWeek > 0 ? ((g.thisWeekCount / totalThisWeek) * 100).toFixed(1) : '0'
  }))

  // 按固定营业部顺序排序
  return result.sort((a, b) => {
    const orderA = GROUP_ORDER[a.group_name] || 99
    const orderB = GROUP_ORDER[b.group_name] || 99
    return orderA - orderB
  })
})

const getChangeClass = (val) => {
  if (val > 0) return 'change-up'
  if (val < 0) return 'change-down'
  return 'change-flat'
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return parseFloat(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const exportToExcel = () => {
  const exportData = accountList.value.map(row => ({
    '开户日期': row.account_date,
    '所属员工': row.member_name,
    '营业部': row.group_name
  }))
  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '新开户明细')
  XLSX.writeFile(wb, `两融新开户明细_${selectedYear.value}.xlsx`)
  ElMessage.success('导出成功')
}

const handleDeleteWeek = async () => {
  if (!selectedWeek.value) {
    ElMessage.warning('请先选择要删除的周')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除 ${selectedWeek.value} 的新开户数据吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await marginTradingApi.deleteNewAccounts(selectedWeek.value)
    ElMessage.success(`已删除 ${selectedWeek.value} 的数据`)
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
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
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
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
.change-up { color: #EF4444; font-weight: 500; }
.change-down { color: #10B981; font-weight: 500; }
.change-flat { color: #9CA3AF; font-weight: 500; }
@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
