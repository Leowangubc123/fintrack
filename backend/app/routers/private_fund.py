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
                "product_name": t.product.name if t.product else '未知产品'
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
    """获取保有量趋势数据（模拟数据）"""
    today = date.today()

    if period == "week":
        # 最近12周
        periods = []
        for i in range(11, -1, -1):
            week_start = today - timedelta(days=today.weekday() + i * 7)
            periods.append({
                "period": f"{week_start.month}/{week_start.day}",
                "assessed_holding": 12000 + i * 200 + (i % 3) * 500
            })
    elif period == "month":
        # 最近12个月
        periods = []
        for i in range(11, -1, -1):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            periods.append({
                "period": f"{year}-{month:02d}",
                "assessed_holding": 10000 + i * 300 + (i % 4) * 800
            })
    else:  # quarter
        # 最近8个季度
        periods = []
        for i in range(7, -1, -1):
            quarter = (today.month - 1) // 3 + 1 - i
            year = today.year
            if quarter <= 0:
                quarter += 4
                year -= 1
            periods.append({
                "period": f"{year}Q{quarter}",
                "assessed_holding": 9000 + i * 500 + (i % 2) * 1000
            })

    return periods


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
            # 检查是否已存在
            existing = db.query(PrivateFundProduct).filter(PrivateFundProduct.code == p.get('code')).first()
            if existing:
                continue

            db_product = PrivateFundProduct(
                id=p.get('id'),
                name=p.get('name'),
                code=p.get('code'),
                distribution_scope=p.get('distribution_scope', '全国'),
                strategy_type=p.get('strategy_type'),
                custom_strategy=p.get('custom_strategy'),
                risk_level=p.get('risk_level'),
                lock_period=p.get('lock_period'),
                open_period=p.get('open_period'),
                sales_coefficient=Decimal(str(p.get('sales_coefficient', 1.0))),
                holding_coefficient=Decimal(str(p.get('holding_coefficient', 1.0))) if p.get('holding_coefficient') else Decimal('1.0'),
                subscription_fee=Decimal(str(p.get('subscription_fee'))) if p.get('subscription_fee') else None,
                service_fee=Decimal(str(p.get('service_fee'))) if p.get('service_fee') else None,
                management_fee=Decimal(str(p.get('management_fee'))) if p.get('management_fee') else None,
                performance_fee=p.get('performance_fee')
            )
            db.add(db_product)
            migrated += 1

        db.commit()
        return {"message": f"成功迁移 {migrated} 个产品", "migrated": migrated}

    except Exception as e:
        return {"message": f"迁移失败: {str(e)}", "migrated": 0}
