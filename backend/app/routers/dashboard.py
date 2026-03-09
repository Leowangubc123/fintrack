from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List
from app.database import get_db
from app.models import Product, SalesRecord, Group, Member

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """获取Dashboard汇总数据"""
    today = date.today()
    month_start = today.replace(day=1)

    # 在售产品数
    active_products = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).count()

    # 本月整体销售额
    total_sales = db.query(func.sum(SalesRecord.amount)).filter(
        SalesRecord.sale_date >= month_start
    ).scalar() or 0

    # 本月整体目标（简化计算，使用产品总目标）
    total_target = db.query(func.sum(Product.total_target)).filter(
        Product.is_archived == False
    ).scalar() or 0

    # 整体完成率
    completion_rate = (float(total_sales) / float(total_target) * 100) if total_target > 0 else 0

    # 近7日新增
    week_ago = today - timedelta(days=7)
    week_sales = db.query(func.sum(SalesRecord.amount)).filter(
        SalesRecord.sale_date >= week_ago
    ).scalar() or 0

    # 最近截止的产品
    nearest_product = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).order_by(Product.end_date.asc()).first()

    days_to_deadline = None
    if nearest_product:
        days_to_deadline = (nearest_product.end_date - today).days

    return {
        "active_products": active_products,
        "total_sales": float(total_sales),
        "total_target": float(total_target),
        "completion_rate": round(completion_rate, 1),
        "week_sales": float(week_sales),
        "nearest_deadline": {
            "product_name": nearest_product.name if nearest_product else None,
            "days": days_to_deadline
        }
    }


@router.get("/products")
def get_active_products_summary(db: Session = Depends(get_db)):
    """获取在售产品明细"""
    today = date.today()
    products = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).all()

    result = []
    for product in products:
        # 计算产品总销售额
        total_sales = db.query(func.sum(SalesRecord.amount)).filter(
            SalesRecord.product_id == product.id
        ).scalar() or 0

        # 各营业部完成情况
        group_stats = db.query(
            Group.name,
            func.sum(SalesRecord.amount).label('sales')
        ).join(
            SalesRecord, SalesRecord.group_id == Group.id
        ).filter(
            SalesRecord.product_id == product.id
        ).group_by(Group.id).all()

        days_left = (product.end_date - today).days

        result.append({
            "id": product.id,
            "name": product.name,
            "type": product.type,
            "target": float(product.total_target),
            "sales": float(total_sales),
            "completion_rate": round(float(total_sales) / float(product.total_target) * 100, 1) if product.total_target > 0 else 0,
            "days_left": days_left,
            "group_stats": [{"name": g.name, "sales": float(g.sales)} for g in group_stats]
        })

    return result


@router.get("/groups-ranking")
def get_groups_ranking(db: Session = Depends(get_db)):
    """获取营业部排名"""
    today = date.today()
    month_start = today.replace(day=1)

    groups = db.query(Group).all()
    result = []

    for group in groups:
        # 销售额
        sales = db.query(func.sum(SalesRecord.amount)).filter(
            SalesRecord.group_id == group.id,
            SalesRecord.sale_date >= month_start
        ).scalar() or 0

        # 目标（简化：使用产品总目标的比例）
        target = float(group.members.__len__()) * 100 if group.members else 0

        completion_rate = (float(sales) / target * 100) if target > 0 else 0

        result.append({
            "id": group.id,
            "name": group.name,
            "leader": group.leader,
            "target": target,
            "sales": float(sales),
            "completion_rate": round(completion_rate, 1)
        })

    # 按销售额排序
    result.sort(key=lambda x: x['sales'], reverse=True)

    # 添加排名
    for i, item in enumerate(result):
        item['rank'] = i + 1

    return result


@router.get("/matrix")
def get_sales_matrix(db: Session = Depends(get_db)):
    """获取产品矩阵数据"""
    # 获取所有在售产品
    products = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).order_by(Product.start_date).all()

    # 获取所有成员
    members = db.query(Member).all()

    # 构建矩阵
    matrix_amount = []
    matrix_rate = []

    for member in members:
        amount_row = []
        rate_row = []

        for product in products:
            # 销售额
            sales = db.query(func.sum(SalesRecord.amount)).filter(
                SalesRecord.member_id == member.id,
                SalesRecord.product_id == product.id
            ).scalar() or 0

            # 目标（简化：平均分配）
            member_count = db.query(Member).count()
            target = float(product.total_target) / member_count if member_count > 0 else 0

            amount_row.append(float(sales))
            rate_row.append(round(float(sales) / target * 100, 1) if target > 0 else 0)

        matrix_amount.append(amount_row)
        matrix_rate.append(rate_row)

    return {
        "products": [{"id": p.id, "name": p.name} for p in products],
        "members": [
            {
                "id": m.id,
                "name": m.name,
                "group_name": m.group.name if m.group else ""
            }
            for m in members
        ],
        "amount_matrix": matrix_amount,
        "rate_matrix": matrix_rate
    }


@router.get("/large-orders")
def get_large_orders(min_amount: float = 50, db: Session = Depends(get_db)):
    """获取大单数据（≥50万）"""
    today = date.today()

    # 获取在售产品ID列表
    active_products = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).all()
    active_product_ids = [p.id for p in active_products]

    if not active_product_ids:
        return []

    # 查询大单记录（关联在售产品）
    large_orders = db.query(
        SalesRecord,
        Product.name.label('product_name'),
        Member.name.label('member_name'),
        Group.name.label('group_name')
    ).join(
        Product, SalesRecord.product_id == Product.id
    ).join(
        Member, SalesRecord.member_id == Member.id
    ).join(
        Group, SalesRecord.group_id == Group.id
    ).filter(
        SalesRecord.product_id.in_(active_product_ids),
        SalesRecord.amount >= min_amount
    ).order_by(
        SalesRecord.sale_date.desc()
    ).limit(10).all()

    result = []
    for order, product_name, member_name, group_name in large_orders:
        result.append({
            "id": order.id,
            "product_name": product_name,
            "member_name": member_name,
            "group_name": group_name,
            "amount": float(order.amount),
            "sale_date": order.sale_date.isoformat()
        })

    return result
