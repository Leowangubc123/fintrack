# 投资顾问服务订阅跟踪功能设计文档

**创建日期:** 2024-04-15  
**功能名称:** 投顾服务 (Investment Advisory Service)  
**版本:** V4

---

## 1. 功能概述

在 FinTrack 系统中新增投资顾问服务订阅跟踪子功能，用于跟踪统计各营业部员工的投顾产品签约情况。

### 1.1 产品类型

| 类型 | 说明 |
|------|------|
| 千1 | 荐股服务，千分之一佣金 |
| 千3 | 荐股服务，千分之三佣金 |
| 万2 | 荐股服务，万分之二佣金 |
| 网格 | 网格交易工具 |
| 量化T | 量化T策略工具 |
| GWT | GWT签约服务 |

### 1.2 数据维度

- **签约户数**: 按员工+产品统计，可重复计算
- **签约资产**: 各产品独立计算，简单加总
- **投顾收入**: 签约时记录的收入金额
- **折算户数**: 根据资产规模折算后的户数（用于考核）

### 1.3 更新机制

采用**时点全量更新**机制：
- 每次导入数据时，根据"数据日期"全量替换该日期的所有记录
- 需要记录"最近更新日期"KPI
- 与私募保有数据更新逻辑一致

---

## 2. 页面设计

### 2.1 左侧菜单

```
投资顾问 (新增)
├── 年度看板
├── 签约明细
├── 数据导入
└── 考核管理
```

### 2.2 年度看板

**维度切换:** 全辖区 / 营业部 / 个人

**KPI卡片 (4个):**
1. 累计签约户数 - 较上次更新新增/减少
2. 累计签约资产 - 较上次更新新增/减少
3. 本年投顾收入 - 较上次更新新增/减少
4. 最近更新日期 - 显示上次更新日期

**图表区域:**
- 左: 各产品签约分布 (按顺序: 千1/千3/万2/网格/量化T/GWT)
- 右: 年度趋势分析 (双轴: 柱状图显示收入 + 折线图显示户数)

### 2.3 营业部视图

- 纵向列表展示各营业部
- 每行显示: 排名、营业部名称、签约摘要、收入完成率、户数完成率
- 点击展开: 各产品签约分布 (6宫格) + 最近签约明细
- 产品分布格子布局: 产品类型(上) / 签约户数(中,带单位) / 签约资产(下)

### 2.4 个人视图

- 筛选栏: 营业部 + 员工 + 产品类型
- 可排序表格:
  - 各产品签约户数列 (千1/千3/万2/网格/量化T/GWT)
  - 签约户数总计
  - 签约资产
  - 投顾收入
- 支持点击表头排序
- 导出Excel功能

### 2.5 数据导入

- 时点更新机制说明
- 字段说明: 营业部、员工姓名、签约日期、产品类型、签约资产(万)、投顾收入(元)
- 拖拽上传区域
- 支持 .xlsx, .xls 格式
- 显示上次导入记录

### 2.6 考核管理

**考核指标设置:**
- 收入目标 (万元)
- 户数目标
- 当前完成及完成率

**签约明细编辑:**
- 点击营业部查看明细
- 可编辑"折算户数"字段
- 支持折算规则说明标注
- 保存后更新考核完成率

---

## 3. 数据模型

### 3.1 数据库表

```sql
-- 投顾签约记录表
investment_advisory_subscriptions
- id: INT PK
- member_id: INT FK (营销人员)
- group_id: INT FK (营业部)
- product_type: ENUM ('千1', '千3', '万2', '网格', '量化T', 'GWT')
- subscription_date: DATE (签约日期)
- asset_amount: DECIMAL(15,2) (签约资产,万元)
- advisory_income: DECIMAL(15,2) (投顾收入,元)
- original_households: INT (原始户数,默认1)
- converted_households: INT (折算户数)
- conversion_note: VARCHAR(255) (折算说明)
- record_date: DATE (数据日期,用于时点更新)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

-- 营业部考核指标表
investment_advisory_targets
- id: INT PK
- group_id: INT FK (营业部)
- year: INT (年度)
- income_target: DECIMAL(15,2) (收入目标,万元)
- households_target: INT (户数目标)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

-- 数据导入记录表 (可选,复用现有import_logs)
```

### 3.2 API端点

```
GET  /api/advisory/stats                  # 获取统计数据
GET  /api/advisory/subscriptions          # 获取签约明细列表
POST /api/advisory/subscriptions/import   # 导入签约数据
PUT  /api/advisory/subscriptions/:id      # 更新单条记录(折算户数)
GET  /api/advisory/targets                # 获取考核指标
POST /api/advisory/targets                # 创建/更新考核指标
GET  /api/advisory/member-stats           # 获取个人统计数据
```

---

## 4. 技术实现

### 4.1 前端

- **路由:** /advisory
- **组件结构:**
  ```
  AdvisoryService.vue (主页面)
  ├── AdvisoryDashboard.vue (年度看板)
  │   ├── KPICards.vue
  │   ├── ProductDistribution.vue
  │   └── TrendChart.vue
  ├── AdvisoryGroupView.vue (营业部视图)
  ├── AdvisoryMemberView.vue (个人视图)
  ├── AdvisoryImport.vue (数据导入)
  └── AdvisoryTarget.vue (考核管理)
  ```

### 4.2 后端

- **路由文件:** backend/app/routers/advisory.py
- **模型文件:** backend/app/models/advisory.py
- **复用现有:** Member, Group 模型

### 4.3 样式

- 主色调: 青绿色 (#0891B2) - 与私募紫色区分
- 遵循现有 FinTrack UI 风格
- 白色卡片 + 圆角 + 阴影

---

## 5. 验收标准

- [ ] 左侧菜单新增"投顾服务"入口
- [ ] 年度看板三个维度切换正常
- [ ] KPI卡片显示正确,较上次更新变化清晰可见
- [ ] 产品分布按指定顺序展示
- [ ] 趋势图双轴显示,数据标签正确
- [ ] 营业部视图可展开收起,产品分布格子布局正确
- [ ] 个人视图支持排序和筛选
- [ ] 数据导入支持Excel上传,时点更新机制正确
- [ ] 考核管理支持指标设置和折算户数编辑
- [ ] 所有页面风格与现有系统一致
