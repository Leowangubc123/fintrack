from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Member, Group, SalesRecord
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("", response_model=List[MemberResponse])
def list_members(group_id: int = None, db: Session = Depends(get_db)):
    """获取成员列表，可按营业部筛选"""
    query = db.query(Member)
    if group_id:
        query = query.filter(Member.group_id == group_id)
    members = query.all()
    result = []
    for member in members:
        group = db.query(Group).filter(Group.id == member.group_id).first()
        result.append(MemberResponse(
            id=member.id,
            name=member.name,
            phone=member.phone,
            group_id=member.group_id,
            group_name=group.name if group else None
        ))
    return result


@router.post("", response_model=MemberResponse)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    """创建成员"""
    db_member = Member(name=member.name, phone=member.phone, group_id=member.group_id)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    group = db.query(Group).filter(Group.id == db_member.group_id).first()
    return MemberResponse(
        id=db_member.id,
        name=db_member.name,
        phone=db_member.phone,
        group_id=db_member.group_id,
        group_name=group.name if group else None
    )


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, member: MemberUpdate, db: Session = Depends(get_db)):
    """更新成员"""
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="成员不存在")
    if member.name:
        db_member.name = member.name
    if member.phone:
        db_member.phone = member.phone
    if member.group_id:
        db_member.group_id = member.group_id
    db.commit()
    db.refresh(db_member)
    group = db.query(Group).filter(Group.id == db_member.group_id).first()
    return MemberResponse(
        id=db_member.id,
        name=db_member.name,
        phone=db_member.phone,
        group_id=db_member.group_id,
        group_name=group.name if group else None
    )


@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """删除成员"""
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="成员不存在")
    # Check for existing sales records
    sales_count = db.query(SalesRecord).filter(SalesRecord.member_id == member_id).count()
    if sales_count > 0:
        raise HTTPException(status_code=400, detail="该成员存在销售记录，无法删除")
    db.delete(db_member)
    db.commit()
    return {"message": "成员已删除"}


@router.post("/{member_id}/transfer")
def transfer_member(member_id: int, target_group_id: int, db: Session = Depends(get_db)):
    """成员转组"""
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="成员不存在")

    # 验证目标营业部是否存在
    target_group = db.query(Group).filter(Group.id == target_group_id).first()
    if not target_group:
        raise HTTPException(status_code=404, detail="目标营业部不存在")

    db_member.group_id = target_group_id
    db.commit()
    return {"message": "成员已转组", "member_id": member_id, "new_group_id": target_group_id}
