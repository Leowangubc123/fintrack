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
    year_start = today.replace(month=1, day=1)

    # 在售产品数
    active_products = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).count()

    # 本年度已发售重点产品数（含已归档）
    year_products = db.query(Product).filter(
        Product.start_date >= year_start
    ).count()

    # 本年度销售额：本年度发售的所有产品的累积销售额总和（含已归档）
    year_product_ids = db.query(Product.id).filter(
        Product.start_date >= year_start
    ).subquery()

    total_sales = db.query(func.sum(SalesRecord.amount)).filter(
        SalesRecord.product_id.in_(year_product_ids)
    ).scalar() or 0

    # 整体目标（含已归档产品）
    total_target = db.query(func.sum(Product.total_target)).scalar() or 0

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
        "year_products": year_products,
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
    """获取在售产品明细，按募集期开始日期排序（最近的在前）"""
    today = date.today()
    products = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).order_by(Product.start_date.desc()).all()

    product_ids = [p.id for p in products]

    # 一次性查询所有产品的销售额和分配人数
    sales_summary = {}
    if product_ids:
        sales_rows = db.query(
            SalesRecord.product_id,
            func.sum(SalesRecord.amount).label('total_sales'),
            func.count(SalesRecord.member_id.distinct()).label('assigned_count')
        ).filter(
            SalesRecord.product_id.in_(product_ids)
        ).group_by(SalesRecord.product_id).all()
        sales_summary = {r.product_id: r for r in sales_rows}

    # 一次性查询所有产品的营业部销售分布
    group_stats_map = {}
    if product_ids:
        group_rows = db.query(
            SalesRecord.product_id,
            Group.name,
            func.sum(SalesRecord.amount).label('sales')
        ).join(
            Group, SalesRecord.group_id == Group.id
        ).filter(
            SalesRecord.product_id.in_(product_ids)
        ).group_by(SalesRecord.product_id, Group.id).all()
        for pid, gname, sales in group_rows:
            group_stats_map.setdefault(pid, []).append({"name": gname, "sales": float(sales)})

    result = []
    for product in products:
        sales_row = sales_summary.get(product.id)
        total_sales = float(sales_row.total_sales) if sales_row else 0
        assigned_count = sales_row.assigned_count if sales_row else 0
        days_left = (product.end_date - today).days

        result.append({
            "id": product.id,
            "name": product.name,
            "code": product.code,
            "type": product.type,
            "target": float(product.total_target),
            "sales": total_sales,
            "completion_rate": round(total_sales / float(product.total_target) * 100, 1) if product.total_target > 0 else 0,
            "days_left": days_left,
            "start_date": product.start_date.isoformat() if product.start_date else None,
            "group_stats": group_stats_map.get(product.id, [])
        })

    return result


@router.get("/groups-ranking")
def get_groups_ranking(product_id: int = None, db: Session = Depends(get_db)):
    """获取营业部排名，支持按产品筛选"""
    from app.models import ProductTarget

    groups = db.query(Group).all()
    group_ids = [g.id for g in groups]

    # 一次性查询所有营业部目标
    target_rows = db.query(
        ProductTarget.group_id,
        func.sum(ProductTarget.target_amount).label('target')
    ).filter(
        ProductTarget.member_id == None,
        ProductTarget.group_id.in_(group_ids)
    )
    if product_id:
        target_rows = target_rows.filter(ProductTarget.product_id == product_id)
    target_rows = target_rows.group_by(ProductTarget.group_id).all()
    target_map = {r.group_id: float(r.target) for r in target_rows}

    # 一次性查询所有营业部销量
    sales_rows = db.query(
        SalesRecord.group_id,
        func.sum(SalesRecord.amount).label('sales')
    ).filter(
        SalesRecord.group_id.in_(group_ids)
    )
    if product_id:
        sales_rows = sales_rows.filter(SalesRecord.product_id == product_id)
    sales_rows = sales_rows.group_by(SalesRecord.group_id).all()
    sales_map = {r.group_id: float(r.sales) for r in sales_rows}

    result = []
    for group in groups:
        target = target_map.get(group.id, 0)
        sales = sales_map.get(group.id, 0)
        completion_rate = (sales / target * 100) if target > 0 else 0

        result.append({
            "id": group.id,
            "name": group.name,
            "leader": group.leader,
            "target": target,
            "sales": sales,
            "completion_rate": round(completion_rate, 1)
        })

    # 按完成率排序
    result.sort(key=lambda x: x['completion_rate'], reverse=True)

    return result


@router.get("/matrix")
def get_sales_matrix(db: Session = Depends(get_db)):
    """获取产品矩阵数据 - 按营业部统计"""
    from app.models import ProductTarget

    # 获取所有在售产品
    products = db.query(Product).filter(
        Product.status == "募集中",
        Product.is_archived == False
    ).order_by(Product.start_date).all()

    # 获取所有营业部
    groups = db.query(Group).all()
    group_ids = [g.id for g in groups]
    product_ids = [p.id for p in products]

    # 一次性查询所有营业部-产品销量矩阵
    sales_matrix = {}
    if product_ids and group_ids:
        sales_rows = db.query(
            SalesRecord.group_id,
            SalesRecord.product_id,
            func.sum(SalesRecord.amount).label('sales')
        ).filter(
            SalesRecord.group_id.in_(group_ids),
            SalesRecord.product_id.in_(product_ids)
        ).group_by(SalesRecord.group_id, SalesRecord.product_id).all()
        for r in sales_rows:
            sales_matrix[(r.group_id, r.product_id)] = float(r.sales)

    # 一次性查询所有营业部-产品目标矩阵
    target_matrix = {}
    if product_ids and group_ids:
        target_rows = db.query(
            ProductTarget.group_id,
            ProductTarget.product_id,
            func.sum(ProductTarget.target_amount).label('target')
        ).filter(
            ProductTarget.group_id.in_(group_ids),
            ProductTarget.product_id.in_(product_ids),
            ProductTarget.member_id == None
        ).group_by(ProductTarget.group_id, ProductTarget.product_id).all()
        for r in target_rows:
            target_matrix[(r.group_id, r.product_id)] = float(r.target)

    # 组装矩阵
    matrix_amount = []
    matrix_rate = []
    sales_data = []
    target_data = []

    for group in groups:
        amount_row = []
        rate_row = []
        for product in products:
            sales = sales_matrix.get((group.id, product.id), 0)
            target = target_matrix.get((group.id, product.id), 0)

            amount_row.append(sales)
            rate_row.append(round(sales / target * 100, 1) if target > 0 else 0)

            if sales > 0:
                sales_data.append({
                    'group_id': group.id,
                    'product_id': product.id,
                    'amount': sales
                })

            if target > 0:
                target_data.append({
                    'group_id': group.id,
                    'product_id': product.id,
                    'target_amount': target
                })

        matrix_amount.append(amount_row)
        matrix_rate.append(rate_row)

    return {
        "products": [{"id": p.id, "name": p.name} for p in products],
        "groups": [{"id": g.id, "name": g.name} for g in groups],
        "amount_matrix": matrix_amount,
        "rate_matrix": matrix_rate,
        "sales_data": sales_data,
        "target_data": target_data
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
