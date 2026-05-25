from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.database import get_db
from app.models import Member, Group
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse

router = APIRouter(prefix="/api/members", tags=["members"])


def _has_scope_column(db):
    """检查 members 表是否有 scope 列"""
    try:
        db.execute(text("SELECT scope FROM members LIMIT 0"))
        return True
    except Exception:
        return False


@router.get("", response_model=List[MemberResponse])
def list_members(group_id: int = None, db: Session = Depends(get_db)):
    """获取成员列表，可按营业部筛选"""
    has_scope = _has_scope_column(db)
    if has_scope:
        sql = "SELECT id, name, phone, group_id, COALESCE(scope, 'public_fund,private_fund,advisory,margin_trading') as scope FROM members"
    else:
        sql = "SELECT id, name, phone, group_id, 'public_fund,private_fund,advisory,margin_trading' as scope FROM members"
    params = {}
    if group_id:
        sql += " WHERE group_id = :group_id"
        params['group_id'] = group_id
    result_rows = db.execute(text(sql), params).fetchall()
    result = []
    for row in result_rows:
        group = db.query(Group).filter(Group.id == row.group_id).first()
        result.append(MemberResponse(
            id=row.id,
            name=row.name,
            phone=row.phone,
            group_id=row.group_id,
            scope=row.scope,
            group_name=group.name if group else None
        ))
    return result


@router.post("", response_model=MemberResponse)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    """创建成员"""
    has_scope = _has_scope_column(db)
    columns = ["name", "phone", "group_id"]
    values = [":name", ":phone", ":group_id"]
    params = {"name": member.name, "phone": member.phone or "", "group_id": member.group_id}

    if has_scope:
        columns.append("scope")
        values.append(":scope")
        params["scope"] = member.scope or 'public_fund,private_fund,advisory,margin_trading'

    sql = f"INSERT INTO members ({', '.join(columns)}) VALUES ({', '.join(values)})"
    result = db.execute(text(sql), params)
    db.commit()
    new_id = result.lastrowid

    if has_scope:
        row = db.execute(
            text("SELECT id, name, phone, group_id, COALESCE(scope, 'public_fund,private_fund,advisory,margin_trading') as scope FROM members WHERE id = :id"),
            {"id": new_id}
        ).fetchone()
    else:
        row = db.execute(
            text("SELECT id, name, phone, group_id FROM members WHERE id = :id"),
            {"id": new_id}
        ).fetchone()
    group = db.query(Group).filter(Group.id == row.group_id).first()
    return MemberResponse(
        id=row.id,
        name=row.name,
        phone=row.phone,
        group_id=row.group_id,
        scope=row.scope if has_scope else 'public_fund,private_fund,advisory,margin_trading',
        group_name=group.name if group else None
    )


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, member: MemberUpdate, db: Session = Depends(get_db)):
    """更新成员"""
    has_scope = _has_scope_column(db)

    # 检查成员是否存在
    row = db.execute(text("SELECT id, name, phone, group_id FROM members WHERE id = :id"), {"id": member_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="成员不存在")

    # 构建更新 SQL
    updates = []
    params = {"id": member_id}
    if member.name:
        updates.append("name = :name")
        params["name"] = member.name
    if member.phone is not None:
        updates.append("phone = :phone")
        params["phone"] = member.phone
    if member.group_id:
        updates.append("group_id = :group_id")
        params["group_id"] = member.group_id
    if has_scope and member.scope is not None:
        updates.append("scope = :scope")
        params["scope"] = member.scope

    if updates:
        sql = "UPDATE members SET " + ", ".join(updates) + " WHERE id = :id"
        db.execute(text(sql), params)
        db.commit()

    # 重新查询
    if has_scope:
        row = db.execute(
            text("SELECT id, name, phone, group_id, COALESCE(scope, 'public_fund,private_fund,advisory,margin_trading') as scope FROM members WHERE id = :id"),
            {"id": member_id}
        ).fetchone()
    else:
        row = db.execute(
            text("SELECT id, name, phone, group_id FROM members WHERE id = :id"),
            {"id": member_id}
        ).fetchone()
    group = db.query(Group).filter(Group.id == row.group_id).first()
    return MemberResponse(
        id=row.id,
        name=row.name,
        phone=row.phone,
        group_id=row.group_id,
        scope=row.scope if has_scope else 'public_fund,private_fund,advisory,margin_trading',
        group_name=group.name if group else None
    )


@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """删除成员"""
    row = db.execute(text("SELECT id FROM members WHERE id = :id"), {"id": member_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="成员不存在")
    db.execute(text("DELETE FROM members WHERE id = :id"), {"id": member_id})
    db.commit()
    return {"message": "成员已删除"}


@router.post("/{member_id}/transfer")
def transfer_member(member_id: int, target_group_id: int, db: Session = Depends(get_db)):
    """成员转组"""
    row = db.execute(text("SELECT id FROM members WHERE id = :id"), {"id": member_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="成员不存在")

    # 验证目标营业部是否存在
    target_group = db.query(Group).filter(Group.id == target_group_id).first()
    if not target_group:
        raise HTTPException(status_code=404, detail="目标营业部不存在")

    db.execute(text("UPDATE members SET group_id = :group_id WHERE id = :id"), {"id": member_id, "group_id": target_group_id})
    db.commit()
    return {"message": "成员已转组", "member_id": member_id, "new_group_id": target_group_id}
