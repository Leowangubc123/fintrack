from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from app.database import get_db
from app.models import Member, Group, PrivateFundProduct, PrivateFundTransaction

router = APIRouter(prefix="/api/private-fund", tags=["private_fund"])

# ============== Pydantic 数据模型 ==============

class PrivateFundProductBase(BaseModel):
    name: str
    code: str
    distribution_scope: Optional[str] = "全国"
    strategy_type: str
    custom_strategy: Optional[str] = None
    risk_level: str  # R3/R4/R5
    lock_period: Optional[str] = None
    open_period: Optional[str] = None
    sales_coefficient: float
    holding_coefficient: Optional[float] = 1.0
    subscription_fee: Optional[float] = None
    service_fee: Optional[float] = None
    management_fee: Optional[float] = None
    performance_fee: Optional[str] = None

class PrivateFundProductCreate(PrivateFundProductBase):
    pass

class PrivateFundProductResponse(PrivateFundProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PrivateFundTransactionBase(BaseModel):
    product_id: int
    member_id: int
    transaction_date: date
    amount: float
    transaction_type: str  # 'sale' 或 'redeem'
    remark: Optional[str] = None

class PrivateFundTransactionCreate(PrivateFundTransactionBase):
    sales_coefficient: Optional[float] = None
    assessed_amount: Optional[float] = None

class PrivateFundTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    member_id: int
    transaction_date: date
    amount: float
    transaction_type: str
    remark: Optional[str] = None
    sales_coefficient: Optional[float] = None
    assessed_amount: Optional[float] = None
    product_name: Optional[str] = None
    member_name: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    holding_coefficient: Optional[float] = None
    created_at: Optional[datetime] = None


# ============== 产品管理API ==============

@router.get("/products", response_model=List[PrivateFundProductResponse])
def get_products(db: Session = Depends(get_db)):
    """获取所有私募产品列表"""
    products = db.query(PrivateFundProduct).all()
    return [
        PrivateFundProductResponse(
            id=p.id,
            name=p.name,
            code=p.code,
            distribution_scope=p.distribution_scope,
            strategy_type=p.strategy_type,
            custom_strategy=p.custom_strategy,
            risk_level=p.risk_level,
            lock_period=p.lock_period,
            open_period=p.open_period,
            sales_coefficient=float(p.sales_coefficient),
            holding_coefficient=float(p.holding_coefficient) if p.holding_coefficient else 1.0,
            subscription_fee=float(p.subscription_fee) if p.subscription_fee else None,
            service_fee=float(p.service_fee) if p.service_fee else None,
            management_fee=float(p.management_fee) if p.management_fee else None,
            performance_fee=p.performance_fee,
            created_at=p.created_at,
            updated_at=p.updated_at
        ) for p in products
    ]


@router.post("/products", response_model=PrivateFundProductResponse)
def create_product(product: PrivateFundProductCreate, db: Session = Depends(get_db)):
    """创建新私募产品"""
    # 检查产品代码是否已存在
    existing = db.query(PrivateFundProduct).filter(PrivateFundProduct.code == product.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="产品代码已存在")

    db_product = PrivateFundProduct(
        name=product.name,
        code=product.code,
        distribution_scope=product.distribution_scope,
        strategy_type=product.strategy_type,
        custom_strategy=product.custom_strategy,
        risk_level=product.risk_level,
        lock_period=product.lock_period,
        open_period=product.open_period,
        sales_coefficient=Decimal(str(product.sales_coefficient)),
        holding_coefficient=Decimal(str(product.holding_coefficient)) if product.holding_coefficient else Decimal('1.0'),
        subscription_fee=Decimal(str(product.subscription_fee)) if product.subscription_fee else None,
        service_fee=Decimal(str(product.service_fee)) if product.service_fee else None,
        management_fee=Decimal(str(product.management_fee)) if product.management_fee else None,
        performance_fee=product.performance_fee
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return PrivateFundProductResponse(
        id=db_product.id,
        name=db_product.name,
        code=db_product.code,
        distribution_scope=db_product.distribution_scope,
        strategy_type=db_product.strategy_type,
        custom_strategy=db_product.custom_strategy,
        risk_level=db_product.risk_level,
        lock_period=db_product.lock_period,
        open_period=db_product.open_period,
        sales_coefficient=float(db_product.sales_coefficient),
        holding_coefficient=float(db_product.holding_coefficient) if db_product.holding_coefficient else 1.0,
        subscription_fee=float(db_product.subscription_fee) if db_product.subscription_fee else None,
        service_fee=float(db_product.service_fee) if db_product.service_fee else None,
        management_fee=float(db_product.management_fee) if db_product.management_fee else None,
        performance_fee=db_product.performance_fee,
        created_at=db_product.created_at,
        updated_at=db_product.updated_at
    )


@router.put("/products/{product_id}", response_model=PrivateFundProductResponse)
def update_product(product_id: int, product: PrivateFundProductCreate, db: Session = Depends(get_db)):
    """更新私募产品"""
    db_product = db.query(PrivateFundProduct).filter(PrivateFundProduct.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 检查新产品代码是否与其他产品冲突
    if product.code != db_product.code:
        existing = db.query(PrivateFundProduct).filter(PrivateFundProduct.code == product.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="产品代码已存在")

    db_product.name = product.name
    db_product.code = product.code
    db_product.distribution_scope = product.distribution_scope
    db_product.strategy_type = product.strategy_type
    db_product.custom_strategy = product.custom_strategy
    db_product.risk_level = product.risk_level
    db_product.lock_period = product.lock_period
    db_product.open_period = product.open_period
    db_product.sales_coefficient = Decimal(str(product.sales_coefficient))
    db_product.holding_coefficient = Decimal(str(product.holding_coefficient)) if product.holding_coefficient else Decimal('1.0')
    db_product.subscription_fee = Decimal(str(product.subscription_fee)) if product.subscription_fee else None
    db_product.service_fee = Decimal(str(product.service_fee)) if product.service_fee else None
    db_product.management_fee = Decimal(str(product.management_fee)) if product.management_fee else None
    db_product.performance_fee = product.performance_fee

    db.commit()
    db.refresh(db_product)

    return PrivateFundProductResponse(
        id=db_product.id,
        name=db_product.name,
        code=db_product.code,
        distribution_scope=db_product.distribution_scope,
        strategy_type=db_product.strategy_type,
        custom_strategy=db_product.custom_strategy,
        risk_level=db_product.risk_level,
        lock_period=db_product.lock_period,
        open_period=db_product.open_period,
        sales_coefficient=float(db_product.sales_coefficient),
        holding_coefficient=float(db_product.holding_coefficient) if db_product.holding_coefficient else 1.0,
        subscription_fee=float(db_product.subscription_fee) if db_product.subscription_fee else None,
        service_fee=float(db_product.service_fee) if db_product.service_fee else None,
        management_fee=float(db_product.management_fee) if db_product.management_fee else None,
        performance_fee=db_product.performance_fee,
        created_at=db_product.created_at,
        updated_at=db_product.updated_at
    )


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除私募产品"""
    db_product = db.query(PrivateFundProduct).filter(PrivateFundProduct.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    db.delete(db_product)
    db.commit()
    return {"message": "删除成功"}


# ============== 交易记录API ==============

@router.post("/transactions", response_model=PrivateFundTransactionResponse)
def create_transaction(transaction: PrivateFundTransactionCreate, db: Session = Depends(get_db)):
    """创建交易记录（销售或赎回）"""
    # 获取产品信息
    product = db.query(PrivateFundProduct).filter(PrivateFundProduct.id == transaction.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 获取销售人员信息
    member = db.query(Member).filter(Member.id == transaction.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="销售人员不存在")

    group = db.query(Group).filter(Group.id == member.group_id).first()

    # 计算考核销量（销售时）
    assessed_amount = None
    sales_coefficient = None
    if transaction.transaction_type == 'sale':
        sales_coefficient = transaction.sales_coefficient or float(product.sales_coefficient)
        assessed_amount = transaction.amount * sales_coefficient

    db_transaction = PrivateFundTransaction(
        product_id=transaction.product_id,
        member_id=transaction.member_id,
        transaction_date=transaction.transaction_date,
        amount=Decimal(str(transaction.amount)),
        transaction_type=transaction.transaction_type,
        remark=transaction.remark,
        sales_coefficient=Decimal(str(sales_coefficient)) if sales_coefficient else None,
        assessed_amount=Decimal(str(assessed_amount)) if assessed_amount else None,
        holding_coefficient=product.holding_coefficient or Decimal('1.0')
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return PrivateFundTransactionResponse(
        id=db_transaction.id,
        product_id=db_transaction.product_id,
        member_id=db_transaction.member_id,
        transaction_date=db_transaction.transaction_date,
        amount=float(db_transaction.amount),
        transaction_type=db_transaction.transaction_type,
        remark=db_transaction.remark,
        sales_coefficient=float(db_transaction.sales_coefficient) if db_transaction.sales_coefficient else None,
        assessed_amount=float(db_transaction.assessed_amount) if db_transaction.assessed_amount else None,
        product_name=product.name,
        member_name=member.name,
        group_id=member.group_id,
        group_name=group.name if group else '未知',
        holding_coefficient=float(db_transaction.holding_coefficient) if db_transaction.holding_coefficient else 1.0,
        created_at=db_transaction.created_at
    )


@router.get("/transactions/recent", response_model=List[PrivateFundTransactionResponse])
def get_recent_transactions(limit: int = 10, db: Session = Depends(get_db)):
    """获取最近交易记录"""
    transactions = db.query(PrivateFundTransaction).order_by(
        PrivateFundTransaction.created_at.desc()
    ).limit(limit).all()

    result = []
    for t in transactions:
        member = db.query(Member).filter(Member.id == t.member_id).first()
        product = db.query(PrivateFundProduct).filter(PrivateFundProduct.id == t.product_id).first()
        group = db.query(Group).filter(Group.id == member.group_id).first() if member else None

        result.append(PrivateFundTransactionResponse(
            id=t.id,
            product_id=t.product_id,
            member_id=t.member_id,
            transaction_date=t.transaction_date,
            amount=float(t.amount),
            transaction_type=t.transaction_type,
            remark=t.remark,
            sales_coefficient=float(t.sales_coefficient) if t.sales_coefficient else None,
            assessed_amount=float(t.assessed_amount) if t.assessed_amount else None,
            product_name=product.name if product else '未知产品',
            member_name=member.name if member else '未知人员',
            group_id=member.group_id if member else None,
            group_name=group.name if group else '未知营业部',
            holding_coefficient=float(t.holding_coefficient) if t.holding_coefficient else 1.0,
            created_at=t.created_at
        ))

    return result


@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """删除交易记录"""
    transaction = db.query(PrivateFundTransaction).filter(
        PrivateFundTransaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    db.delete(transaction)
    db.commit()

    return {"message": "删除成功", "id": transaction_id}


# ============== 年度统计API ==============

@router.get("/stats/annual")
def get_annual_stats(year: Optional[int] = None, db: Session = Depends(get_db)):
    """获取年度统计数据"""
    if not year:
        year = date.today().year

    transactions = db.query(PrivateFundTransaction).filter(
        extract('year', PrivateFundTransaction.transaction_date) == year
    ).all()

    total_assessed_sales = 0
    total_actual_sales = 0
    total_redemption = 0

    for t in transactions:
        if t.transaction_type == 'sale':
            total_actual_sales += float(t.amount)
            total_assessed_sales += float(t.assessed_amount) if t.assessed_amount else 0
        else:
            total_redemption += float(t.amount)

    return {
        "total_assessed_sales": round(total_assessed_sales, 2),
        "total_actual_sales": round(total_actual_sales, 2),
        "total_redemption": round(total_redemption, 2),
        "net_sales": round(total_actual_sales - total_redemption, 2)
    }


@router.get("/sales/annual")
def get_annual_sales(year: Optional[int] = None, db: Session = Depends(get_db)):
    """获取年度销售明细"""
    if not year:
        year = date.today().year

    transactions = db.query(PrivateFundTransaction).filter(
        extract('year', PrivateFundTransaction.transaction_date) == year,
        PrivateFundTransaction.transaction_type == 'sale'
    ).all()

    result = []
    for t in transactions:
        member = db.query(Member).filter(Member.id == t.member_id).first()
        product = db.query(PrivateFundProduct).filter(PrivateFundProduct.id == t.product_id).first()
        group = db.query(Group).filter(Group.id == member.group_id).first() if member else None

        result.append({
            "id": t.id,
            "transaction_date": t.transaction_date.isoformat(),
            "product_name": product.name if product else '未知产品',
            "strategy_type": product.strategy_type if product else '',
            "member_name": member.name if member else '未知人员',
            "group_name": group.name if group else '未知营业部',
            "amount": float(t.amount),
            "assessed_amount": float(t.assessed_amount) if t.assessed_amount else None,
            "sales_coefficient": float(t.sales_coefficient) if t.sales_coefficient else None
        })

    return result


# ============== 保有统计API ==============

@router.get("/holdings/stats")
def get_holding_stats(db: Session = Depends(get_db)):
    """获取保有统计数据"""
    # 计算所有产品的实际保有量
    transactions = db.query(PrivateFundTransaction).all()

    product_holdings = {}
    for t in transactions:
        if t.product_id not in product_holdings:
            product_holdings[t.product_id] = 0
        if t.transaction_type == 'sale':
            product_holdings[t.product_id] += float(t.amount)
        else:
            product_holdings[t.product_id] -= float(t.amount)

    total_holding = sum(max(0, h) for h in product_holdings.values())

    # 计算加权平均保有系数
    total_weighted_coeff = 0
    for pid, holding in product_holdings.items():
        if holding > 0:
            product = db.query(PrivateFundProduct).filter(PrivateFundProduct.id == pid).first()
            if product:
                coeff = float(product.holding_coefficient) if product.holding_coefficient else 1.0
                total_weighted_coeff += holding * coeff

    avg_holding_coeff = total_weighted_coeff / total_holding if total_holding > 0 else 0
    total_assessed_holding = total_holding * avg_holding_coeff

    return {
        "total_holding": round(total_holding, 2),
        "avg_holding_coeff": round(avg_holding_coeff, 2),
        "total_assessed_holding": round(total_assessed_holding, 2)
    }


@router.get("/holdings/products")
def get_product_holdings(db: Session = Depends(get_db)):
    """获取各产品保有量明细"""
    transactions = db.query(PrivateFundTransaction).all()

    # 计算各产品保有量
    product_stats = {}
    for t in transactions:
        if t.product_id not in product_stats:
            product_stats[t.product_id] = {
                "holding": 0,
                "product_name": None  # 稍后从数据库查询
            }
        if t.transaction_type == 'sale':
            product_stats[t.product_id]["holding"] += float(t.amount)
        else:
            product_stats[t.product_id]["holding"] -= float(t.amount)

    # 组装返回数据
    result = []
    for pid, stats in product_stats.items():
        if stats["holding"] > 0:
            product = db.query(PrivateFundProduct).filter(PrivateFundProduct.id == pid).first()
            if product:
                holding = max(0, stats["holding"])
                coeff = float(product.holding_coefficient) if product.holding_coefficient else 1.0
                result.append({
                    "product_id": pid,
                    "product_name": product.name,
                    "strategy_type": product.strategy_type,
                    "risk_level": product.risk_level,
                    "holding_amount": round(holding, 2),
                    "holding_coefficient": coeff,
                    "assessed_holding": round(holding * coeff, 2)
                })

    return sorted(result, key=lambda x: x["assessed_holding"], reverse=True)


@router.get("/holdings/trend")
def get_holding_trend(period: str = "week", db: Session = Depends(get_db)):
    """获取保有量趋势数据（基于真实交易计算）"""
    from datetime import datetime
    from collections import defaultdict

    today = date.today()
    transactions = db.query(PrivateFundTransaction).all()
    products = db.query(PrivateFundProduct).all()
    product_map = {p.id: p for p in products}

    # 生成时间段列表
    periods = []
    if period == "week":
        # 最近12周
        for i in range(11, -1, -1):
            week_end = today - timedelta(days=today.weekday() + i * 7 - 6)
            week_start = week_end - timedelta(days=6)
            periods.append({
                "label": f"{week_start.month}/{week_start.day}",
                "end_date": week_end,
                "start_date": week_start
            })
    elif period == "month":
        # 最近12个月
        for i in range(11, -1, -1):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            # 该月最后一天
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            month_end = next_month - timedelta(days=1)
            periods.append({
                "label": f"{year}-{month:02d}",
                "end_date": month_end,
                "start_date": date(year, month, 1)
            })
    else:  # quarter
        # 最近8个季度
        for i in range(7, -1, -1):
            quarter = (today.month - 1) // 3 + 1 - i
            year = today.year
            if quarter <= 0:
                quarter += 4
                year -= 1
            # 季度末最后一天
            quarter_end_month = quarter * 3
            if quarter_end_month == 12:
                next_q = date(year + 1, 1, 1)
            else:
                next_q = date(year, quarter_end_month + 1, 1)
            quarter_end = next_q - timedelta(days=1)
            periods.append({
                "label": f"{year}Q{quarter}",
                "end_date": quarter_end,
                "start_date": date(year, (quarter - 1) * 3 + 1, 1)
            })

    # 按时间段累计计算保有量
    result = []
    for period_info in periods:
        end_date = period_info["end_date"]

        # 计算到该时间点为止的累计保有
        product_holdings = defaultdict(float)

        for t in transactions:
            if t.transaction_date > end_date:
                continue  # 该时间点之后的交易不计入

            if t.transaction_type == 'sale':
                product_holdings[t.product_id] += float(t.amount)
            else:  # redeem
                product_holdings[t.product_id] -= float(t.amount)

        # 计算考核保有量（考虑保有系数）
        total_assessed_holding = 0
        for pid, holding in product_holdings.items():
            if holding > 0:
                product = product_map.get(pid)
                coeff = float(product.holding_coefficient) if product and product.holding_coefficient else 1.0
                total_assessed_holding += holding * coeff

        result.append({
            "period": period_info["label"],
            "assessed_holding": round(total_assessed_holding, 2)
        })

    return result


@router.get("/holdings/groups")
def get_group_holdings(db: Session = Depends(get_db)):
    """获取各营业部保有明细（按成员和产品维度计算）"""
    # 获取所有交易记录
    transactions = db.query(PrivateFundTransaction).all()
    products = db.query(PrivateFundProduct).all()
    members = db.query(Member).all()
    groups = db.query(Group).all()

    # 构建查询映射
    product_map = {p.id: p for p in products}
    member_map = {m.id: m for m in members}
    group_map = {g.id: g for g in groups}

    # 计算每个成员每个产品的净保有
    member_product_holding = {}  # {(member_id, product_id): net_holding}
    for t in transactions:
        key = (t.member_id, t.product_id)
        if key not in member_product_holding:
            member_product_holding[key] = 0
        if t.transaction_type == 'sale':
            member_product_holding[key] += float(t.amount)
        else:
            member_product_holding[key] -= float(t.amount)

    # 按营业部汇总
    group_stats = {}
    for (member_id, product_id), holding in member_product_holding.items():
        if holding <= 0:
            continue

        member = member_map.get(member_id)
        if not member:
            continue

        group_id = member.group_id
        group = group_map.get(group_id)
        if not group:
            continue

        product = product_map.get(product_id)
        holding_coeff = product.holding_coefficient if product else 1.0
        if isinstance(holding_coeff, Decimal):
            holding_coeff = float(holding_coeff)

        if group_id not in group_stats:
            group_stats[group_id] = {
                "group_id": group_id,
                "group_name": group.name,
                "total_holding": 0,
                "total_assessed": 0,
                "total_coeff_weighted": 0,
                "product_count": set()
            }

        group_stats[group_id]["total_holding"] += holding
        group_stats[group_id]["total_assessed"] += holding * holding_coeff
        group_stats[group_id]["total_coeff_weighted"] += holding * holding_coeff
        group_stats[group_id]["product_count"].add(product_id)

    # 组装结果
    result = []
    for stats in group_stats.values():
        total_holding = stats["total_holding"]
        avg_coeff = stats["total_coeff_weighted"] / total_holding if total_holding > 0 else 1.0
        result.append({
            "group_id": stats["group_id"],
            "group_name": stats["group_name"],
            "holding_amount": round(total_holding, 2),
            "avg_holding_coeff": round(avg_coeff, 2),
            "assessed_holding": round(stats["total_assessed"], 2),
            "product_count": len(stats["product_count"])
        })

    # 按考核保有量降序排列
    return sorted(result, key=lambda x: x["assessed_holding"], reverse=True)


# ============== 数据迁移API（一次性使用） ==============

@router.post("/migrate-from-pickle")
def migrate_from_pickle(db: Session = Depends(get_db)):
    """从pickle文件迁移数据到数据库（一次性使用）"""
    import os
    import pickle

    pickle_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'private_fund_products.pkl')

    if not os.path.exists(pickle_path):
        return {"message": "pickle文件不存在", "migrated": 0}

    try:
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)

        products = data.get('products', [])
        migrated = 0

        for p in products:
            # 从对象实例获取属性（pickle存储的是对象，不是字典）
            code = getattr(p, 'code', None)
            if not code:
                continue

            # 检查是否已存在
            existing = db.query(PrivateFundProduct).filter(PrivateFundProduct.code == code).first()
            if existing:
                continue

            # 获取销售系数和保有系数，处理不同可能的数据类型
            sales_coeff = getattr(p, 'sales_coefficient', 1.0)
            holding_coeff = getattr(p, 'holding_coefficient', 1.0)

            # 转换为 Decimal
            if isinstance(sales_coeff, Decimal):
                sales_coeff_decimal = sales_coeff
            else:
                sales_coeff_decimal = Decimal(str(sales_coeff))

            if isinstance(holding_coeff, Decimal):
                holding_coeff_decimal = holding_coeff
            else:
                holding_coeff_decimal = Decimal(str(holding_coeff)) if holding_coeff else Decimal('1.0')

            db_product = PrivateFundProduct(
                name=getattr(p, 'name', ''),
                code=code,
                distribution_scope=getattr(p, 'distribution_scope', '全国'),
                strategy_type=getattr(p, 'strategy_type', ''),
                custom_strategy=getattr(p, 'custom_strategy', None),
                risk_level=getattr(p, 'risk_level', 'R3'),
                lock_period=getattr(p, 'lock_period', None),
                open_period=getattr(p, 'open_period', None),
                sales_coefficient=sales_coeff_decimal,
                holding_coefficient=holding_coeff_decimal,
                subscription_fee=Decimal(str(getattr(p, 'subscription_fee', None))) if getattr(p, 'subscription_fee', None) else None,
                service_fee=Decimal(str(getattr(p, 'service_fee', None))) if getattr(p, 'service_fee', None) else None,
                management_fee=Decimal(str(getattr(p, 'management_fee', None))) if getattr(p, 'management_fee', None) else None,
                performance_fee=getattr(p, 'performance_fee', None)
            )
            db.add(db_product)
            migrated += 1

        db.commit()
        return {"message": f"成功迁移 {migrated} 个产品", "migrated": migrated}

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return {"message": f"迁移失败: {str(e)}", "migrated": 0}


@router.post("/migrate-sales-to-private-fund")
def migrate_sales_to_private_fund(db: Session = Depends(get_db)):
    """将2026年销售记录迁移到私募交易表"""
    from app.models import SalesRecord, Product
    from sqlalchemy import func

    try:
        # 1. 获取2026年的销售记录
        sales_records = db.query(SalesRecord).filter(
            extract('year', SalesRecord.sale_date) == 2026
        ).all()

        # 2. 获取所有私募产品，建立映射
        private_products = db.query(PrivateFundProduct).all()
        private_product_by_code = {p.code: p for p in private_products}
        private_product_by_name = {p.name: p for p in private_products}

        # 3. 获取普通产品信息
        products = db.query(Product).all()
        product_map = {p.id: p for p in products}

        # 4. 处理每条销售记录
        migrated = 0
        skipped = 0
        errors = []

        for record in sales_records:
            product = product_map.get(record.product_id)
            if not product:
                skipped += 1
                errors.append(f"记录ID {record.id}: 找不到对应的产品")
                continue

            # 尝试匹配私募产品
            private_product = None
            if product.name in private_product_by_name:
                private_product = private_product_by_name[product.name]
            elif product.code and product.code in private_product_by_code:
                private_product = private_product_by_code[product.code]

            if not private_product:
                skipped += 1
                continue

            # 检查是否已存在
            existing = db.query(PrivateFundTransaction).filter(
                PrivateFundTransaction.product_id == private_product.id,
                PrivateFundTransaction.member_id == record.member_id,
                PrivateFundTransaction.transaction_date == record.sale_date,
                PrivateFundTransaction.amount == record.amount
            ).first()

            if existing:
                skipped += 1
                continue

            # 创建私募交易记录
            sales_coefficient = float(private_product.sales_coefficient)
            assessed_amount = float(record.amount) * sales_coefficient

            transaction = PrivateFundTransaction(
                product_id=private_product.id,
                member_id=record.member_id,
                transaction_date=record.sale_date,
                amount=record.amount,
                transaction_type='sale',
                sales_coefficient=Decimal(str(sales_coefficient)),
                assessed_amount=Decimal(str(assessed_amount)),
                holding_coefficient=private_product.holding_coefficient or Decimal('1.0'),
                remark="从销售记录迁移"
            )

            db.add(transaction)
            migrated += 1

        db.commit()

        return {
            "message": "迁移完成",
            "total_sales_records": len(sales_records),
            "migrated": migrated,
            "skipped": skipped,
            "errors": errors[:10] if errors else []
        }

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"迁移失败: {str(e)}")


# ============== 保有数据管理API ==============

from app.models import PrivateFundHolding

class HoldingUploadItem(BaseModel):
    product_code: str
    group_name: str
    holding_market_value: float
    product_name: Optional[str] = None  # 可选，仅用于错误提示

class HoldingDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    product_code: str
    group_name: str
    group_id: int
    holding_market_value: float
    holding_coefficient: float
    assessed_holding: float
    record_date: date
    created_at: Optional[datetime] = None

class HoldingStatsResponse(BaseModel):
    total_assessed_holding: float
    total_market_value: float
    record_count: int
    latest_record_date: Optional[date] = None
    group_stats: List[dict]
    trend_data: List[dict]

@router.post("/holdings/upload")
def upload_holdings(
    data: List[HoldingUploadItem],
    record_date: date,
    db: Session = Depends(get_db)
):
    """上传保有数据

    参数:
    - data: 保有数据列表，包含产品名称、代码、营业部、保有市值
    - record_date: 数据日期（时点）

    系统会自动:
    1. 根据产品代码匹配产品库中的保有系数
    2. 计算考核保有量 = 保有市值 × 保有系数
    3. 保存到数据库
    """
    try:
        # 获取所有产品
        products = db.query(PrivateFundProduct).all()
        product_by_code = {p.code: p for p in products}

        # 获取所有营业部
        groups = db.query(Group).all()
        group_by_name = {g.name: g for g in groups}

        success_count = 0
        errors = []

        for item in data:
            # 查找产品（仅通过产品代码）
            product = product_by_code.get(item.product_code)
            if not product:
                errors.append(f"未找到产品: {item.product_code}")
                continue

            # 查找营业部
            group = group_by_name.get(item.group_name)
            if not group:
                errors.append(f"未找到营业部: {item.group_name}")
                continue

            # 获取保有系数
            holding_coefficient = float(product.holding_coefficient) if product.holding_coefficient else 1.0

            # 计算考核保有量
            assessed_holding = item.holding_market_value * holding_coefficient

            # 检查是否已存在该日期该产品该营业部的记录
            existing = db.query(PrivateFundHolding).filter(
                PrivateFundHolding.product_id == product.id,
                PrivateFundHolding.group_id == group.id,
                PrivateFundHolding.record_date == record_date
            ).first()

            if existing:
                # 更新现有记录
                existing.holding_market_value = Decimal(str(item.holding_market_value))
                existing.holding_coefficient = Decimal(str(holding_coefficient))
                existing.assessed_holding = Decimal(str(assessed_holding))
            else:
                # 创建新记录
                holding = PrivateFundHolding(
                    product_id=product.id,
                    group_id=group.id,
                    holding_market_value=Decimal(str(item.holding_market_value)),
                    holding_coefficient=Decimal(str(holding_coefficient)),
                    assessed_holding=Decimal(str(assessed_holding)),
                    record_date=record_date
                )
                db.add(holding)

            success_count += 1

        db.commit()

        return {
            "message": "上传成功",
            "record_date": record_date.isoformat(),
            "success_count": success_count,
            "errors": errors
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/holdings", response_model=List[HoldingDataResponse])
def get_holdings(
    group_id: Optional[int] = None,
    record_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """获取保有数据列表"""
    query = db.query(
        PrivateFundHolding,
        PrivateFundProduct.name.label("product_name"),
        PrivateFundProduct.code.label("product_code"),
        Group.name.label("group_name")
    ).join(
        PrivateFundProduct, PrivateFundHolding.product_id == PrivateFundProduct.id
    ).join(
        Group, PrivateFundHolding.group_id == Group.id
    )

    if group_id:
        query = query.filter(PrivateFundHolding.group_id == group_id)

    if record_date:
        query = query.filter(PrivateFundHolding.record_date == record_date)
    else:
        # 默认获取最新日期的数据
        latest_date = db.query(func.max(PrivateFundHolding.record_date)).scalar()
        if latest_date:
            query = query.filter(PrivateFundHolding.record_date == latest_date)

    results = query.order_by(PrivateFundHolding.assessed_holding.desc()).all()

    return [
        HoldingDataResponse(
            id=h.PrivateFundHolding.id,
            product_name=h.product_name,
            product_code=h.product_code,
            group_name=h.group_name,
            group_id=h.PrivateFundHolding.group_id,
            holding_market_value=float(h.PrivateFundHolding.holding_market_value),
            holding_coefficient=float(h.PrivateFundHolding.holding_coefficient),
            assessed_holding=float(h.PrivateFundHolding.assessed_holding),
            record_date=h.PrivateFundHolding.record_date,
            created_at=h.PrivateFundHolding.created_at
        ) for h in results
    ]

@router.get("/holdings/stats", response_model=HoldingStatsResponse)
def get_holding_stats(db: Session = Depends(get_db)):
    """获取保有统计数据"""
    # 获取最新日期的数据
    latest_date = db.query(func.max(PrivateFundHolding.record_date)).scalar()

    if not latest_date:
        return HoldingStatsResponse(
            total_assessed_holding=0,
            total_market_value=0,
            record_count=0,
            latest_record_date=None,
            group_stats=[],
            trend_data=[]
        )

    # 总考核保有量和总保有市值
    totals = db.query(
        func.sum(PrivateFundHolding.assessed_holding).label("total_assessed"),
        func.sum(PrivateFundHolding.holding_market_value).label("total_market"),
        func.count(PrivateFundHolding.id).label("count")
    ).filter(
        PrivateFundHolding.record_date == latest_date
    ).first()

    # 按营业部统计
    group_stats_query = db.query(
        Group.name.label("group_name"),
        func.sum(PrivateFundHolding.assessed_holding).label("assessed_holding"),
        func.sum(PrivateFundHolding.holding_market_value).label("market_value")
    ).join(
        Group, PrivateFundHolding.group_id == Group.id
    ).filter(
        PrivateFundHolding.record_date == latest_date
    ).group_by(
        Group.id, Group.name
    ).order_by(
        func.sum(PrivateFundHolding.assessed_holding).desc()
    ).all()

    group_stats = [
        {
            "group_name": g.group_name,
            "assessed_holding": float(g.assessed_holding or 0),
            "market_value": float(g.market_value or 0)
        } for g in group_stats_query
    ]

    # 趋势数据（按record_date分组）
    trend_query = db.query(
        PrivateFundHolding.record_date,
        func.sum(PrivateFundHolding.assessed_holding).label("total_assessed"),
        func.sum(PrivateFundHolding.holding_market_value).label("total_market")
    ).group_by(
        PrivateFundHolding.record_date
    ).order_by(
        PrivateFundHolding.record_date
    ).all()

    trend_data = [
        {
            "record_date": t.record_date.isoformat(),
            "assessed_holding": float(t.total_assessed or 0),
            "market_value": float(t.total_market or 0)
        } for t in trend_query
    ]

    return HoldingStatsResponse(
        total_assessed_holding=float(totals.total_assessed or 0),
        total_market_value=float(totals.total_market or 0),
        record_count=totals.count or 0,
        latest_record_date=latest_date,
        group_stats=group_stats,
        trend_data=trend_data
    )

@router.get("/holdings/dates")
def get_holding_dates(db: Session = Depends(get_db)):
    """获取所有有数据的日期列表"""
    dates = db.query(
        PrivateFundHolding.record_date
    ).distinct().order_by(
        PrivateFundHolding.record_date.desc()
    ).all()

    return [d.record_date.isoformat() for d in dates]
