# 私募销售考核管理功能设计文档

> 为私募销售模块新增考核管理子功能，支持管理人手动设置各营业部年度销量目标，并基于考核销量自动计算完成率和时间进度状态。

---

## 1. 需求概述

### 1.1 目标
- 在私募销售页面新增"考核管理"标签页。
- 考核指标仅有一项：**销量新增**（考核销量）。
- 统计维度：**各营业部**。
- 数据来源：本年 `transaction_type == 'sale'` 的 `PrivateFundTransaction.assessed_amount` 合计。
- 管理人可手动设置并修改各营业部销量目标。
- 自动计算完成率及是否超过时间进度。

### 1.2 时间进度与状态规则
- **时间进度**：当前已过天数 / 当年总天数（按自然日计算）。
- **完成率**：`current_assessed_sales / sales_target × 100%`。
- **状态阈值**（严格）：
  - **超前**：完成率 ≥ 时间进度 + 5%
  - **正常**：时间进度 - 5% < 完成率 < 时间进度 + 5%
  - **落后**：完成率 ≤ 时间进度 - 5%

---

## 2. 数据模型

### 2.1 新增模型：`PrivateFundTarget`

文件：`backend/app/models/private_fund.py`

```python
class PrivateFundTarget(Base):
    __tablename__ = "private_fund_targets"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    year = Column(Integer, nullable=False)
    sales_target = Column(Numeric(15, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

约束：`(group_id, year)` 唯一。

---

## 3. 后端 API 设计

所有 API 挂载到 `/api/private-fund` 下。

### 3.1 GET `/targets`

**参数：**
- `year` (int, optional)：默认当前年份。

**返回：**
```json
[
  {
    "id": 1,
    "group_id": 2,
    "group_name": "北京营业部",
    "year": 2026,
    "sales_target": 500.00,
    "current_sales": 320.50,
    "completion_rate": 64.10,
    "time_progress": 29.04,
    "status": "normal"
  }
]
```

**计算逻辑：**
1. 查询所有 `Group`。
2. 查询 `PrivateFundTarget` 中该年份的目标记录。
3. 统计本年（`transaction_date` 年份匹配）且 `transaction_type == 'sale'` 的 `assessed_amount` 按 `group_id` 汇总。
4. 计算完成率、时间进度、状态。

**状态计算（精确到小数）：**
```python
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
```

### 3.2 POST `/targets`

**请求体：**
```json
{
  "group_id": 2,
  "year": 2026,
  "sales_target": 500.00
}
```

**行为：**
- 若 `(group_id, year)` 已存在，则更新 `sales_target`。
- 若不存在，则创建新记录。
- 返回更新后的完整 `TargetResponse`（含计算后的完成率、时间进度、状态）。

### 3.3 Pydantic 模型

```python
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
    status: str  # "ahead", "normal", "behind"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PrivateFundTargetCreate(BaseModel):
    group_id: int
    year: int
    sales_target: float
```

---

## 4. 前端设计

### 4.1 路由与菜单

文件：`frontend/src/views/PrivateSecuritiesFund.vue`

在 `tabs` 数组中新增：
```javascript
{ key: 'assessment', label: '考核管理' }
```

引入组件：
```javascript
import AssessmentTarget from '../components/privateFund/AssessmentTarget.vue'
```

渲染条件：
```html
<AssessmentTarget v-if="activeTab === 'assessment'" />
```

### 4.2 组件：`AssessmentTarget.vue`

路径：`frontend/src/components/privateFund/AssessmentTarget.vue`

#### 布局结构
参考 `AdvisoryTarget.vue` 的 Apple-style 表格风格。

1. **顶部操作区**
   - 左侧：年份选择器（`el-select`，当前年 + 次年）。
   - 右侧：`批量设置指标` 按钮。

2. **考核指标表格**
   - 表头：序号 | 营业部 | 销量目标 | 当前考核销量 | 完成率 | 时间进度 | 状态 | 操作
   - 行内可编辑`销量目标`，点击保存/取消。
   - 完成率列展示彩色迷你进度条 + 百分比文字。
   - 状态列用 `el-tag` 展示：
     - 超前 → `el-tag type="success"`
     - 正常 → `el-tag type="info"`
     - 落后 → `el-tag type="danger"`

3. **批量设置弹窗**
   - `el-dialog`，500px 宽。
   - 表单字段：营业部（可选，不选则全部）、销量目标。
   - 点击保存后，逐个调用 API 或走批量接口。

#### API 封装

文件：`frontend/src/api/index.js`

在 `privateFundApi` 中新增：
```javascript
getTargets: (year) => api.get('/private-fund/targets', { params: { year } }),
saveTarget: (data) => api.post('/private-fund/targets', data),
```

---

## 5. 数据库迁移

无需 Alembic。在应用启动时通过自动迁移逻辑处理：

文件：`backend/app/main.py` 或现有表创建逻辑中。

检测 `private_fund_targets` 表是否存在，若不存在则自动创建。参考现有模式（如 `InvestmentAdvisoryTarget` 的迁移方式）。

新增 `PrivateFundTarget` 到 `backend/app/models/__init__.py` 的导出列表中。

---

## 6. 实现任务清单

1. 后端数据模型：`backend/app/models/private_fund.py` 新增 `PrivateFundTarget`。
2. 后端 API：`backend/app/routers/private_fund.py` 新增 `GET /targets` 和 `POST /targets`。
3. 后端导出：`backend/app/models/__init__.py` 注册模型。
4. 数据库表创建：在应用启动时自动创建 `private_fund_targets` 表。
5. 前端 API：`frontend/src/api/index.js` 的 `privateFundApi` 新增两个方法。
6. 前端组件：新建 `frontend/src/components/privateFund/AssessmentTarget.vue`。
7. 前端路由：`frontend/src/views/PrivateSecuritiesFund.vue` 新增标签页和组件引用。
8. 构建并推送。

---

## 7. 样式与交互规范

- 主色调：沿用私募销售现有紫色系 `#7C3AED`，但考核管理的进度条颜色参考投顾签约的完成率配色（绿/橙/红）。
- 表格行 hover 效果：`background: #F8FAFC`。
- 编辑态行背景：`#FFFBEB`。
- 响应式：900px 以下切换为卡片堆叠布局（参考 `AdvisoryTarget.vue` 的 `@media` 处理）。
