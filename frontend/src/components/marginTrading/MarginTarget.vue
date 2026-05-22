<template>
  <div class="margin-target">
    <div class="annotation">
      两融业务考核管理：考核息费收入目标和开户数量目标，支持行内编辑和批量设置。
    </div>

    <div class="filter-bar">
      <el-select v-model="selectedYear" style="width: 120px">
        <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
      </el-select>
      <el-button type="primary" @click="showBatchDialog = true">
        <el-icon><Plus /></el-icon>批量设置指标
      </el-button>
    </div>

    <!-- Progress Charts -->
    <div class="progress-grid">
      <div class="progress-card">
        <div class="progress-card-title">息费收入考核完成率</div>
        <div v-for="row in targetData.slice(0, 6)" :key="row.group_id + '-income'" class="progress-row">
          <div class="progress-name">{{ row.group_name }}</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :class="getProgressClass(row.income_completion_rate)"
                 :style="{ width: Math.min(row.income_completion_rate || 0, 100) + '%' }" />
          </div>
          <div class="progress-value" :class="getProgressClass(row.income_completion_rate)">
            {{ row.income_completion_rate || 0 }}%
          </div>
        </div>
      </div>
      <div class="progress-card">
        <div class="progress-card-title">开户数量考核完成率</div>
        <div v-for="row in targetData.slice(0, 6)" :key="row.group_id + '-account'" class="progress-row">
          <div class="progress-name">{{ row.group_name }}</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :class="getProgressClass(row.account_completion_rate)"
                 :style="{ width: Math.min(row.account_completion_rate || 0, 100) + '%' }" />
          </div>
          <div class="progress-value" :class="getProgressClass(row.account_completion_rate)">
            {{ row.account_completion_rate || 0 }}%
          </div>
        </div>
      </div>
    </div>

    <!-- Target Table -->
    <div class="table-container" style="margin-top: 20px;">
      <el-table :data="targetData" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="group_name" label="营业部" min-width="120" />
        <el-table-column label="息费收入目标(万)" align="right" width="150">
          <template #default="{ row }">
            <el-input-number v-if="editingRow === row.group_id" v-model="editForm.income_target"
                             :min="0" :precision="2" size="small" style="width: 130px" />
            <span v-else>{{ row.income_target?.toFixed(2) || '0.00' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="息费收入实际(万)" align="right" width="150">
          <template #default="{ row }">
            {{ row.income_actual?.toFixed(2) || '0.00' }}
          </template>
        </el-table-column>
        <el-table-column label="收入完成率" align="center" width="120">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.income_completion_rate)" size="small">
              {{ row.income_completion_rate || 0 }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开户目标(户)" align="right" width="120">
          <template #default="{ row }">
            <el-input-number v-if="editingRow === row.group_id" v-model="editForm.account_target"
                             :min="0" size="small" style="width: 100px" />
            <span v-else>{{ row.account_target || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="开户实际(户)" align="right" width="120">
          <template #default="{ row }">
            {{ row.account_actual || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="开户完成率" align="center" width="120">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.account_completion_rate)" size="small">
              {{ row.account_completion_rate || 0 }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="120">
          <template #default="{ row }">
            <div v-if="editingRow === row.group_id">
              <el-button type="primary" link size="small" @click="saveEdit(row)">保存</el-button>
              <el-button link size="small" @click="cancelEdit">取消</el-button>
            </div>
            <div v-else>
              <el-button type="primary" link size="small" @click="startEdit(row)">编辑</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Batch Dialog -->
    <el-dialog v-model="showBatchDialog" title="批量设置考核指标" width="500px">
      <el-form label-width="140px">
        <el-form-item label="营业部">
          <el-select v-model="batchForm.group_id" placeholder="选择营业部" style="width: 100%">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <div class="form-tip">不选择则设置所有营业部</div>
        </el-form-item>
        <el-form-item label="息费收入目标(万)">
          <el-input-number v-model="batchForm.income_target" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开户数量目标(户)">
          <el-input-number v-model="batchForm.account_target" :min="0" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="saveBatch">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { marginTradingApi } from '../../api/marginTrading.js'
import { groupsApi } from '../../api/index.js'

const selectedYear = ref(new Date().getFullYear())
const yearOptions = computed(() => {
  const current = new Date().getFullYear()
  return [current, current + 1]
})

const groups = ref([])
const targetData = ref([])
const loading = ref(false)
const editingRow = ref(null)
const editForm = ref({ income_target: 0, account_target: 0 })
const showBatchDialog = ref(false)
const batchForm = ref({ group_id: null, income_target: 0, account_target: 0 })

const fetchGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchTargets = async () => {
  loading.value = true
  try {
    const res = await marginTradingApi.getTargets({ year: selectedYear.value })
    targetData.value = res || []
  } catch (error) {
    console.error('Failed to fetch targets:', error)
    ElMessage.error('获取考核指标失败')
  } finally {
    loading.value = false
  }
}

const startEdit = (row) => {
  editingRow.value = row.group_id
  editForm.value = {
    income_target: row.income_target || 0,
    account_target: row.account_target || 0
  }
}

const cancelEdit = () => {
  editingRow.value = null
}

const saveEdit = async (row) => {
  try {
    await marginTradingApi.saveTarget({
      group_id: row.group_id,
      year: selectedYear.value,
      income_target: editForm.value.income_target,
      account_target: editForm.value.account_target
    })
    ElMessage.success('保存成功')
    editingRow.value = null
    fetchTargets()
  } catch (error) {
    console.error('Save error:', error)
    ElMessage.error('保存失败')
  }
}

const saveBatch = async () => {
  try {
    const groupsToUpdate = batchForm.value.group_id
      ? groups.value.filter(g => g.id === batchForm.value.group_id)
      : groups.value

    for (const group of groupsToUpdate) {
      await marginTradingApi.saveTarget({
        group_id: group.id,
        year: selectedYear.value,
        income_target: batchForm.value.income_target,
        account_target: batchForm.value.account_target
      })
    }
    ElMessage.success('批量设置成功')
    showBatchDialog.value = false
    fetchTargets()
  } catch (error) {
    console.error('Batch save error:', error)
    ElMessage.error('保存失败')
  }
}

const getProgressClass = (rate) => {
  if (rate >= 100) return 'success'
  if (rate >= 50) return 'warning'
  return 'danger'
}

const getTagType = (rate) => {
  if (rate >= 100) return 'success'
  if (rate >= 50) return 'warning'
  return 'danger'
}

watch(selectedYear, () => {
  fetchTargets()
})

onMounted(() => {
  fetchGroups()
  fetchTargets()
})
</script>

<style scoped>
.margin-target { padding: 0; }
.annotation {
  background: #FFF7ED; border-left: 3px solid #EA580C;
  padding: 12px 16px; border-radius: 0 8px 8px 0;
  margin-bottom: 20px; font-size: 13px; color: #9A3412;
}
.filter-bar {
  display: flex; gap: 12px; margin-bottom: 20px; align-items: center;
}
.progress-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
}
.progress-card {
  background: white; border-radius: 12px; padding: 20px;
  border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.progress-card-title {
  font-size: 14px; font-weight: 600; color: #374151;
  margin-bottom: 16px;
}
.progress-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid #F3F4F6;
}
.progress-row:last-child { border-bottom: none; }
.progress-name { width: 100px; font-size: 13px; color: #374151; flex-shrink: 0; }
.progress-bar-bg {
  flex: 1; height: 8px; background: #F3F4F6;
  border-radius: 4px; overflow: hidden;
}
.progress-bar-fill {
  height: 100%; border-radius: 4px; transition: width 0.3s ease;
}
.progress-bar-fill.success { background: #10B981; }
.progress-bar-fill.warning { background: #F59E0B; }
.progress-bar-fill.danger { background: #EF4444; }
.progress-value { width: 50px; text-align: right; font-size: 12px; font-weight: 600; }
.progress-value.success { color: #10B981; }
.progress-value.warning { color: #F59E0B; }
.progress-value.danger { color: #EF4444; }
.table-container {
  background: white; border-radius: 12px; border: 1px solid #E5E7EB; overflow: hidden;
}
.form-tip { font-size: 12px; color: #9CA3AF; margin-top: 4px; }
:deep(.el-button--primary) { background: #EA580C; border-color: #EA580C; }
@media (max-width: 900px) {
  .progress-grid { grid-template-columns: 1fr; }
}
</style>