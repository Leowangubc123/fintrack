# 私募销售数据流验证文档

## 数据模型分离说明

### 普通产品销售 (SalesRecord)
- **用途**: 普通基金/产品销售记录
- **关联表**: `products` (普通产品表)
- **数据字段**: product_id, member_id, group_id, amount, sale_date

### 私募产品销售 (PrivateFundTransaction)
- **用途**: 私募产品交易记录（销售/赎回）
- **关联表**: `private_fund_products` (私募产品表)
- **数据字段**: product_id, member_id, amount, transaction_date, transaction_type, sales_coefficient, assessed_amount, holding_coefficient

---

## 数据流架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端界面层                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ 产品库管理    │  │ 销售录入      │  │ 业绩统计/保有统计     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API路由层                                 │
├─────────────────────────────────────────────────────────────────┤
│  /api/private-fund/products      GET/POST/PUT/DELETE            │
│  /api/private-fund/transactions  POST                           │
│  /api/private-fund/stats/annual  GET                            │
│  /api/private-fund/sales/annual  GET                            │
│  /api/private-fund/holdings/*    GET                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据库模型层                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │ private_fund_products│    │ private_fund_transactions    │  │
│  │ - id                 │    │ - id                         │  │
│  │ - name               │    │ - product_id (FK)            │  │
│  │ - code               │    │ - member_id (FK)             │  │
│  │ - sales_coefficient  │    │ - amount                     │  │
│  │ - holding_coefficient│    │ - transaction_type (sale/redeem)│
│  │ - ...                │    │ - sales_coefficient          │  │
│  └──────────────────────┘    │ - assessed_amount            │  │
│                              │ - holding_coefficient        │  │
│                              └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API数据流详细说明

### 1. 录入销售/赎回

**前端** → 填写表单 → 调用 `POST /api/private-fund/transactions`

**请求体**:
```json
{
  "product_id": 1,
  "member_id": 5,
  "transaction_date": "2026-03-29",
  "amount": 100,
  "transaction_type": "sale",  // 或 "redeem"
  "remark": ""
}
```

**后端处理** ([private_fund.py:217](backend/app/routers/private_fund.py:217)):
1. 验证产品存在
2. 验证销售人员存在
3. 如果是销售类型，自动计算:
   - `sales_coefficient` = 产品的销售系数
   - `assessed_amount` = amount × sales_coefficient
4. 保存到 `private_fund_transactions` 表
5. 记录 `holding_coefficient` 用于后续保有计算

**响应**:
```json
{
  "id": 123,
  "product_id": 1,
  "product_name": "赫富城盈500指数增强二号A类",
  "member_name": "张三",
  "group_name": "营业部A",
  "amount": 100,
  "transaction_type": "sale",
  "sales_coefficient": 2.0,
  "assessed_amount": 200,
  "holding_coefficient": 1.0
}
```

---

### 2. 年度看板统计

**前端** → 页面加载 → 调用:
- `GET /api/private-fund/stats/annual?year=2026`
- `GET /api/private-fund/sales/annual?year=2026`

**后端处理 - 年度统计** ([private_fund.py:310](backend/app/routers/private_fund.py:310)):
```python
# 统计逻辑
for t in transactions:
    if t.transaction_type == 'sale':
        total_actual_sales += t.amount
        total_assessed_sales += t.assessed_amount
    else:  # redeem
        total_redemption += t.amount
net_sales = total_actual_sales - total_redemption
```

**响应**:
```json
{
  "total_assessed_sales": 15000.00,
  "total_actual_sales": 8000.00,
  "total_redemption": 2000.00,
  "net_sales": 6000.00
}
```

**后端处理 - 年度销售明细** ([private_fund.py:339](backend/app/routers/private_fund.py:339)):
- 只返回 `transaction_type='sale'` 的记录
- 包含产品名称、策略类型、销售人员、营业部等信息

---

### 3. 保有统计

**前端** → 页面加载 → 调用:
- `GET /api/private-fund/holdings/stats`
- `GET /api/private-fund/holdings/groups`
- `GET /api/private-fund/holdings/trend`

**后端处理 - 保有统计** ([private_fund.py:372](backend/app/routers/private_fund.py:372)):
```python
# 计算逻辑
for t in transactions:
    if t.transaction_type == 'sale':
        product_holding += t.amount
    else:  # redeem
        product_holding -= t.amount

# 加权平均保有系数
avg_holding_coeff = sum(holding * coeff) / total_holding
total_assessed_holding = total_holding * avg_holding_coeff
```

**后端处理 - 营业部保有明细** ([private_fund.py:491](backend/app/routers/private_fund.py:491)):
- 按 (member_id, product_id) 维度计算净保有
- 销售 - 赎回 = 净保有
- 按营业部汇总，计算加权平均保有系数

---

## 数据迁移说明

### 迁移脚本

**本地执行**:
```bash
cd /Users/leowang/FinTrack/backend
python scripts/migrate_sales_to_private_fund.py
```

**线上执行 (Railway)**:
```bash
curl -X POST https://fintrack-api-production-879c.up.railway.app/api/private-fund/migrate-sales-to-private-fund
```

### 迁移逻辑

1. 查询 `sales_records` 表中2026年的记录
2. 通过产品名称/code匹配对应的私募产品
3. 创建对应的 `private_fund_transactions` 记录
4. 自动计算 `assessed_amount` = amount × sales_coefficient
5. 标记 `transaction_type='sale'`

---

## 验证检查清单

### 录入销售后验证

- [ ] 年度看板显示新录入的销售数据
  - 总考核销量增加
  - 总实际销量增加
  - 净销量正确计算

- [ ] 保有统计显示新增保有量
  - 实际保有量增加
  - 考核保有量正确计算

- [ ] 营业部保有明细显示
  - 对应营业部保有量增加
  - 产品数量正确

### 录入赎回后验证

- [ ] 年度看板显示
  - 总赎回金额增加
  - 净销量减少（实际销量 - 总赎回）

- [ ] 保有统计显示
  - 实际保有量减少
  - 考核保有量相应减少

---

## 数据库表结构

### private_fund_products
```sql
CREATE TABLE private_fund_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    risk_level VARCHAR(10) NOT NULL,
    sales_coefficient NUMERIC(4,2) NOT NULL DEFAULT 1.0,
    holding_coefficient NUMERIC(4,2) DEFAULT 1.0,
    -- ... 其他字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### private_fund_transactions
```sql
CREATE TABLE private_fund_transactions (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES private_fund_products(id),
    member_id INTEGER REFERENCES members(id),
    transaction_date DATE NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,  -- 'sale' | 'redeem'
    sales_coefficient NUMERIC(4,2),
    assessed_amount NUMERIC(15,2),
    holding_coefficient NUMERIC(4,2),
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
