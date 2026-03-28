from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Member, Group
import os
import pickle

router = APIRouter(prefix="/api/private-fund", tags=["private_fund"])

# ============== 数据模型 ==============

class PrivateFundProductBase(BaseModel):
    name: str
    code: str
    manager: str
    distribution_scope: Optional[str] = "全国"
    strategy_type: str
    risk_level: str  # R3/R4/R5
    lock_period: Optional[str] = None
    open_period: Optional[str] = None  # 开放期
    sales_coefficient: float
    holding_coefficient: Optional[float] = 1.0
    subscription_fee: Optional[float] = None
    service_fee: Optional[float] = None
    management_fee: Optional[float] = None
    performance_fee: Optional[str] = None

class PrivateFundProductCreate(PrivateFundProductBase):
    pass

class PrivateFundProductResponse(PrivateFundProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

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

class PrivateFundTransactionResponse(PrivateFundTransactionBase):
    id: int
    sales_coefficient: Optional[float] = None
    assessed_amount: Optional[float] = None
    product_name: Optional[str] = None
    member_name: Optional[str] = None
    group_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ============== 数据库模型（需要在models.py中添加）=============
# 这里使用内存存储作为示例，实际应该添加到models.py

class PrivateFundProduct:
    _id_counter = 0
    _products = []
    _data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'private_fund_products.pkl')

    def __init__(self, **kwargs):
        PrivateFundProduct._id_counter += 1
        self.id = PrivateFundProduct._id_counter
        self.__dict__.update(kwargs)
        self.created_at = datetime.now()
        self.updated_at = None

    @classmethod
    def _save_to_file(cls):
        """保存数据到文件"""
        try:
            os.makedirs(os.path.dirname(cls._data_file), exist_ok=True)
            with open(cls._data_file, 'wb') as f:
                pickle.dump({
                    'products': cls._products,
                    'id_counter': cls._id_counter
                }, f)
        except Exception as e:
            print(f"[WARN] Failed to save private fund data: {e}")

    @classmethod
    def _load_from_file(cls):
        """从文件加载数据"""
        if os.path.exists(cls._data_file):
            try:
                with open(cls._data_file, 'rb') as f:
                    data = pickle.load(f)
                    cls._products = data.get('products', [])
                    cls._id_counter = data.get('id_counter', 0)
                    print(f"[INFO] Loaded {len(cls._products)} private fund products from file")
            except Exception as e:
                print(f"[WARN] Failed to load private fund data: {e}")

    @classmethod
    def create(cls, data):
        # 确保已加载数据
        if not cls._products and os.path.exists(cls._data_file):
            cls._load_from_file()
        product = cls(**data)
        cls._products.append(product)
        cls._save_to_file()
        return product

    @classmethod
    def get_all(cls):
        if not cls._products and os.path.exists(cls._data_file):
            cls._load_from_file()
        return cls._products

    @classmethod
    def get_by_id(cls, product_id):
        if not cls._products and os.path.exists(cls._data_file):
            cls._load_from_file()
        for p in cls._products:
            if p.id == product_id:
                return p
        return None

    @classmethod
    def update(cls, product_id, data):
        product = cls.get_by_id(product_id)
        if product:
            for key, value in data.items():
                setattr(product, key, value)
            product.updated_at = datetime.now()
            cls._save_to_file()
        return product

    @classmethod
    def delete(cls, product_id):
        product = cls.get_by_id(product_id)
        if product:
            cls._products.remove(product)
            cls._save_to_file()
            return True
        return False


class PrivateFundTransaction:
    _id_counter = 0
    _transactions = []

    def __init__(self, **kwargs):
        PrivateFundTransaction._id_counter += 1
        self.id = PrivateFundTransaction._id_counter
        self.__dict__.update(kwargs)
        self.created_at = datetime.now()

    @classmethod
    def create(cls, data):
        transaction = cls(**data)
        cls._transactions.append(transaction)
        return transaction

    @classmethod
    def get_all(cls, limit=None):
        transactions = sorted(cls._transactions, key=lambda x: x.created_at, reverse=True)
        if limit:
            return transactions[:limit]
        return transactions

    @classmethod
    def get_by_year(cls, year):
        return [t for t in cls._transactions
                if t.transaction_date.year == year]


# ============== 产品管理API ==============

@router.get("/products", response_model=List[PrivateFundProductResponse])
def get_products(db: Session = Depends(get_db)):
    """获取所有私募产品列表"""
    products = PrivateFundProduct.get_all()
    return [
        PrivateFundProductResponse(
            id=p.id,
            name=p.name,
            code=p.code,
            manager=p.manager,
            distribution_scope=p.distribution_scope,
            strategy_type=p.strategy_type,
            risk_level=p.risk_level,
            lock_period=p.lock_period,
            sales_coefficient=p.sales_coefficient,
            holding_coefficient=p.holding_coefficient,
            subscription_fee=p.subscription_fee,
            redemption_fee=p.redemption_fee,
            service_fee=p.service_fee,
            management_fee=p.management_fee,
            performance_fee=p.performance_fee,
            created_at=p.created_at,
            updated_at=p.updated_at
        ) for p in products
    ]


@router.post("/products", response_model=PrivateFundProductResponse)
def create_product(product: PrivateFundProductCreate, db: Session = Depends(get_db)):
    """创建新私募产品"""
    p = PrivateFundProduct.create(product.dict())
    return PrivateFundProductResponse(
        id=p.id,
        name=p.name,
        code=p.code,
        manager=p.manager,
        distribution_scope=p.distribution_scope,
        strategy_type=p.strategy_type,
        risk_level=p.risk_level,
        lock_period=p.lock_period,
        sales_coefficient=p.sales_coefficient,
        holding_coefficient=p.holding_coefficient,
        subscription_fee=p.subscription_fee,
        redemption_fee=p.redemption_fee,
        service_fee=p.service_fee,
        management_fee=p.management_fee,
        performance_fee=p.performance_fee,
        created_at=p.created_at,
        updated_at=p.updated_at
    )


@router.put("/products/{product_id}", response_model=PrivateFundProductResponse)
def update_product(product_id: int, product: PrivateFundProductCreate, db: Session = Depends(get_db)):
    """更新私募产品"""
    p = PrivateFundProduct.update(product_id, product.dict())
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    return PrivateFundProductResponse(
        id=p.id,
        name=p.name,
        code=p.code,
        manager=p.manager,
        distribution_scope=p.distribution_scope,
        strategy_type=p.strategy_type,
        risk_level=p.risk_level,
        lock_period=p.lock_period,
        sales_coefficient=p.sales_coefficient,
        holding_coefficient=p.holding_coefficient,
        subscription_fee=p.subscription_fee,
        redemption_fee=p.redemption_fee,
        service_fee=p.service_fee,
        management_fee=p.management_fee,
        performance_fee=p.performance_fee,
        created_at=p.created_at,
        updated_at=p.updated_at
    )


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除私募产品"""
    success = PrivateFundProduct.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="产品不存在")
    return {"message": "删除成功"}


# ============== 交易记录API ==============

@router.post("/transactions", response_model=PrivateFundTransactionResponse)
def create_transaction(transaction: PrivateFundTransactionCreate, db: Session = Depends(get_db)):
    """创建交易记录（销售或赎回）"""
    # 获取产品信息
    product = PrivateFundProduct.get_by_id(transaction.product_id)
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
        sales_coefficient = transaction.sales_coefficient or product.sales_coefficient
        assessed_amount = transaction.amount * sales_coefficient

    data = {
        **transaction.dict(),
        'sales_coefficient': sales_coefficient,
        'assessed_amount': assessed_amount,
        'product_name': product.name,
        'member_name': member.name,
        'group_name': group.name if group else '未知'
    }

    t = PrivateFundTransaction.create(data)

    return PrivateFundTransactionResponse(
        id=t.id,
        product_id=t.product_id,
        member_id=t.member_id,
        transaction_date=t.transaction_date,
        amount=t.amount,
        transaction_type=t.transaction_type,
        remark=t.remark,
        sales_coefficient=t.sales_coefficient,
        assessed_amount=t.assessed_amount,
        product_name=t.product_name,
        member_name=t.member_name,
        group_name=t.group_name,
        created_at=t.created_at
    )


@router.get("/transactions/recent")
def get_recent_transactions(limit: int = 10, db: Session = Depends(get_db)):
    """获取最近交易记录"""
    transactions = PrivateFundTransaction.get_all(limit=limit)
    return [
        PrivateFundTransactionResponse(
            id=t.id,
            product_id=t.product_id,
            member_id=t.member_id,
            transaction_date=t.transaction_date,
            amount=t.amount,
            transaction_type=t.transaction_type,
            remark=t.remark,
            sales_coefficient=t.sales_coefficient,
            assessed_amount=t.assessed_amount,
            product_name=t.product_name,
            member_name=t.member_name,
            group_name=t.group_name,
            created_at=t.created_at
        ) for t in transactions
    ]


# ============== 年度统计API ==============

@router.get("/stats/annual")
def get_annual_stats(year: Optional[int] = None, db: Session = Depends(get_db)):
    """获取年度统计数据"""
    if not year:
        year = date.today().year

    transactions = PrivateFundTransaction.get_by_year(year)

    total_assessed_sales = 0
    total_actual_sales = 0
    total_redemption = 0

    for t in transactions:
        if t.transaction_type == 'sale':
            total_actual_sales += t.amount
            total_assessed_sales += t.assessed_amount or 0
        else:
            total_redemption += t.amount

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

    transactions = [t for t in PrivateFundTransaction.get_by_year(year)
                    if t.transaction_type == 'sale']

    return [
        {
            "id": t.id,
            "transaction_date": t.transaction_date.isoformat(),
            "product_name": t.product_name,
            "member_name": t.member_name,
            "group_name": t.group_name,
            "amount": t.amount,
            "assessed_amount": t.assessed_amount,
            "sales_coefficient": t.sales_coefficient
        }
        for t in transactions
    ]


# ============== 保有统计API ==============

@router.get("/holdings/stats")
def get_holding_stats(db: Session = Depends(get_db)):
    """获取保有统计数据"""
    # 计算所有产品的实际保有量
    transactions = PrivateFundTransaction.get_all()

    product_holdings = {}
    for t in transactions:
        if t.product_id not in product_holdings:
            product_holdings[t.product_id] = 0
        if t.transaction_type == 'sale':
            product_holdings[t.product_id] += t.amount
        else:
            product_holdings[t.product_id] -= t.amount

    total_holding = sum(max(0, h) for h in product_holdings.values())

    # 计算加权平均保有系数
    total_weighted_coeff = 0
    for pid, holding in product_holdings.items():
        if holding > 0:
            product = PrivateFundProduct.get_by_id(pid)
            if product:
                total_weighted_coeff += holding * (product.holding_coefficient or 1.0)

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
    transactions = PrivateFundTransaction.get_all()

    # 计算各产品保有量
    product_stats = {}
    for t in transactions:
        if t.product_id not in product_stats:
            product_stats[t.product_id] = {
                "holding": 0,
                "product_name": t.product_name
            }
        if t.transaction_type == 'sale':
            product_stats[t.product_id]["holding"] += t.amount
        else:
            product_stats[t.product_id]["holding"] -= t.amount

    # 组装返回数据
    result = []
    for pid, stats in product_stats.items():
        if stats["holding"] > 0:
            product = PrivateFundProduct.get_by_id(pid)
            if product:
                holding = max(0, stats["holding"])
                result.append({
                    "product_id": pid,
                    "product_name": product.name,
                    "strategy_type": product.strategy_type,
                    "risk_level": product.risk_level,
                    "manager": product.manager,
                    "holding_amount": round(holding, 2),
                    "holding_coefficient": product.holding_coefficient or 1.0,
                    "assessed_holding": round(holding * (product.holding_coefficient or 1.0), 2)
                })

    return sorted(result, key=lambda x: x["assessed_holding"], reverse=True)


@router.get("/holdings/trend")
def get_holding_trend(period: str = "week", db: Session = Depends(get_db)):
    """获取保有量趋势数据"""
    # 生成模拟数据，实际应该根据period查询数据库
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
