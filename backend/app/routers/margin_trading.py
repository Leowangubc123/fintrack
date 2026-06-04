from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, text
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from collections import defaultdict

from app.database import get_db
from app.models import Member, Group
from app.models.margin_trading import (MarginBalanceMember, MarginBalanceGroup,
                                        MarginIncome, MarginNewAccount, MarginTarget, MarginImportLog)

router = APIRouter(prefix="/api/margin-trading", tags=["margin_trading"])

# ============== Pydantic 数据模型 ==============

class ImportItem(BaseModel):
    data_type: str  # 'member_balance', 'group_balance', 'income', 'new_account'
    record_week: str
    record_date: date
    data: List[dict]


class ImportResponse(BaseModel):
    success_count: int
    error_count: int
    errors: List[str]


class MemberBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    member_name: str
    group_id: int
    group_name: str
    development_balance: float
    service_balance: float
    balance_type: str
    record_week: str
    record_date: date


class GroupBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    group_name: str
    spot_balance: float
    daily_balance: float
    record_week: str
    record_date: date


class IncomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    group_name: str
    income_amount: float
    record_week: str
    record_date: date


class NewAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    member_name: str
    group_id: int
    group_name: str
    customer_name: str
    asset_amount: float
    account_date: date
    record_week: str


class StatsResponse(BaseModel):
    spot_balance: float
    daily_balance: float
    new_account_count: int
    income_total: float
    spot_change: float
    daily_change: float
    account_change: int
    income_change: float
    last_update_date: Optional[date] = None
    group_distribution: List[dict]
    income_distribution: List[dict]
    weekly_account_trend: List[dict]
    monthly_account_trend: List[dict]


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    group_name: str
    year: int
    income_target: float
    account_target: int
    income_completion_rate: float
    account_completion_rate: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TargetCreateRequest(BaseModel):
    group_id: int
    year: int
    income_target: float = 0
    account_target: int = 0


class ImportLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    import_date: date
    data_type: str
    record_count: int
    success_count: int
    error_count: int
    operator: str
    created_at: Optional[datetime] = None


# ============== 数据导入API ==============

@router.post("/import", response_model=ImportResponse)
def import_data(
    request: ImportItem,
    operator: str = "admin",
    db: Session = Depends(get_db)
):
    """导入两融数据（全量覆盖当周数据）"""
    record_week = request.record_week
    record_date = request.record_date
    data_type = request.data_type

    valid_types = ['member_balance', 'group_balance', 'income', 'new_account']
    if data_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的数据类型: {data_type}")

    # 预加载成员（使用原生 SQL 避免选择不存在的 scope 列）和营业部
    member_rows = db.execute(text("SELECT id, name, group_id FROM members")).fetchall()
    members = [{'id': row.id, 'name': row.name, 'group_id': row.group_id} for row in member_rows]
    groups = db.query(Group).all()
    # 支持重名员工：联合 key 为 (member_name, group_name)
    group_by_id = {g.id: g for g in groups}
    group_by_name = {g.name: g for g in groups}
    member_by_name = {m['name']: m for m in members}
    member_by_name_and_group = {}
    for m in members:
        g = group_by_id.get(m['group_id'])
        if g:
            key = (m['name'], g.name)
            member_by_name_and_group[key] = m

    success_count = 0
    fail_count = 0
    errors = []

    # 开户数据解析辅助（提前导入避免循环内重复导入）
    from datetime import datetime as _dt

    # 1. 删除该类型当周的历史记录（全量覆盖）
    if data_type == 'member_balance':
        db.query(MarginBalanceMember).filter(
            MarginBalanceMember.record_week == record_week
        ).delete()
    elif data_type == 'group_balance':
        db.query(MarginBalanceGroup).filter(
            MarginBalanceGroup.record_week == record_week
        ).delete()
    elif data_type == 'income':
        db.query(MarginIncome).filter(
            MarginIncome.record_week == record_week
        ).delete()
    elif data_type == 'new_account':
        # 开户数据为累计数据：先收集所有数据中的年份，删除这些年份的全部历史记录
        years_to_clear = set()
        for item in request.data:
            account_date_str = item.get('account_date') or item.get('开户日期', '')
            try:
                if isinstance(account_date_str, str) and account_date_str:
                    d = _dt.strptime(account_date_str, '%Y-%m-%d').date()
                    years_to_clear.add(d.year)
            except (ValueError, TypeError):
                pass
        for year in years_to_clear:
            db.query(MarginNewAccount).filter(
                extract('year', MarginNewAccount.account_date) == year
            ).delete()

    # 2. 插入新数据
    for item in request.data:
        try:
            if data_type == 'member_balance':
                group_name = item.get('group_name', '')
                member_name = item.get('member_name', '')
                dev_balance = float(item.get('development_balance', 0))
                svc_balance = float(item.get('service_balance', 0))
                balance_type = item.get('balance_type', 'spot')

                if not group_name or not member_name:
                    errors.append(f"缺少必要字段: 营业部或员工姓名")
                    fail_count += 1
                    continue

                group = group_by_name.get(group_name)
                # 优先按 (姓名, 营业部) 联合匹配，支持重名员工
                member = member_by_name_and_group.get((member_name, group_name)) or member_by_name.get(member_name)
                if not group:
                    errors.append(f"未找到营业部: {group_name}")
                    fail_count += 1
                    continue
                if not member:
                    errors.append(f"未找到员工: {member_name}（请先在营销人员中添加该员工）")
                    fail_count += 1
                    continue

                db.add(MarginBalanceMember(
                    member_id=member['id'],
                    group_id=group.id,
                    development_balance=Decimal(str(dev_balance)),
                    service_balance=Decimal(str(svc_balance)),
                    balance_type=balance_type,
                    record_week=record_week,
                    record_date=record_date
                ))

            elif data_type == 'group_balance':
                group_name = item.get('group_name') or item.get('营业部', '')
                spot = float(item.get('spot_balance') or item.get('时点余额', 0))
                daily = float(item.get('daily_balance') or item.get('日均余额', 0))

                group = group_by_name.get(group_name)
                if not group:
                    available_groups = ', '.join(sorted(group_by_name.keys()))
                    errors.append(f"未找到营业部: '{group_name}'。系统中存在的营业部: {available_groups}")
                    continue

                db.add(MarginBalanceGroup(
                    group_id=group.id,
                    spot_balance=Decimal(str(spot)),
                    daily_balance=Decimal(str(daily)),
                    record_week=record_week,
                    record_date=record_date
                ))

            elif data_type == 'income':
                group_name = item.get('group_name') or item.get('营业部', '')
                income = float(item.get('income_amount') or item.get('息费收入', 0))

                group = group_by_name.get(group_name)
                if not group:
                    available_groups = ', '.join(sorted(group_by_name.keys()))
                    errors.append(f"未找到营业部: '{group_name}'。系统中存在的营业部: {available_groups}")
                    continue

                db.add(MarginIncome(
                    group_id=group.id,
                    income_amount=Decimal(str(income)),
                    record_week=record_week,
                    record_date=record_date
                ))

            elif data_type == 'new_account':
                group_name = item.get('group_name') or item.get('营业部', '')
                member_name = item.get('member_name') or item.get('所属员工', '')
                customer = item.get('customer_name') or item.get('客户姓名', '')
                asset = float(item.get('asset_amount') or item.get('开户资产', 0))
                account_date_str = item.get('account_date') or item.get('开户日期', '')

                group = group_by_name.get(group_name)
                # 优先按 (姓名, 营业部) 联合匹配，支持重名员工
                member = member_by_name_and_group.get((member_name, group_name)) or member_by_name.get(member_name)
                if not group:
                    errors.append(f"未找到营业部: {group_name}")
                    continue
                if not member:
                    errors.append(f"未找到员工: {member_name}")
                    continue
                if not customer:
                    errors.append(f"缺少客户姓名")
                    continue

                # Parse date
                try:
                    from datetime import datetime as dt
                    if isinstance(account_date_str, str):
                        account_date = dt.strptime(account_date_str, '%Y-%m-%d').date()
                    else:
                        account_date = account_date_str
                except (ValueError, TypeError):
                    errors.append(f"无效的开户日期: {account_date_str}")
                    continue

                db.add(MarginNewAccount(
                    member_id=member['id'],
                    group_id=group.id,
                    customer_name=customer,
                    asset_amount=Decimal(str(asset)),
                    account_date=account_date,
                    record_week=record_week
                ))

            success_count += 1
        except Exception as e:
            errors.append(f"数据处理错误: {str(e)}")

    db.commit()

    # 记录导入日志
    log = MarginImportLog(
        import_date=record_date,
        data_type=data_type,
        record_count=len(request.data),
        success_count=success_count,
        error_count=len(errors),
        operator=operator
    )
    db.add(log)
    db.commit()

    return ImportResponse(
        success_count=success_count,
        error_count=len(errors),
        errors=errors[:20]
    )


# ============== 列表查询API ==============

@router.get("/member-balances", response_model=List[MemberBalanceResponse])
def get_member_balances(
    balance_type: str = Query('spot', regex="^(spot|daily)$"),
    record_week: Optional[str] = None,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取个人余额列表（使用原生SQL避免选择不存在的scope列）"""
    sql = """
        SELECT
            mbm.id, mbm.member_id, mbm.group_id,
            mbm.development_balance, mbm.service_balance,
            mbm.balance_type, mbm.record_week, mbm.record_date,
            m.name as member_name, g.name as group_name
        FROM margin_balance_members mbm
        JOIN (SELECT id, name FROM members) m ON mbm.member_id = m.id
        JOIN (SELECT id, name FROM groups) g ON mbm.group_id = g.id
        WHERE mbm.balance_type = :balance_type
    """
    params = {"balance_type": balance_type}
    if record_week:
        sql += " AND mbm.record_week = :record_week"
        params["record_week"] = record_week
    if group_id:
        sql += " AND mbm.group_id = :group_id"
        params["group_id"] = group_id
    sql += " ORDER BY (mbm.development_balance + mbm.service_balance) DESC"

    rows = db.execute(text(sql), params).fetchall()

    return [
        MemberBalanceResponse(
            id=row.id,
            member_id=row.member_id,
            member_name=row.member_name,
            group_id=row.group_id,
            group_name=row.group_name,
            development_balance=float(row.development_balance),
            service_balance=float(row.service_balance),
            balance_type=row.balance_type,
            record_week=row.record_week,
            record_date=row.record_date
        )
        for row in rows
    ]


@router.get("/group-balances", response_model=List[GroupBalanceResponse])
def get_group_balances(
    record_week: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取营业部余额列表"""
    query = db.query(
        MarginBalanceGroup,
        Group.name.label("group_name")
    ).join(Group, MarginBalanceGroup.group_id == Group.id)

    if record_week:
        query = query.filter(MarginBalanceGroup.record_week == record_week)

    results = query.order_by(MarginBalanceGroup.spot_balance.desc()).all()

    return [
        GroupBalanceResponse(
            id=r.MarginBalanceGroup.id,
            group_id=r.MarginBalanceGroup.group_id,
            group_name=r.group_name,
            spot_balance=float(r.MarginBalanceGroup.spot_balance),
            daily_balance=float(r.MarginBalanceGroup.daily_balance),
            record_week=r.MarginBalanceGroup.record_week,
            record_date=r.MarginBalanceGroup.record_date
        )
        for r in results
    ]


@router.delete("/member-balances")
def delete_member_balances(
    record_week: str,
    db: Session = Depends(get_db)
):
    """删除指定周的个人余额数据"""
    count = db.query(MarginBalanceMember).filter(
        MarginBalanceMember.record_week == record_week
    ).delete()
    db.commit()
    return {"message": f"已删除 {record_week} 的个人余额数据", "deleted_count": count}


@router.delete("/group-balances")
def delete_group_balances(
    record_week: str,
    db: Session = Depends(get_db)
):
    """删除指定周的营业部余额数据"""
    count = db.query(MarginBalanceGroup).filter(
        MarginBalanceGroup.record_week == record_week
    ).delete()
    db.commit()
    return {"message": f"已删除 {record_week} 的营业部余额数据", "deleted_count": count}


@router.delete("/income")
def delete_income(
    record_week: str,
    db: Session = Depends(get_db)
):
    """删除指定周的息费收入数据"""
    count = db.query(MarginIncome).filter(
        MarginIncome.record_week == record_week
    ).delete()
    db.commit()
    return {"message": f"已删除 {record_week} 的息费收入数据", "deleted_count": count}


@router.delete("/new-accounts")
def delete_new_accounts(
    record_week: str,
    db: Session = Depends(get_db)
):
    """删除指定周的新开户数据"""
    count = db.query(MarginNewAccount).filter(
        MarginNewAccount.record_week == record_week
    ).delete()
    db.commit()
    return {"message": f"已删除 {record_week} 的新开户数据", "deleted_count": count}


@router.get("/income", response_model=List[IncomeResponse])
def get_income(
    record_week: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取息费收入列表"""
    query = db.query(
        MarginIncome,
        Group.name.label("group_name")
    ).join(Group, MarginIncome.group_id == Group.id)

    if record_week:
        query = query.filter(MarginIncome.record_week == record_week)
    if year:
        query = query.filter(extract('year', MarginIncome.record_date) == year)

    results = query.order_by(MarginIncome.income_amount.desc()).all()

    return [
        IncomeResponse(
            id=r.MarginIncome.id,
            group_id=r.MarginIncome.group_id,
            group_name=r.group_name,
            income_amount=float(r.MarginIncome.income_amount),
            record_week=r.MarginIncome.record_week,
            record_date=r.MarginIncome.record_date
        )
        for r in results
    ]


@router.get("/new-accounts", response_model=List[NewAccountResponse])
def get_new_accounts(
    year: Optional[int] = None,
    record_week: Optional[str] = None,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取新开户列表（使用原生SQL避免选择不存在的scope列）"""
    sql = """
        SELECT
            mna.id, mna.member_id, mna.group_id,
            mna.customer_name, mna.asset_amount, mna.account_date,
            mna.record_week,
            m.name as member_name, g.name as group_name
        FROM margin_new_accounts mna
        JOIN (SELECT id, name FROM members) m ON mna.member_id = m.id
        JOIN (SELECT id, name FROM groups) g ON mna.group_id = g.id
        WHERE 1=1
    """
    params = {}
    if year:
        sql += " AND EXTRACT(year FROM mna.account_date) = :year"
        params["year"] = year
    if record_week:
        sql += " AND mna.record_week = :record_week"
        params["record_week"] = record_week
    if group_id:
        sql += " AND mna.group_id = :group_id"
        params["group_id"] = group_id
    sql += " ORDER BY mna.account_date DESC"

    rows = db.execute(text(sql), params).fetchall()

    return [
        NewAccountResponse(
            id=row.id,
            member_id=row.member_id,
            member_name=row.member_name,
            group_id=row.group_id,
            group_name=row.group_name,
            customer_name=row.customer_name,
            asset_amount=float(row.asset_amount),
            account_date=row.account_date,
            record_week=row.record_week
        )
        for row in rows
    ]


# ============== 统计数据API ==============

@router.get("/stats", response_model=StatsResponse)
def get_stats(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取年度看板统计数据"""
    if not year:
        year = date.today().year

    # 获取最新一周的数据（同时考虑余额、开户和收入表）
    latest_week_bg = db.query(func.max(MarginBalanceGroup.record_week)).scalar()
    latest_week_na = db.query(func.max(MarginNewAccount.record_week)).scalar()
    latest_week_in = db.query(func.max(MarginIncome.record_week)).scalar()

    all_weeks = [w for w in [latest_week_bg, latest_week_na, latest_week_in] if w]
    latest_week = max(all_weeks) if all_weeks else None

    prev_week = None
    if latest_week:
        # 简单计算上一周: 2026-W20 -> 2026-W19
        parts = latest_week.split('-W')
        y, w = int(parts[0]), int(parts[1])
        if w > 1:
            prev_week = f"{y}-W{w-1:02d}"
        else:
            prev_week = f"{y-1}-W52"

    # 辖区时点余额 & 日均余额（最新周）
    spot_total = 0.0
    daily_total = 0.0
    spot_prev = 0.0
    daily_prev = 0.0

    if latest_week:
        latest_groups = db.query(MarginBalanceGroup).filter(
            MarginBalanceGroup.record_week == latest_week
        ).all()
        spot_total = sum(float(g.spot_balance) for g in latest_groups)
        daily_total = sum(float(g.daily_balance) for g in latest_groups)

    if prev_week:
        prev_groups = db.query(MarginBalanceGroup).filter(
            MarginBalanceGroup.record_week == prev_week
        ).all()
        spot_prev = sum(float(g.spot_balance) for g in prev_groups)
        daily_prev = sum(float(g.daily_balance) for g in prev_groups)

    # 今年开户数量（按 account_date 统计）
    new_account_count = db.query(MarginNewAccount).filter(
        extract('year', MarginNewAccount.account_date) == year
    ).count()

    # 今年息费收入累计
    income_records = db.query(MarginIncome).filter(
        extract('year', MarginIncome.record_date) == year
    ).all()
    income_total = sum(float(r.income_amount) for r in income_records)

    # 计算环比变化
    spot_change = spot_total - spot_prev
    daily_change = daily_total - daily_prev

    # 开户周环比（按 account_date 所在自然周统计）
    from datetime import timedelta
    today = date.today()
    # 本周一和本周日
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    # 上周一和上周日
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = prev_week_start + timedelta(days=6)

    week_accounts = db.query(MarginNewAccount).filter(
        extract('year', MarginNewAccount.account_date) == year,
        MarginNewAccount.account_date >= week_start,
        MarginNewAccount.account_date <= week_end
    ).count()
    prev_week_accounts = db.query(MarginNewAccount).filter(
        extract('year', MarginNewAccount.account_date) == year,
        MarginNewAccount.account_date >= prev_week_start,
        MarginNewAccount.account_date <= prev_week_end
    ).count()
    account_change = week_accounts - prev_week_accounts

    # 息费收入周环比（按 record_week 统计，因为收入是周度汇总数据）
    income_change = 0.0
    if latest_week:
        latest_income = db.query(MarginIncome).filter(
            MarginIncome.record_week == latest_week
        ).all()
        income_latest = sum(float(r.income_amount) for r in latest_income)
        prev_income = db.query(MarginIncome).filter(
            MarginIncome.record_week == prev_week
        ).all() if prev_week else []
        income_prev = sum(float(r.income_amount) for r in prev_income)
        income_change = income_latest - income_prev

    # 营业部分布（时点余额）
    group_distribution = []
    if latest_week:
        group_data = db.query(
            MarginBalanceGroup,
            Group.name.label("group_name")
        ).join(Group).filter(
            MarginBalanceGroup.record_week == latest_week
        ).order_by(MarginBalanceGroup.spot_balance.desc()).all()
        group_distribution = [
            {"group_name": r.group_name, "spot_balance": float(r.MarginBalanceGroup.spot_balance),
             "daily_balance": float(r.MarginBalanceGroup.daily_balance)}
            for r in group_data
        ]
        # 按固定营业部顺序排序
        group_order = {'上一': 1, '上二': 2, '上三': 3, '上四': 4, '上五': 5, '上六': 6, '上海分公司': 7}
        group_distribution.sort(key=lambda x: group_order.get(x['group_name'], 99))

    # 息费收入分布
    income_distribution = []
    income_by_group = db.query(
        MarginIncome.group_id,
        Group.name.label("group_name"),
        func.sum(MarginIncome.income_amount).label("total_income")
    ).join(Group).filter(
        extract('year', MarginIncome.record_date) == year
    ).group_by(MarginIncome.group_id, Group.name).order_by(func.sum(MarginIncome.income_amount).desc()).all()
    income_distribution = [
        {"group_name": r.group_name, "income": float(r.total_income)}
        for r in income_by_group
    ]
    # 按固定营业部顺序排序
    group_order = {'上一': 1, '上二': 2, '上三': 3, '上四': 4, '上五': 5, '上六': 6, '上海分公司': 7}
    income_distribution.sort(key=lambda x: group_order.get(x['group_name'], 99))

    # 周度开户趋势（按 account_date 的自然周统计，ISO 周格式）
    weekly_trend_sql = text("""
        SELECT
            TO_CHAR(account_date, 'YYYY') || '-W' || LPAD(TO_CHAR(account_date, 'IW'), 2, '0') as week,
            COUNT(*) as count
        FROM margin_new_accounts
        WHERE EXTRACT(year FROM account_date) = :year
        GROUP BY TO_CHAR(account_date, 'YYYY') || '-W' || LPAD(TO_CHAR(account_date, 'IW'), 2, '0')
        ORDER BY week
    """)
    weekly_trend_rows = db.execute(weekly_trend_sql, {"year": year}).fetchall()
    weekly_account_trend = [
        {"week": r.week, "count": r.count}
        for r in weekly_trend_rows
    ]

    # 月度开户趋势（按 account_date 的月份统计）
    month_expr = extract('month', MarginNewAccount.account_date).label("month")
    monthly_trend = db.query(
        month_expr,
        func.count(MarginNewAccount.id).label("count")
    ).filter(
        extract('year', MarginNewAccount.account_date) == year
    ).group_by(month_expr).order_by(month_expr).all()
    monthly_account_trend = [
        {"month": int(r.month), "count": r.count}
        for r in monthly_trend
    ]

    # 最近更新时间（从余额表和开户表取最新）
    last_update_bg = db.query(func.max(MarginBalanceGroup.record_date)).scalar()
    last_update_na = db.query(func.max(MarginNewAccount.account_date)).scalar()
    last_update = max([d for d in [last_update_bg, last_update_na] if d], default=None)

    return StatsResponse(
        spot_balance=round(spot_total, 2),
        daily_balance=round(daily_total, 2),
        new_account_count=new_account_count,
        income_total=round(income_total, 2),
        spot_change=round(spot_change, 2),
        daily_change=round(daily_change, 2),
        account_change=account_change,
        income_change=round(income_change, 2),
        last_update_date=last_update,
        group_distribution=group_distribution,
        income_distribution=income_distribution,
        weekly_account_trend=weekly_account_trend,
        monthly_account_trend=monthly_account_trend
    )


# ============== 导入日志API ==============

@router.get("/import-logs", response_model=List[ImportLogResponse])
def get_import_logs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取导入日志"""
    logs = db.query(MarginImportLog).order_by(
        MarginImportLog.created_at.desc()
    ).limit(limit).all()

    return [
        ImportLogResponse(
            id=log.id,
            import_date=log.import_date,
            data_type=log.data_type,
            record_count=log.record_count,
            success_count=log.success_count,
            error_count=log.error_count,
            operator=log.operator,
            created_at=log.created_at
        )
        for log in logs
    ]


# ============== 考核指标API ==============

@router.get("/targets", response_model=List[TargetResponse])
def get_targets(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取考核指标"""
    if not year:
        year = date.today().year

    # 获取所有营业部
    groups = db.query(Group).all()

    # 获取目标数据
    targets = db.query(MarginTarget).filter(MarginTarget.year == year).all()
    target_map = {t.group_id: t for t in targets}

    # 计算年度实际值
    income_actual = defaultdict(float)
    income_records = db.query(MarginIncome).filter(
        extract('year', MarginIncome.record_date) == year
    ).all()
    for r in income_records:
        income_actual[r.group_id] += float(r.income_amount)

    account_actual = defaultdict(int)
    account_records = db.query(MarginNewAccount).filter(
        extract('year', MarginNewAccount.account_date) == year
    ).all()
    for r in account_records:
        account_actual[r.group_id] += 1

    result = []
    for g in groups:
        target = target_map.get(g.id)
        income_t = float(target.income_target) if target else 0
        account_t = target.account_target if target else 0
        income_a = income_actual.get(g.id, 0)
        account_a = account_actual.get(g.id, 0)

        result.append(TargetResponse(
            id=target.id if target else 0,
            group_id=g.id,
            group_name=g.name,
            year=year,
            income_target=income_t,
            account_target=account_t,
            income_completion_rate=round((income_a / income_t * 100), 2) if income_t > 0 else 0,
            account_completion_rate=round((account_a / account_t * 100), 2) if account_t > 0 else 0,
            created_at=target.created_at if target else None,
            updated_at=target.updated_at if target else None
        ))

    # 按固定营业部顺序排序
    group_order = {'上一': 1, '上二': 2, '上三': 3, '上四': 4, '上五': 5, '上六': 6, '上海分公司': 7}
    result.sort(key=lambda x: group_order.get(x.group_name, 99))

    return result


@router.post("/targets", response_model=TargetResponse)
def create_or_update_target(
    request: TargetCreateRequest,
    db: Session = Depends(get_db)
):
    """保存/更新考核指标"""
    group = db.query(Group).filter(Group.id == request.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="营业部不存在")

    target = db.query(MarginTarget).filter(
        MarginTarget.group_id == request.group_id,
        MarginTarget.year == request.year
    ).first()

    if target:
        target.income_target = Decimal(str(request.income_target))
        target.account_target = request.account_target
    else:
        target = MarginTarget(
            group_id=request.group_id,
            year=request.year,
            income_target=Decimal(str(request.income_target)),
            account_target=request.account_target
        )
        db.add(target)

    db.commit()
    db.refresh(target)

    # 计算完成率
    income_actual = db.query(MarginIncome).filter(
        MarginIncome.group_id == request.group_id,
        extract('year', MarginIncome.record_date) == request.year
    ).all()
    income_a = sum(float(r.income_amount) for r in income_actual)

    account_actual = db.query(MarginNewAccount).filter(
        MarginNewAccount.group_id == request.group_id,
        extract('year', MarginNewAccount.account_date) == request.year
    ).count()

    income_t = float(target.income_target)
    account_t = target.account_target

    return TargetResponse(
        id=target.id,
        group_id=target.group_id,
        group_name=group.name,
        year=target.year,
        income_target=income_t,
        account_target=account_t,
        income_completion_rate=round((income_a / income_t * 100), 2) if income_t > 0 else 0,
        account_completion_rate=round((account_a / account_t * 100), 2) if account_t > 0 else 0,
        created_at=target.created_at,
        updated_at=target.updated_at
    )
