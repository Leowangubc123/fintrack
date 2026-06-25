from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import Group, Member
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("", response_model=List[GroupResponse])
def list_groups(db: Session = Depends(get_db)):
    """获取所有营业部列表"""
    results = db.query(
        Group,
        func.count(Member.id).label('member_count')
    ).outerjoin(
        Member, Member.group_id == Group.id
    ).group_by(Group.id).all()

    return [
        GroupResponse(
            id=group.id,
            name=group.name,
            leader=group.leader,
            created_at=group.created_at,
            member_count=count
        )
        for group, count in results
    ]


@router.post("", response_model=GroupResponse)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    """创建营业部"""
    db_group = Group(name=group.name, leader=group.leader)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return GroupResponse(
        id=db_group.id,
        name=db_group.name,
        leader=db_group.leader,
        created_at=db_group.created_at,
        member_count=0
    )


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(group_id: int, group: GroupUpdate, db: Session = Depends(get_db)):
    """更新营业部"""
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="营业部不存在")
    db_group.name = group.name
    db_group.leader = group.leader
    db.commit()
    db.refresh(db_group)
    member_count = db.query(func.count(Member.id)).filter(Member.group_id == db_group.id).scalar()
    return GroupResponse(
        id=db_group.id,
        name=db_group.name,
        leader=db_group.leader,
        created_at=db_group.created_at,
        member_count=member_count
    )


@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """删除营业部"""
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="营业部不存在")
    db.delete(db_group)
    db.commit()
    return {"message": "营业部已删除"}
