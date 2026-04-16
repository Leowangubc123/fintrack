# 私募销售考核管理功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为私募销售模块新增考核管理子功能，支持管理人设置各营业部年度销量目标，并自动计算完成率与时间进度状态。

**Architecture:** 新增 `PrivateFundTarget` 数据模型存储营业部年度销量目标；后端提供 `GET/POST /api/private-fund/targets` API 完成目标 CRUD 与实时完成率计算；前端新建 `AssessmentTarget.vue` 组件，以 Apple-style 表格展示各营业部考核数据，支持行内编辑与批量设置。

**Tech Stack:** FastAPI + SQLAlchemy + SQLite/PostgreSQL, Vue 3 + Element Plus

---

## 文件结构

- `backend/app/models/private_fund.py` — 新增 `PrivateFundTarget` 模型
- `backend/app/models/__init__.py` — 导出新增模型
- `backend/app/routers/private_fund.py` — 新增考核指标 API
- `backend/app/database.py` 或 `backend/app/main.py` — 自动创建缺失的数据库表
- `frontend/src/api/index.js` — 前端 API 封装
- `frontend/src/components/privateFund/AssessmentTarget.vue` — 新建考核管理组件
- `frontend/src/views/PrivateSecuritiesFund.vue` — 新增标签页与组件引用

---

### Task 1: 新增后端数据模型 PrivateFundTarget

**Files:**
- Modify: `backend/app/models/private_fund.py`

- [ ] **Step 1: 在 PrivateFundHolding 之后添加 PrivateFundTarget 模型**

在 `backend/app/models/private_fund.py` 的 `PrivateFundHolding` 类之后，追加以下内容：

```python
class PrivateFundTarget(Base):
    """私募销售考核目标模型"""
    __tablename__ = "private_fund_targets"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    year = Column(Integer, nullable=False)
    sales_target = Column(Numeric(15, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/private_fund.py
git commit -m "feat(private_fund): add PrivateFundTarget model"
```

---

### Task 2: 导出 PrivateFundTarget 模型

**Files:**
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 导入并导出 PrivateFundTarget**

修改 `backend/app/models/__init__.py`：

```python
from app.models.private_fund import PrivateFundProduct, PrivateFundTransaction, PrivateFundHolding, PrivateFundTarget
```

```python
__all__ = ["User", "Group", "Member", "Product", "ProductTarget", "SalesRecord", "ImportLog",
           "PrivateFundProduct", "PrivateFundTransaction", "PrivateFundHolding", "PrivateFundTarget",
           "InvestmentAdvisorySubscription", "InvestmentAdvisoryTarget", "AdvisoryImportLog"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/__init__.py
git commit -m "feat(models): export PrivateFundTarget"
```

---

### Task 3: 自动创建 private_fund_targets 数据库表

**Files:**
- Modify: `backend/app/database.py`

- [ ] **Step 1: 读取 database.py 确认现有表创建逻辑**

使用 Read 工具读取 `backend/app/database.py`，找到 `Base.metadata.create_all(bind=engine)` 的调用位置。

- [ ] **Step 2: 确认或补充 create_all 调用**

如果 `database.py` 中已有 `Base.metadata.create_all(bind=engine)`（通常在 `get_db` 之外的全局作用域或初始化函数中），则无需修改，SQLAlchemy 会自动在应用启动时创建新表。

如果 `database.py` 中没有该调用，添加：

```python
Base.metadata.create_all(bind=engine)
```

到文件末尾（在 `engine` 和 `Base` 定义之后）。

- [ ] **Step 3: Commit（如有修改）**

```bash
git add backend/app/database.py
git commit -m "chore(database): ensure all tables are created on startup"
```

---

### Task 4: 后端 API — GET /api/private-fund/targets

**Files:**
- Modify: `backend/app/routers/private_fund.py`

- [ ] **Step 1: 在文件末尾添加 Pydantic 响应模型和 GET 接口**

在 `backend/app/routers/private_fund.py` 的最末尾（即所有已有路由之后），添加以下内容：

```python
import calendar
from app.models import PrivateFundTarget

class PrivateFundTargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    group_name: str
    year: int
    sales_target: float
    current_sales: float
    completion_rate: float
    time_progress: float
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PrivateFundTargetCreate(BaseModel):
    group_id: int
    year: int
    sales_target: float


@router.get("/targets", response_model=List[PrivateFundTargetResponse])
def get_private_fund_targets(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取私募销售考核指标及完成情况"""
    if not year:
        year = date.today().year

    # 获取所有营业部
    groups = db.query(Group).all()

    # 获取目标数据
    targets = db.query(PrivateFundTarget).filter(PrivateFundTarget.year == year).all()
    target_map = {t.group_id: t for t in targets}

    # 统计本年各营业部考核销量（assessed_amount）
    actual_stats = db.query(
        Member.group_id,
        func.sum(PrivateFundTransaction.assessed_amount).label("total_sales")
    ).join(
        PrivateFundTransaction, Member.id == PrivateFundTransaction.member_id
    ).filter(
        extract('year', PrivateFundTransaction.transaction_date) == year,
        PrivateFundTransaction.transaction_type == 'sale'
    ).group_by(Member.group_id).all()

    actual_map = {s.group_id: float(s.total_sales) if s.total_sales else 0 for s in actual_stats}

    # 计算时间进度
    today = date.today()
    day_of_year = today.timetuple().tm_yday
    total_days = 366 if calendar.isleap(today.year) else 365
    time_progress = round(day_of_year / total_days * 100, 2)

    result = []
    for group in groups:
        target = target_map.get(group.id)
        current_sales = actual_map.get(group.id, 0)
        sales_target = float(target.sales_target) if target else 0

        completion_rate = (current_sales / sales_target * 100) if sales_target > 0 else 0

        diff = completion_rate - time_progress
        if diff >= 5:
            status = "ahead"
        elif diff <= -5:
            status = "behind"
        else:
            status = "normal"

        result.append(PrivateFundTargetResponse(
            id=target.id if target else 0,
            group_id=group.id,
            group_name=group.name,
            year=year,
            sales_target=round(sales_target, 2),
            current_sales=round(current_sales, 2),
            completion_rate=round(completion_rate, 2),
            time_progress=time_progress,
            status=status,
            created_at=target.created_at if target else None,
            updated_at=target.updated_at if target else None
        ))

    return result
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/private_fund.py
git commit -m "feat(api): add GET /private-fund/targets endpoint"
```

---

### Task 5: 后端 API — POST /api/private-fund/targets

**Files:**
- Modify: `backend/app/routers/private_fund.py`

- [ ] **Step 1: 在 GET /targets 之后添加 POST /targets**

在同一个文件的 `get_private_fund_targets` 函数之后，追加：

```python
@router.post("/targets", response_model=PrivateFundTargetResponse)
def create_or_update_private_fund_target(
    request: PrivateFundTargetCreate,
    db: Session = Depends(get_db)
):
    """设置私募销售考核指标（创建或更新）"""
    group = db.query(Group).filter(Group.id == request.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="营业部不存在")

    target = db.query(PrivateFundTarget).filter(
        PrivateFundTarget.group_id == request.group_id,
        PrivateFundTarget.year == request.year
    ).first()

    if target:
        target.sales_target = Decimal(str(request.sales_target))
    else:
        target = PrivateFundTarget(
            group_id=request.group_id,
            year=request.year,
            sales_target=Decimal(str(request.sales_target))
        )
        db.add(target)

    db.commit()
    db.refresh(target)

    # 重新计算当前完成情况
    actual_stats = db.query(
        func.sum(PrivateFundTransaction.assessed_amount).label("total_sales")
    ).join(
        Member, Member.id == PrivateFundTransaction.member_id
    ).filter(
        Member.group_id == request.group_id,
        extract('year', PrivateFundTransaction.transaction_date) == request.year,
        PrivateFundTransaction.transaction_type == 'sale'
    ).first()

    current_sales = float(actual_stats.total_sales) if actual_stats.total_sales else 0
    completion_rate = (current_sales / request.sales_target * 100) if request.sales_target > 0 else 0

    today = date.today()
    day_of_year = today.timetuple().tm_yday
    total_days = 366 if calendar.isleap(today.year) else 365
    time_progress = round(day_of_year / total_days * 100, 2)

    diff = completion_rate - time_progress
    if diff >= 5:
        status = "ahead"
    elif diff <= -5:
        status = "behind"
    else:
        status = "normal"

    return PrivateFundTargetResponse(
        id=target.id,
        group_id=target.group_id,
        group_name=group.name,
        year=target.year,
        sales_target=request.sales_target,
        current_sales=round(current_sales, 2),
        completion_rate=round(completion_rate, 2),
        time_progress=time_progress,
        status=status,
        created_at=target.created_at,
        updated_at=target.updated_at
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/private_fund.py
git commit -m "feat(api): add POST /private-fund/targets endpoint"
```

---

### Task 6: 前端 API 封装

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 在 privateFundApi 中新增两个方法**

在 `frontend/src/api/index.js` 的 `privateFundApi` 对象中，在 `getHoldingDates` 之后添加：

```javascript
  // 考核指标
  getTargets: (year) => api.get('/private-fund/targets', { params: { year } }),
  saveTarget: (data) => api.post('/private-fund/targets', data),
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat(api): add private fund target APIs"
```

---

### Task 7: 前端组件 AssessmentTarget.vue

**Files:**
- Create: `frontend/src/components/privateFund/AssessmentTarget.vue`

- [ ] **Step 1: 创建组件文件并写入完整代码**

创建 `frontend/src/components/privateFund/AssessmentTarget.vue`，内容如下：

```vue
<template>
  <div class="assessment-target">
    <!-- Header -->
    <div class="view-header">
      <el-select v-model="selectedYear" style="width: 120px">
        <el-option v-for="year in years" :key="year" :label="year + '年'" :value="year" />
      </el-select>
      <el-button type="primary" @click="showBatchDialog = true">
        <el-icon><Plus /></el-icon>批量设置指标
      </el-button>
    </div>

    <!-- Targets Table -->
    <div class="targets-card">
      <div class="card-title">营业部考核指标</div>
      <div class="custom-table">
        <div class="table-head">
          <div class="th" style="width: 50px">序号</div>
          <div class="th" style="flex: 1">营业部</div>
          <div class="th" style="width: 120px" align="right">销量目标</div>
          <div class="th" style="width: 120px" align="right">当前考核销量</div>
          <div class="th" style="width: 100px" align="right">完成率</div>
          <div class="th" style="width: 100px" align="right">时间进度</div>
          <div class="th" style="width: 80px" align="center">状态</div>
          <div class="th" style="width: 100px" align="center">操作</div>
        </div>
        <div
          v-for="(row, index) in tableData"
          :key="row.group_id"
          class="table-body-row"
          :class="{ editing: editingRow === row.group_id }"
        >
          <div class="td" style="width: 50px" data-label="序号">{{ index + 1 }}</div>
          <div class="td" style="flex: 1" data-label="营业部">
            <span class="group-name">{{ row.group_name }}</span>
          </div>
          <div class="td" style="width: 120px" align="right" data-label="销量目标">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.sales_target" :min="0" :precision="2" size="small" style="width: 110px" />
            </div>
            <span v-else>{{ row.sales_target?.toFixed(2) || '0.00' }}万</span>
          </div>
          <div class="td" style="width: 120px" align="right" data-label="当前考核销量">{{ row.current_sales?.toFixed(2) || '0.00' }}万</div>
          <div class="td" style="width: 100px" align="right" data-label="完成率">
            <div class="rate-cell">
              <div class="rate-bar-bg">
                <div
                  class="rate-bar-fill"
                  :class="getProgressClass(row.completion_rate)"
                  :style="{ width: Math.min(row.completion_rate || 0, 100) + '%' }"
                />
              </div>
              <span class="rate-text" :class="getProgressClass(row.completion_rate)">
                {{ row.completion_rate || 0 }}%
              </span>
            </div>
          </div>
          <div class="td" style="width: 100px" align="right" data-label="时间进度">{{ row.time_progress }}%</div>
          <div class="td" style="width: 80px" align="center" data-label="状态">
            <el-tag :type="getStatusTagType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
          </div>
          <div class="td" style="width: 100px" align="center" data-label="操作" @click.stop>
            <div v-if="editingRow === row.group_id">
              <el-button type="primary" link size="small" @click="saveEdit(row)">保存</el-button>
              <el-button link size="small" @click="cancelEdit">取消</el-button>
            </div>
            <div v-else>
              <el-button type="primary" link size="small" @click="startEdit(row)">编辑</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Batch Set Targets Dialog -->
    <el-dialog v-model="showBatchDialog" title="批量设置考核指标" width="500px">
      <el-form label-width="100px">
        <el-form-item label="营业部">
          <el-select v-model="batchForm.group_id" placeholder="选择营业部" style="width: 100%">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <div class="form-tip">不选择则设置所有营业部</div>
        </el-form-item>
        <el-form-item label="销量目标">
          <el-input-number v-model="batchForm.sales_target" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="saveBatchTargets">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { privateFundApi } from '../../api/index.js'
import { groupsApi } from '../../api/index.js'

const selectedYear = ref(new Date().getFullYear())
const years = computed(() => {
  const current = new Date().getFullYear()
  return [current, current + 1]
})

const groups = ref([])
const targets = ref([])

const editingRow = ref(null)
const editForm = ref({
  sales_target: 0
})

const showBatchDialog = ref(false)
const batchForm = ref({
  group_id: null,
  sales_target: 0
})

const fetchGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchTargets = async () => {
  try {
    const res = await privateFundApi.getTargets(selectedYear.value)
    targets.value = res || []
  } catch (error) {
    console.error('Failed to fetch targets:', error)
    ElMessage.error('获取考核数据失败')
  }
}

const tableData = computed(() => {
  return targets.value.sort((a, b) => b.current_sales - a.current_sales)
})

const startEdit = (row) => {
  editingRow.value = row.group_id
  editForm.value = {
    sales_target: row.sales_target
  }
}

const cancelEdit = () => {
  editingRow.value = null
}

const saveEdit = async (row) => {
  try {
    await privateFundApi.saveTarget({
      group_id: row.group_id,
      year: selectedYear.value,
      sales_target: editForm.value.sales_target
    })
    ElMessage.success('保存成功')
    editingRow.value = null
    fetchTargets()
  } catch (error) {
    console.error('Save error:', error)
    ElMessage.error('保存失败')
  }
}

const saveBatchTargets = async () => {
  try {
    if (batchForm.value.group_id) {
      await privateFundApi.saveTarget({
        group_id: batchForm.value.group_id,
        year: selectedYear.value,
        sales_target: batchForm.value.sales_target
      })
    } else {
      for (const group of groups.value) {
        await privateFundApi.saveTarget({
          group_id: group.id,
          year: selectedYear.value,
          sales_target: batchForm.value.sales_target
        })
      }
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

const getStatusTagType = (status) => {
  if (status === 'ahead') return 'success'
  if (status === 'behind') return 'danger'
  return 'info'
}

const getStatusLabel = (status) => {
  if (status === 'ahead') return '超前'
  if (status === 'behind') return '落后'
  return '正常'
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
.assessment-target {
  padding: 0;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.targets-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  padding: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

.custom-table {
  width: 100%;
}

.table-head {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: #F9FAFB;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #6B7280;
  margin-bottom: 6px;
}

.table-body-row {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.table-body-row:hover {
  background: #F8FAFC;
}

.table-body-row.editing {
  background: #FFFBEB;
}

.th,
.td {
  padding: 0 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.th:first-child,
.td:first-child {
  padding-left: 0;
}

.th:last-child,
.td:last-child {
  padding-right: 0;
}

.group-name {
  font-weight: 500;
}

.edit-field {
  display: flex;
  justify-content: flex-end;
}

.rate-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rate-bar-bg {
  flex: 1;
  height: 6px;
  background: #F3F4F6;
  border-radius: 3px;
  overflow: hidden;
  min-width: 40px;
}

.rate-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.rate-bar-fill.success {
  background: #10B981;
}

.rate-bar-fill.warning {
  background: #F59E0B;
}

.rate-bar-fill.danger {
  background: #EF4444;
}

.rate-text {
  font-size: 13px;
  font-weight: 600;
  min-width: 44px;
  text-align: right;
}

.rate-text.success {
  color: #10B981;
}

.rate-text.warning {
  color: #F59E0B;
}

.rate-text.danger {
  color: #EF4444;
}

.form-tip {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 4px;
}

:deep(.el-dialog__header) {
  font-weight: 600;
}

@media (max-width: 900px) {
  .table-head {
    display: none;
  }

  .table-body-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 16px;
    margin-bottom: 8px;
    border: 1px solid #F3F4F6;
  }

  .td {
    width: 100% !important;
    padding: 0;
    display: flex;
    justify-content: space-between;
  }

  .td::before {
    content: attr(data-label);
    font-weight: 500;
    color: #6B7280;
    font-size: 13px;
  }

  .rate-cell {
    width: 100%;
  }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/privateFund/AssessmentTarget.vue
git commit -m "feat(frontend): add AssessmentTarget component for private fund"
```

---

### Task 8: 在 PrivateSecuritiesFund.vue 中新增标签页

**Files:**
- Modify: `frontend/src/views/PrivateSecuritiesFund.vue`

- [ ] **Step 1: 引入组件并添加到 tabs**

修改 `frontend/src/views/PrivateSecuritiesFund.vue`：

在 `<script setup>` 的 import 区域添加：

```javascript
import AssessmentTarget from '../components/privateFund/AssessmentTarget.vue'
```

在 `tabs` 数组中添加：

```javascript
{ key: 'assessment', label: '考核管理' }
```

推荐放在 `entry` 之后或 `stats` 之后。建议顺序：

```javascript
const tabs = [
  { key: 'stats', label: '年度看板' },
  { key: 'holding', label: '保有统计' },
  { key: 'assessment', label: '考核管理' },
  { key: 'entry', label: '销售录入' },
  { key: 'products', label: '产品库' }
]
```

在 `<template>` 中添加渲染条件：

```html
<!-- 考核管理 -->
<AssessmentTarget v-if="activeTab === 'assessment'" />
```

放在 `AnnualDashboard` 之后即可。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/PrivateSecuritiesFund.vue
git commit -m "feat(frontend): add assessment tab to private fund page"
```

---

### Task 9: 构建前端并验证

**Files:**
- None (build step)

- [ ] **Step 1: 运行前端构建**

```bash
cd /Users/leowang/FinTrack/frontend
npm run build
```

Expected: build succeeds with no new errors.

- [ ] **Step 2: Commit dist changes**

```bash
git add frontend/dist/
git commit -m "chore(build): rebuild frontend dist for private fund assessment"
```

---

### Task 10: 推送到 GitHub

**Files:**
- None

- [ ] **Step 1: 推送**

```bash
cd /Users/leowang/FinTrack
git push origin main
```

- [ ] **Step 2: 若推送失败（网络问题），尝试重试**

```bash
git push origin main
```

---

## Spec Self-Review Checklist

1. **Spec coverage:**
   - 数据模型 ✅ Task 1
   - 后端 GET API ✅ Task 4
   - 后端 POST API ✅ Task 5
   - 前端组件 ✅ Task 7
   - 标签页集成 ✅ Task 8
   - 构建推送 ✅ Task 9-10

2. **Placeholder scan:** 无 TBD/TODO/"implement later"。

3. **Type consistency：**
   - 后端 `sales_target` 统一用 `Numeric(15, 2)` / `float`。
   - 前端 `el-input-number` 统一设置 `:precision="2"`。
   - API 路径统一为 `/private-fund/targets`。

4. **Ambiguity check：** 完成率计算明确为 `assessed_amount` 合计；状态阈值明确为 ±5%。
