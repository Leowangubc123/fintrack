from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from collections import defaultdict

from app.database import get_db
from app.models import Member, Group, InvestmentAdvisorySubscription, InvestmentAdvisoryTarget, AdvisoryImportLog

router = APIRouter(prefix="/api/advisory", tags=["advisory"])

# ============== Pydantic 数据模型 ==============

class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    member_name: str
    group_id: int
    group_name: str
    product_type: str
    subscription_date: date
    asset_amount: float
    advisory_income: float
    original_households: int
    converted_households: int
    conversion_note: Optional[str] = None
    record_date: date
    created_at: Optional[datetime] = None


class SubscriptionUpdateRequest(BaseModel):
    converted_households: int
    conversion_note: Optional[str] = None


class SubscriptionImportItem(BaseModel):
    member_name: str
    group_name: str
    product_type: str
    subscription_date: date
    asset_amount: float
    advisory_income: float = 0
    order_status: str = "支付成功"


class IncomeImportItem(BaseModel):
    group_name: str
    advisory_income: float


class SubscriptionImportRequest(BaseModel):
    record_date: date
    product_type: str  # '万2', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT', '投顾收入'
    data: List[dict]


class SubscriptionImportResponse(BaseModel):
    success_count: int
    error_count: int
    errors: List[str]
    log_id: Optional[int] = None


class ImportLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    import_date: date
    product_type: str
    record_count: int
    success_count: int
    error_count: int
    operator: str
    created_at: Optional[datetime] = None


class StatsResponse(BaseModel):
    total_households: int
    total_assets: float
    total_income: float
    households_change: int
    assets_change: float
    income_change: float
    product_distribution: List[dict]
    trend_data: List[dict]
    last_update_date: Optional[date] = None


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    group_name: str
    year: int
    income_target: float
    households_target: int
    assessed_households: int
    current_income: float
    current_households: int
    income_completion_rate: float
    households_completion_rate: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TargetCreateRequest(BaseModel):
    group_id: int
    year: int
    income_target: float
    households_target: int
    assessed_households: int = 0


# ============== 统计数据API ==============

@router.get("/stats", response_model=StatsResponse)
def get_stats(
    year: Optional[int] = None,
    group_id: Optional[int] = None,
    member_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取投顾业务统计数据"""
    if not year:
        year = date.today().year

    # 基础查询 - 按年份过滤（通过record_date）
    base_query = db.query(InvestmentAdvisorySubscription).filter(
        extract('year', InvestmentAdvisorySubscription.record_date) == year
    )

    if group_id:
        base_query = base_query.filter(InvestmentAdvisorySubscription.group_id == group_id)
    if member_id:
        base_query = base_query.filter(InvestmentAdvisorySubscription.member_id == member_id)

    subscriptions = base_query.all()

    # 计算总户数、总资产、总收入（资产转换为万元）
    total_households = sum(s.converted_households for s in subscriptions)
    total_assets = sum(float(s.asset_amount) for s in subscriptions) / 10000
    total_income = sum(float(s.advisory_income) for s in subscriptions)

    # 产品分布统计
    product_stats = defaultdict(lambda: {"count": 0, "assets": 0.0, "income": 0.0})
    for s in subscriptions:
        pt = s.product_type
        if pt == '万2':
            pt = '万2及其他'
        product_stats[pt]["count"] += s.converted_households
        product_stats[pt]["assets"] += float(s.asset_amount) / 10000
        product_stats[pt]["income"] += float(s.advisory_income)

    product_distribution = [
        {
            "product_type": pt,
            "households": stats["count"],
            "assets": round(stats["assets"], 2),
            "income": round(stats["income"], 2)
        }
        for pt, stats in sorted(product_stats.items(), key=lambda x: x[1]["assets"], reverse=True)
    ]

    # 趋势数据（按月统计，基于subscription_date）
    trend_query = db.query(
        extract('month', InvestmentAdvisorySubscription.subscription_date).label('month'),
        func.sum(InvestmentAdvisorySubscription.asset_amount).label('total_assets'),
        func.sum(InvestmentAdvisorySubscription.advisory_income).label('total_income'),
        func.sum(InvestmentAdvisorySubscription.converted_households).label('total_households')
    ).filter(
        extract('year', InvestmentAdvisorySubscription.record_date) == year,
        InvestmentAdvisorySubscription.subscription_date != None
    )

    if group_id:
        trend_query = trend_query.filter(InvestmentAdvisorySubscription.group_id == group_id)
    if member_id:
        trend_query = trend_query.filter(InvestmentAdvisorySubscription.member_id == member_id)

    trend_results = trend_query.group_by('month').order_by('month').all()

    trend_data = [
        {
            "month": int(r.month),
            "assets": round(float(r.total_assets) / 10000, 2) if r.total_assets else 0,
            "income": round(float(r.total_income), 2) if r.total_income else 0,
            "households": int(r.total_households) if r.total_households else 0
        }
        for r in trend_results
    ]

    # 最后更新日期
    last_update_date = db.query(
        func.max(InvestmentAdvisorySubscription.record_date)
    ).filter(extract('year', InvestmentAdvisorySubscription.record_date) == year).scalar()

    # 计算较上次更新变化
    record_dates = db.query(
        InvestmentAdvisorySubscription.record_date
    ).filter(
        extract('year', InvestmentAdvisorySubscription.record_date) == year
    )
    if group_id:
        record_dates = record_dates.filter(InvestmentAdvisorySubscription.group_id == group_id)
    if member_id:
        record_dates = record_dates.filter(InvestmentAdvisorySubscription.member_id == member_id)

    distinct_dates = [r[0] for r in record_dates.distinct().order_by(InvestmentAdvisorySubscription.record_date.desc()).all()]

    households_change = 0
    assets_change = 0.0
    income_change = 0.0

    if len(distinct_dates) >= 2:
        current_date = distinct_dates[0]
        previous_date = distinct_dates[1]

        def calc_date_stats(target_date):
            q = db.query(InvestmentAdvisorySubscription).filter(
                InvestmentAdvisorySubscription.record_date == target_date,
                extract('year', InvestmentAdvisorySubscription.record_date) == year
            )
            if group_id:
                q = q.filter(InvestmentAdvisorySubscription.group_id == group_id)
            if member_id:
                q = q.filter(InvestmentAdvisorySubscription.member_id == member_id)
            subs = q.all()
            h = sum(s.converted_households for s in subs)
            a = sum(float(s.asset_amount) for s in subs) / 10000
            i = sum(float(s.advisory_income) for s in subs)
            return h, a, i

        curr_h, curr_a, curr_i = calc_date_stats(current_date)
        prev_h, prev_a, prev_i = calc_date_stats(previous_date)

        households_change = curr_h - prev_h
        assets_change = round(curr_a - prev_a, 2)
        income_change = round(curr_i - prev_i, 2)

    return StatsResponse(
        total_households=total_households,
        total_assets=round(total_assets, 2),
        total_income=round(total_income, 2),
        households_change=households_change,
        assets_change=assets_change,
        income_change=income_change,
        product_distribution=product_distribution,
        trend_data=trend_data,
        last_update_date=last_update_date
    )


# ============== 签约明细API ==============

class SubscriptionListResponse(BaseModel):
    items: List[SubscriptionResponse]
    total: int


@router.get("/subscriptions", response_model=SubscriptionListResponse)
def get_subscriptions(
    year: Optional[int] = None,
    group_id: Optional[int] = None,
    member_id: Optional[int] = None,
    product_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """获取签约明细列表（分页）"""
    if not year:
        year = date.today().year

    query = db.query(
        InvestmentAdvisorySubscription,
        Member.name.label("member_name"),
        Group.name.label("group_name")
    ).join(
        Member, InvestmentAdvisorySubscription.member_id == Member.id
    ).join(
        Group, InvestmentAdvisorySubscription.group_id == Group.id
    ).filter(extract('year', InvestmentAdvisorySubscription.record_date) == year)

    if group_id:
        query = query.filter(InvestmentAdvisorySubscription.group_id == group_id)
    if member_id:
        query = query.filter(InvestmentAdvisorySubscription.member_id == member_id)
    if product_type:
        query = query.filter(InvestmentAdvisorySubscription.product_type == product_type)

    # 分页
    total = query.count()
    results = query.order_by(InvestmentAdvisorySubscription.record_date.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = [
        SubscriptionResponse(
            id=s.InvestmentAdvisorySubscription.id,
            member_id=s.InvestmentAdvisorySubscription.member_id,
            member_name=s.member_name,
            group_id=s.InvestmentAdvisorySubscription.group_id,
            group_name=s.group_name,
            product_type=s.InvestmentAdvisorySubscription.product_type,
            subscription_date=s.InvestmentAdvisorySubscription.subscription_date,
            asset_amount=float(s.InvestmentAdvisorySubscription.asset_amount),
            advisory_income=float(s.InvestmentAdvisorySubscription.advisory_income),
            original_households=s.InvestmentAdvisorySubscription.original_households,
            converted_households=s.InvestmentAdvisorySubscription.converted_households,
            conversion_note=s.InvestmentAdvisorySubscription.conversion_note,
            record_date=s.InvestmentAdvisorySubscription.record_date,
            created_at=s.InvestmentAdvisorySubscription.created_at
        )
        for s in results
    ]

    return SubscriptionListResponse(items=items, total=total)


@router.post("/subscriptions/import", response_model=SubscriptionImportResponse)
def import_subscriptions(
    request: SubscriptionImportRequest,
    operator: str = "admin",
    db: Session = Depends(get_db)
):
    """导入签约数据（产品特定时点更新机制）

    逻辑：
    1. 如果是投顾收入类型，更新相应记录的收入字段
    2. 如果是产品类型，只删除该产品在该日期的记录，然后插入新记录
    """
    record_date = request.record_date
    product_type = request.product_type

    try:
        # 获取所有成员和营业部用于匹配
        members = db.query(Member).all()
        groups = db.query(Group).all()

        member_by_name = {m.name: m for m in members}
        group_by_name = {g.name: g for g in groups}

        success_count = 0
        errors = []

        # 验证产品类型
        valid_product_types = ['万2及其他', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT', '投顾收入']
        if product_type not in valid_product_types:
            raise HTTPException(status_code=400, detail=f"无效的产品类型: {product_type}")

        # 如果是投顾收入类型，处理方式不同
        if product_type == '投顾收入':
            # 更新各营业部的投顾收入
            for item in request.data:
                group_name = item.get('group_name') or item.get('营业部', '')
                income_value = item.get('advisory_income') or item.get('投顾收入', 0)

                if not group_name:
                    errors.append(f"缺少营业部信息")
                    continue

                group = group_by_name.get(group_name)
                if not group:
                    errors.append(f"未找到营业部: {group_name}")
                    continue

                # 将元转换为万元
                try:
                    income_yuan = float(income_value)
                    income_wan = income_yuan / 10000
                except (ValueError, TypeError):
                    errors.append(f"无效的收入金额: {income_value} (营业部: {group_name})")
                    continue

                # 更新该营业部该日期的所有记录的收入
                db.query(InvestmentAdvisorySubscription).filter(
                    InvestmentAdvisorySubscription.group_id == group.id,
                    InvestmentAdvisorySubscription.record_date == record_date
                ).update({
                    'advisory_income': Decimal(str(income_yuan))
                })

                success_count += 1

        else:
            # 1. 只删除该日期该产品类型的记录（而不是全部）
            deleted = db.query(InvestmentAdvisorySubscription).filter(
                InvestmentAdvisorySubscription.record_date == record_date,
                InvestmentAdvisorySubscription.product_type == product_type
            ).delete()

            # 2. 插入新产品数据
            for item in request.data:
                # 提取字段（支持多种表头命名）
                group_name = item.get('group_name') or item.get('营业部', '')
                member_name = item.get('member_name') or item.get('认领员工', '')
                subscription_date_str = item.get('subscription_date') or item.get('订购日期', '')
                asset_amount = item.get('asset_amount') or item.get('昨日净资产', 0)
                order_status = item.get('order_status') or item.get('订单状态', '支付成功')

                # 检查订单状态
                if product_type == '量化T策略':
                    if '取消' in str(order_status) or '退订' in str(order_status):
                        continue  # 跳过取消/退订订单
                else:
                    valid_statuses = ['支付成功', '已支付', '成功', '正常', '有效', '已成交', '确认', '完成']
                    if not any(s in str(order_status) for s in valid_statuses):
                        continue  # 跳过非成功订单

                # 验证必填字段
                if not member_name:
                    errors.append(f"第 {success_count + len(errors) + 1} 行: 缺少认领员工信息")
                    continue

                if not group_name:
                    errors.append(f"第 {success_count + len(errors) + 1} 行 (员工: {member_name}): 缺少营业部信息")
                    continue

                # 查找成员
                member = member_by_name.get(member_name)
                if not member:
                    errors.append(f"未找到员工: {member_name}，请先在营销人员中录入")
                    continue

                # 查找营业部
                group = group_by_name.get(group_name)
                if not group:
                    errors.append(f"未找到营业部: {group_name}")
                    continue

                # 解析日期（格式：YYYYMMDD）
                try:
                    if isinstance(subscription_date_str, int):
                        date_str = str(subscription_date_str)
                    else:
                        date_str = str(subscription_date_str).replace('-', '').replace('/', '')

                    if len(date_str) == 8:
                        subscription_date = date(
                            int(date_str[:4]),
                            int(date_str[4:6]),
                            int(date_str[6:8])
                        )
                    else:
                        subscription_date = date.today()
                except (ValueError, TypeError):
                    errors.append(f"日期格式错误: {subscription_date_str} (员工: {member_name})")
                    continue

                # 解析资产金额
                try:
                    asset_value = float(asset_amount) if asset_amount else 0
                except (ValueError, TypeError):
                    errors.append(f"资产金额格式错误: {asset_amount} (员工: {member_name})")
                    continue

                # 创建记录
                subscription = InvestmentAdvisorySubscription(
                    member_id=member.id,
                    group_id=group.id,
                    product_type=product_type,
                    subscription_date=subscription_date,
                    asset_amount=Decimal(str(asset_value)),
                    advisory_income=Decimal('0'),  # 产品数据默认收入为0
                    original_households=1,
                    converted_households=1,
                    record_date=record_date
                )
                db.add(subscription)
                success_count += 1

        db.commit()

        # 记录导入日志
        log = AdvisoryImportLog(
            import_date=record_date,
            product_type=product_type,
            record_count=len(request.data),
            success_count=success_count,
            error_count=len(errors),
            operator=operator
        )
        db.add(log)
        db.commit()

        return SubscriptionImportResponse(
            success_count=success_count,
            error_count=len(errors),
            errors=errors[:20],  # 只返回前20个错误
            log_id=log.id
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/import-logs", response_model=List[ImportLogResponse])
def get_import_logs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取导入日志"""
    logs = db.query(AdvisoryImportLog).order_by(
        AdvisoryImportLog.created_at.desc()
    ).limit(limit).all()

    return [
        ImportLogResponse(
            id=log.id,
            import_date=log.import_date,
            product_type=log.product_type,
            record_count=log.record_count,
            success_count=log.success_count,
            error_count=log.error_count,
            operator=log.operator,
            created_at=log.created_at
        )
        for log in logs
    ]


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    request: SubscriptionUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新单条签约记录（折算户数编辑）"""
    subscription = db.query(InvestmentAdvisorySubscription).filter(
        InvestmentAdvisorySubscription.id == subscription_id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="记录不存在")

    subscription.converted_households = request.converted_households
    subscription.conversion_note = request.conversion_note

    db.commit()
    db.refresh(subscription)

    # 获取关联信息
    member = db.query(Member).filter(Member.id == subscription.member_id).first()
    group = db.query(Group).filter(Group.id == subscription.group_id).first()

    return SubscriptionResponse(
        id=subscription.id,
        member_id=subscription.member_id,
        member_name=member.name if member else "未知",
        group_id=subscription.group_id,
        group_name=group.name if group else "未知",
        product_type=subscription.product_type,
        subscription_date=subscription.subscription_date,
        asset_amount=float(subscription.asset_amount),
        advisory_income=float(subscription.advisory_income),
        original_households=subscription.original_households,
        converted_households=subscription.converted_households,
        conversion_note=subscription.conversion_note,
        record_date=subscription.record_date,
        created_at=subscription.created_at
    )


# ============== 考核指标API ==============

@router.get("/targets", response_model=List[TargetResponse])
def get_targets(
    year: Optional[int] = None,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取考核指标及完成情况"""
    if not year:
        year = date.today().year

    # 获取目标数据
    query = db.query(
        InvestmentAdvisoryTarget,
        Group.name.label("group_name")
    ).join(
        Group, InvestmentAdvisoryTarget.group_id == Group.id
    ).filter(InvestmentAdvisoryTarget.year == year)

    if group_id:
        query = query.filter(InvestmentAdvisoryTarget.group_id == group_id)

    targets = query.all()

    # 计算当前年度实际完成情况
    actual_stats = db.query(
        InvestmentAdvisorySubscription.group_id,
        func.sum(InvestmentAdvisorySubscription.advisory_income).label('total_income'),
        func.sum(InvestmentAdvisorySubscription.converted_households).label('total_households')
    ).filter(extract('year', InvestmentAdvisorySubscription.record_date) == year)

    if group_id:
        actual_stats = actual_stats.filter(InvestmentAdvisorySubscription.group_id == group_id)

    actual_stats = actual_stats.group_by(InvestmentAdvisorySubscription.group_id).all()

    # 构建实际完成数据映射
    actual_map = {
        s.group_id: {
            "income": float(s.total_income) if s.total_income else 0,
            "households": int(s.total_households) if s.total_households else 0
        }
        for s in actual_stats
    }

    result = []
    for t in targets:
        target = t.InvestmentAdvisoryTarget
        group_name = t.group_name

        current_income = actual_map.get(target.group_id, {}).get("income", 0)
        current_households = actual_map.get(target.group_id, {}).get("households", 0)

        income_target = float(target.income_target) if target.income_target else 0
        households_target = target.households_target if target.households_target else 0
        assessed_households = target.assessed_households if target.assessed_households else 0

        income_completion_rate = (current_income / income_target * 100) if income_target > 0 else 0
        households_completion_rate = (assessed_households / households_target * 100) if households_target > 0 else 0

        result.append(TargetResponse(
            id=target.id,
            group_id=target.group_id,
            group_name=group_name,
            year=target.year,
            income_target=income_target,
            households_target=households_target,
            assessed_households=assessed_households,
            current_income=round(current_income, 2),
            current_households=current_households,
            income_completion_rate=round(income_completion_rate, 2),
            households_completion_rate=round(households_completion_rate, 2),
            created_at=target.created_at,
            updated_at=target.updated_at
        ))

    return result


@router.post("/targets", response_model=TargetResponse)
def create_or_update_target(
    request: TargetCreateRequest,
    db: Session = Depends(get_db)
):
    """设置考核指标（创建或更新）"""
    # 检查营业部是否存在
    group = db.query(Group).filter(Group.id == request.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="营业部不存在")

    # 查找或创建目标记录
    target = db.query(InvestmentAdvisoryTarget).filter(
        InvestmentAdvisoryTarget.group_id == request.group_id,
        InvestmentAdvisoryTarget.year == request.year
    ).first()

    if target:
        # 更新现有记录
        target.income_target = Decimal(str(request.income_target))
        target.households_target = request.households_target
        target.assessed_households = request.assessed_households
    else:
        # 创建新记录
        target = InvestmentAdvisoryTarget(
            group_id=request.group_id,
            year=request.year,
            income_target=Decimal(str(request.income_target)),
            households_target=request.households_target,
            assessed_households=request.assessed_households
        )
        db.add(target)

    db.commit()
    db.refresh(target)

    # 计算当前完成情况
    actual_stats = db.query(
        func.sum(InvestmentAdvisorySubscription.advisory_income).label('total_income'),
        func.sum(InvestmentAdvisorySubscription.converted_households).label('total_households')
    ).filter(
        InvestmentAdvisorySubscription.group_id == request.group_id,
        extract('year', InvestmentAdvisorySubscription.record_date) == request.year
    ).first()

    current_income = float(actual_stats.total_income) if actual_stats.total_income else 0
    current_households = int(actual_stats.total_households) if actual_stats.total_households else 0

    income_completion_rate = (current_income / request.income_target * 100) if request.income_target > 0 else 0
    households_completion_rate = (request.assessed_households / request.households_target * 100) if request.households_target > 0 else 0

    return TargetResponse(
        id=target.id,
        group_id=target.group_id,
        group_name=group.name,
        year=target.year,
        income_target=request.income_target,
        households_target=request.households_target,
        assessed_households=request.assessed_households,
        current_income=round(current_income, 2),
        current_households=current_households,
        income_completion_rate=round(income_completion_rate, 2),
        households_completion_rate=round(households_completion_rate, 2),
        created_at=target.created_at,
        updated_at=target.updated_at
    )
