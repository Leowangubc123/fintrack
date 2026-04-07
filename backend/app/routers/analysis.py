from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models import SalesRecord, Product, Member, Group, ProductTarget

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/member-sales")
def get_member_sales(
    member_id: Optional[int] = None,
    group_id: Optional[int] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取成员产品销售统计"""
    query = db.query(
        SalesRecord.member_id,
        SalesRecord.product_id,
        func.sum(SalesRecord.amount).label('total_amount'),
        func.count(SalesRecord.id).label('record_count')
    ).group_by(SalesRecord.member_id, SalesRecord.product_id)

    if member_id:
        query = query.filter(SalesRecord.member_id == member_id)
    if group_id:
        query = query.filter(SalesRecord.group_id == group_id)
    if product_id:
        query = query.filter(SalesRecord.product_id == product_id)

    results = query.all()

    return [
        {
            "member_id": r.member_id,
            "product_id": r.product_id,
            "total_amount": float(r.total_amount),
            "record_count": r.record_count
        }
        for r in results
    ]


@router.get("/group-sales")
def get_group_sales(
    group_id: Optional[int] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取营业部产品销售统计"""
    query = db.query(
        SalesRecord.group_id,
        SalesRecord.product_id,
        func.sum(SalesRecord.amount).label('total_amount'),
        func.count(SalesRecord.id).label('record_count')
    ).group_by(SalesRecord.group_id, SalesRecord.product_id)

    if group_id:
        query = query.filter(SalesRecord.group_id == group_id)
    if product_id:
        query = query.filter(SalesRecord.product_id == product_id)

    results = query.all()

    return [
        {
            "group_id": r.group_id,
            "product_id": r.product_id,
            "total_amount": float(r.total_amount),
            "record_count": r.record_count
        }
        for r in results
    ]


@router.get("/member-summary/{member_id}")
def get_member_summary(member_id: int, db: Session = Depends(get_db)):
    """获取个人销售汇总统计"""
    # 总销售额
    total_sales = db.query(func.sum(SalesRecord.amount)).filter(
        SalesRecord.member_id == member_id
    ).scalar() or 0

    # 销售记录数
    record_count = db.query(SalesRecord).filter(
        SalesRecord.member_id == member_id
    ).count()

    # 获取成员信息
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")

    # 获取该成员的任务目标（从ProductTarget表）
    targets = db.query(
        ProductTarget.product_id,
        ProductTarget.target_amount
    ).filter(
        ProductTarget.member_id == member_id
    ).all()

    # 产品数量 = 有任务分配的产品数量
    product_count = len(targets)

    # 计算平均销售额 = 总销售额 / 有任务分配的产品数量
    avg_sales = float(total_sales) / product_count if product_count > 0 else 0

    target_list = [
        {
            "product_id": t.product_id,
            "target": float(t.target_amount)
        }
        for t in targets
    ]

    return {
        "member_id": member_id,
        "member_name": member.name,
        "total_sales": float(total_sales),
        "product_count": product_count,
        "record_count": record_count,
        "avg_sales": avg_sales,
        "targets": target_list
    }


@router.get("/group-comparison")
def get_group_comparison(
    time_range: str = "month",  # month, quarter, year
    db: Session = Depends(get_db)
):
    """获取营业部对比数据，支持时间维度筛选"""
    from sqlalchemy import extract

    today = date.today()

    # 根据时间范围确定起始日期
    if time_range == "month":
        start_date = today.replace(day=1)
    elif time_range == "quarter":
        quarter = (today.month - 1) // 3
        start_date = today.replace(month=quarter * 3 + 1, day=1)
    else:  # year
        start_date = today.replace(month=1, day=1)

    groups = db.query(Group).all()
    members = db.query(Member).all()

    # 获取所有有目标分配的产品ID（不限制在售状态）
    product_ids_with_target = db.query(ProductTarget.product_id).filter(
        ProductTarget.member_id == None
    ).distinct().subquery()

    result = []
    for group in groups:
        # 该营业部的成员
        group_members = [m for m in members if m.group_id == group.id]
        member_ids = [m.id for m in group_members]

        # 该营业部在有目标分配的产品上的总目标
        target = db.query(func.sum(ProductTarget.target_amount)).filter(
            ProductTarget.group_id == group.id,
            ProductTarget.member_id == None
        ).scalar() or 0

        # 该营业部成员的总销量（通过 member_id 查询，避免 group_id 不一致问题）
        total_sales = db.query(func.sum(SalesRecord.amount)).filter(
            SalesRecord.member_id.in_(member_ids),
            SalesRecord.sale_date >= start_date
        ).scalar() or 0 if member_ids else 0

        # 完成率
        if target > 0:
            completion_rate = (float(total_sales) / float(target) * 100)
        else:
            completion_rate = 0

        # 人均销售额
        per_capita = float(total_sales) / len(group_members) if group_members else 0

        # 计算与上月对比的趋势
        if time_range == "month":
            last_month_start = (start_date.replace(day=1) - __import__('datetime').timedelta(days=1)).replace(day=1)
            last_month_end = start_date - __import__('datetime').timedelta(days=1)
            last_month_sales = db.query(func.sum(SalesRecord.amount)).filter(
                SalesRecord.group_id == group.id,
                SalesRecord.sale_date >= last_month_start,
                SalesRecord.sale_date <= last_month_end
            ).scalar() or 0

            if last_month_sales > 0:
                trend = round((float(total_sales) - float(last_month_sales)) / float(last_month_sales) * 100, 1)
            else:
                trend = 100 if total_sales > 0 else 0
        else:
            trend = 0

        result.append({
            "id": group.id,
            "name": group.name,
            "leader": group.leader,
            "member_count": len(group_members),
            "target": float(target),
            "sales": float(total_sales),
            "completion_rate": round(completion_rate, 1),
            "per_capita": round(per_capita, 1),
            "trend": trend
        })

    # 按总销售额排序
    result.sort(key=lambda x: x["sales"], reverse=True)

    return result


@router.get("/group-trend")
def get_group_trend(
    months: int = 6,
    db: Session = Depends(get_db)
):
    """获取各营业部的完成率历史趋势"""
    from sqlalchemy import extract
    from datetime import timedelta

    today = date.today()
    groups = db.query(Group).all()

    # 生成最近N个月的月份列表
    month_list = []
    for i in range(months - 1, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        month_list.append((d.year, d.month))

    result = {}
    for group in groups:
        trend = []
        for year, month in month_list:
            # 该月销售额
            sales = db.query(func.sum(SalesRecord.amount)).filter(
                SalesRecord.group_id == group.id,
                extract('year', SalesRecord.sale_date) == year,
                extract('month', SalesRecord.sale_date) == month
            ).scalar() or 0

            # 目标（暂时使用总目标，可以优化为按时间加权）
            target = db.query(func.sum(ProductTarget.target_amount)).filter(
                ProductTarget.group_id == group.id
            ).scalar() or 0

            # 按月分配目标
            monthly_target = float(target) / 12
            completion_rate = (float(sales) / monthly_target * 100) if monthly_target > 0 else 0

            trend.append({
                "year": year,
                "month": month,
                "label": f"{year}年{month}月",
                "sales": round(float(sales), 2),
                "completion_rate": round(completion_rate, 1)
            })

        result[group.id] = {
            "group_name": group.name,
            "trend": trend
        }

    return result


@router.get("/group-members/{group_id}")
def get_group_members_detail(
    group_id: int,
    time_range: str = "month",
    db: Session = Depends(get_db)
):
    """获取营业部成员明细"""
    from sqlalchemy import extract

    today = date.today()

    # 根据时间范围确定起始日期
    if time_range == "month":
        start_date = today.replace(day=1)
    elif time_range == "quarter":
        quarter = (today.month - 1) // 3
        start_date = today.replace(month=quarter * 3 + 1, day=1)
    else:  # year
        start_date = today.replace(month=1, day=1)

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="营业部不存在")

    members = db.query(Member).filter(Member.group_id == group_id).all()

    result = []
    for member in members:
        # 该成员在指定时间范围内的销售额
        total_sales = db.query(func.sum(SalesRecord.amount)).filter(
            SalesRecord.member_id == member.id,
            SalesRecord.sale_date >= start_date
        ).scalar() or 0

        # 该成员的目标
        target = db.query(func.sum(ProductTarget.target_amount)).filter(
            ProductTarget.member_id == member.id
        ).scalar() or 0

        # 完成率
        completion_rate = (float(total_sales) / float(target) * 100) if target > 0 else 0

        # 销售记录数
        record_count = db.query(SalesRecord).filter(
            SalesRecord.member_id == member.id,
            SalesRecord.sale_date >= start_date
        ).count()

        result.append({
            "id": member.id,
            "name": member.name,
            "target": float(target),
            "sales": float(total_sales),
            "completion_rate": round(completion_rate, 1),
            "record_count": record_count
        })

    # 按完成率排序
    result.sort(key=lambda x: x["completion_rate"], reverse=True)

    return {
        "group_id": group_id,
        "group_name": group.name,
        "members": result
    }


@router.get("/sales-trend")
def get_sales_trend(
    year: Optional[int] = None,
    member_id: Optional[int] = None,
    product_id: Optional[int] = None,
    group_by: str = "month",  # month 或 week
    db: Session = Depends(get_db)
):
    """获取销售趋势，支持按月度/周度聚合，支持按成员/产品筛选"""
    from sqlalchemy import extract

    if not year:
        year = date.today().year

    # 构建基础查询
    query = db.query(
        SalesRecord.sale_date,
        func.sum(SalesRecord.amount).label('total_amount')
    ).filter(
        extract('year', SalesRecord.sale_date) == year
    )

    if member_id:
        query = query.filter(SalesRecord.member_id == member_id)
    if product_id:
        query = query.filter(SalesRecord.product_id == product_id)

    results = query.group_by(SalesRecord.sale_date).all()

    # 按日期聚合结果
    date_amounts = {}
    for r in results:
        d = r.sale_date
        if d not in date_amounts:
            date_amounts[d] = 0
        date_amounts[d] += float(r.total_amount)

    # 按月度聚合
    if group_by == "month":
        monthly_data = {}
        for d, amount in date_amounts.items():
            month = d.month
            if month not in monthly_data:
                monthly_data[month] = 0
            monthly_data[month] += amount

        trend = []
        for month in range(1, 13):
            amount = monthly_data.get(month, 0)

            # 根据金额确定等级（用于热力图颜色）与图例保持一致
            # level-0: 0, level-1: 1-10万, level-2: 10-20万, level-3: 20-40万, level-4: 40万+
            if amount >= 40:
                level = 4
            elif amount >= 20:
                level = 3
            elif amount >= 10:
                level = 2
            elif amount > 0:
                level = 1
            else:
                level = 0

            trend.append({
                "month": month,
                "label": f"{month}月",
                "amount": round(amount, 2),
                "level": level
            })
    # 按周度聚合
    else:
        from datetime import timedelta
        # 找出该年的所有日期
        year_dates = [d for d in date_amounts.keys()]
        if year_dates:
            min_date = min(year_dates)
            max_date = max(year_dates)
        else:
            min_date = date(year, 1, 1)
            max_date = date(year, 12, 31)

        # 计算周次
        weekly_data = {}
        for d, amount in date_amounts.items():
            # 计算该日期是当年的第几周
            week = d.isocalendar()[1]
            if week not in weekly_data:
                weekly_data[week] = 0
            weekly_data[week] += amount

        # 找出该年所有的周
        all_weeks = set()
        current = date(year, 1, 1)
        while current.year == year:
            all_weeks.add(current.isocalendar()[1])
            current += timedelta(days=1)

        trend = []
        for week in sorted(all_weeks):
            amount = weekly_data.get(week, 0)

            # 根据金额确定等级（用于热力图颜色）与图例保持一致
            # level-0: 0, level-1: 1-10万, level-2: 10-20万, level-3: 20-40万, level-4: 40万+
            if amount >= 40:
                level = 4
            elif amount >= 20:
                level = 3
            elif amount >= 10:
                level = 2
            elif amount > 0:
                level = 1
            else:
                level = 0

            trend.append({
                "week": week,
                "label": f"第{week}周",
                "amount": round(amount, 2),
                "level": level
            })

    return trend


@router.get("/sales-trend/stats")
def get_sales_trend_stats(
    year: Optional[int] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取销售趋势统计指标（最高日销售额、平均日销售额、同比、环比）"""
    from sqlalchemy import extract

    today = date.today()
    if not year:
        year = today.year

    # 构建基础查询条件
    def get_sales_query(target_year, target_month=None):
        query = db.query(
            SalesRecord.sale_date,
            func.sum(SalesRecord.amount).label('total_amount')
        ).filter(
            extract('year', SalesRecord.sale_date) == target_year
        )
        if target_month:
            query = query.filter(extract('month', SalesRecord.sale_date) == target_month)
        if product_id:
            query = query.filter(SalesRecord.product_id == product_id)
        return query.group_by(SalesRecord.sale_date)

    # 1. 本年度数据
    current_year_results = get_sales_query(year).all()
    current_year_daily = {r.sale_date: float(r.total_amount) for r in current_year_results}

    # 2. 去年同期数据（用于同比）
    last_year = year - 1
    last_year_results = get_sales_query(last_year).all()
    last_year_total = sum(float(r.total_amount) for r in last_year_results)

    # 3. 本月vs上月数据（用于环比）
    current_month = today.month if year == today.year else 12
    current_month_results = get_sales_query(year, current_month).all()
    current_month_total = sum(float(r.total_amount) for r in current_month_results)

    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = year if current_month > 1 else year - 1
    last_month_results = get_sales_query(last_month_year, last_month).all()
    last_month_total = sum(float(r.total_amount) for r in last_month_results)

    # 计算指标
    if current_year_daily:
        max_daily = max(current_year_daily.values())
        max_daily_date = max(current_year_daily.keys(), key=lambda k: current_year_daily[k])
        avg_daily = sum(current_year_daily.values()) / len(current_year_daily)
    else:
        max_daily = 0
        max_daily_date = None
        avg_daily = 0

    current_year_total = sum(current_year_daily.values())

    # 同比 = (今年-去年)/去年 * 100%
    if last_year_total > 0:
        yoy_growth = round((current_year_total - last_year_total) / last_year_total * 100, 1)
    else:
        yoy_growth = 0 if current_year_total == 0 else 100

    # 环比 = (本月-上月)/上月 * 100%
    if last_month_total > 0:
        mom_growth = round((current_month_total - last_month_total) / last_month_total * 100, 1)
    else:
        mom_growth = 0 if current_month_total == 0 else 100

    return {
        "max_daily": round(max_daily, 2),
        "max_daily_date": max_daily_date.isoformat() if max_daily_date else None,
        "avg_daily": round(avg_daily, 2),
        "yoy_growth": yoy_growth,  # 同比
        "mom_growth": mom_growth,   # 环比
        "current_year_total": round(current_year_total, 2)
    }


@router.get("/product-contribution")
def get_product_contribution(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取产品贡献度（各产品销售额占比）"""
    from sqlalchemy import extract

    if not year:
        year = date.today().year

    # 查询各产品的销售额
    results = db.query(
        SalesRecord.product_id,
        Product.name,
        func.sum(SalesRecord.amount).label('total_amount')
    ).join(
        Product, SalesRecord.product_id == Product.id
    ).filter(
        extract('year', SalesRecord.sale_date) == year
    ).group_by(
        SalesRecord.product_id,
        Product.name
    ).all()

    total_sales = sum(float(r.total_amount) for r in results)

    contribution = []
    for r in results:
        amount = float(r.total_amount)
        percentage = round(amount / total_sales * 100, 2) if total_sales > 0 else 0
        contribution.append({
            "product_id": r.product_id,
            "product_name": r.name,
            "amount": round(amount, 2),
            "percentage": percentage
        })

    # 按销售额降序排列
    contribution.sort(key=lambda x: x["amount"], reverse=True)

    return {
        "total_sales": round(total_sales, 2),
        "contribution": contribution
    }


@router.get("/matrix")
def get_analysis_matrix(db: Session = Depends(get_db)):
    """获取产品矩阵数据"""
    # 获取所有产品（包括已结束的，以便统计历史数据）
    products = db.query(Product).all()

    # 获取所有营业部和成员
    groups = db.query(Group).all()
    members = db.query(Member).all()

    # 获取所有销售记录统计（成员级别）
    sales_stats = db.query(
        SalesRecord.member_id,
        SalesRecord.product_id,
        func.sum(SalesRecord.amount).label('total_amount')
    ).group_by(SalesRecord.member_id, SalesRecord.product_id).all()

    # 构建销售数据列表（可序列化为JSON）- 成员级别
    sales_data = []
    for stat in sales_stats:
        sales_data.append({
            "member_id": stat.member_id,
            "product_id": stat.product_id,
            "amount": float(stat.total_amount)
        })

    # 获取所有成员的任务目标数据
    targets = db.query(ProductTarget).filter(
        ProductTarget.member_id != None
    ).all()

    # 构建任务目标数据列表 - 成员级别
    target_data = []
    for target in targets:
        target_data.append({
            "member_id": target.member_id,
            "product_id": target.product_id,
            "target_amount": float(target.target_amount)
        })

    # 构建营业部级别销售数据（汇总该营业部所有成员的销量）
    group_sales_data = []
    for group in groups:
        group_member_ids = [m.id for m in members if m.group_id == group.id]
        for product in products:
            # 汇总该营业部所有成员在该产品上的销量
            total_sales = db.query(func.sum(SalesRecord.amount)).filter(
                SalesRecord.member_id.in_(group_member_ids),
                SalesRecord.product_id == product.id
            ).scalar() or 0

            if total_sales > 0:
                group_sales_data.append({
                    "group_id": group.id,
                    "product_id": product.id,
                    "amount": float(total_sales)
                })

    # 构建营业部级别任务目标数据（取营业部层面的任务分配）
    group_target_data = []
    for group in groups:
        for product in products:
            # 获取该营业部在该产品上的营业部级别任务目标（member_id IS NULL）
            total_target = db.query(func.sum(ProductTarget.target_amount)).filter(
                ProductTarget.group_id == group.id,
                ProductTarget.product_id == product.id,
                ProductTarget.member_id == None  # 只取营业部级别的任务
            ).scalar() or 0

            if total_target > 0:
                group_target_data.append({
                    "group_id": group.id,
                    "product_id": product.id,
                    "target_amount": float(total_target)
                })

    # 按募集期开始日期排序（较早的排在前面）
    sorted_products = sorted(products, key=lambda p: p.start_date or date.min)

    return {
        "products": [{"id": p.id, "name": p.name, "start_date": p.start_date.isoformat() if p.start_date else None} for p in sorted_products],
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "members": [
                    {"id": m.id, "name": m.name}
                    for m in members if m.group_id == g.id
                ]
            }
            for g in groups
        ],
        "sales_data": sales_data,
        "target_data": target_data,
        "group_sales_data": group_sales_data,
        "group_target_data": group_target_data
    }
