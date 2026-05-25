from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.models import ProductTarget
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/products", tags=["products"])


class GroupAssignment(BaseModel):
    group_id: int
    target: float


class MemberAssignment(BaseModel):
    member_id: int
    target: float


class SaveGroupAssignmentsRequest(BaseModel):
    assignments: List[GroupAssignment]


class SaveMemberAssignmentsRequest(BaseModel):
    group_id: int
    assignments: List[MemberAssignment]


def calculate_status(start_date: date, end_date: date) -> str:
    """根据日期计算产品状态"""
    today = date.today()
    if today < start_date:
        return "待开始"
    elif today > end_date:
        return "已结束"
    else:
        return "募集中"


@router.get("", response_model=List[ProductResponse])
def list_products(
    status: Optional[str] = None,
    product_type: Optional[str] = None,
    is_archived: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取产品列表，支持筛选，包含销售进度"""
    from app.models import SalesRecord
    from sqlalchemy import func

    query = db.query(Product)
    if status:
        query = query.filter(Product.status == status)
    if product_type:
        query = query.filter(Product.type == product_type)
    if is_archived is not None:
        query = query.filter(Product.is_archived == is_archived)

    products = query.order_by(Product.created_at.desc()).all()

    # 计算每个产品的销售总额和分配人数
    result = []
    for product in products:
        # 计算已募集金额
        total_sales = db.query(func.sum(SalesRecord.amount)).filter(
            SalesRecord.product_id == product.id
        ).scalar() or 0

        # 计算已分配人数（有销售记录的不同成员数）
        assigned_count = db.query(SalesRecord.member_id).filter(
            SalesRecord.product_id == product.id
        ).distinct().count()

        # 构建响应数据
        product_dict = {
            "id": product.id,
            "name": product.name,
            "alias": product.alias,
            "type": product.type,
            "issuer": product.issuer,
            "code": product.code,
            "start_date": product.start_date,
            "end_date": product.end_date,
            "total_target": product.total_target,
            "description": product.description,
            "status": product.status,
            "is_archived": product.is_archived,
            "created_at": product.created_at,
            "raised_amount": float(total_sales),
            "assigned_count": assigned_count
        }
        result.append(product_dict)

    return result


@router.post("", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """创建产品"""
    status = calculate_status(product.start_date, product.end_date)
    db_product = Product(
        **product.dict(),
        status=status
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# ===== 任务分配路由（放在通用路由之前，避免被拦截） =====

@router.get("/{product_id}/assignments/groups")
def get_group_assignments(product_id: int, db: Session = Depends(get_db)):
    """获取产品的营业部任务分配"""
    from app.models import Group
    assignments = db.query(ProductTarget).filter(
        ProductTarget.product_id == product_id,
        ProductTarget.member_id == None
    ).all()

    # 获取所有相关营业部ID
    group_ids = [a.group_id for a in assignments if a.group_id]
    groups_map = {}
    if group_ids:
        groups = db.query(Group).filter(Group.id.in_(group_ids)).all()
        groups_map = {g.id: g for g in groups}

    return [
        {
            "group_id": a.group_id,
            "target": float(a.target_amount),
            "group_name": groups_map.get(a.group_id).name if a.group_id and a.group_id in groups_map else None
        }
        for a in assignments
    ]


@router.post("/{product_id}/assignments/groups")
def save_group_assignments(
    product_id: int,
    data: SaveGroupAssignmentsRequest,
    db: Session = Depends(get_db)
):
    """保存营业部任务分配"""
    # 删除该产品现有的营业部分配（member_id为空的记录）
    db.query(ProductTarget).filter(
        ProductTarget.product_id == product_id,
        ProductTarget.member_id == None
    ).delete()

    # 插入新的分配记录
    for assignment in data.assignments:
        if assignment.target > 0:
            target = ProductTarget(
                product_id=product_id,
                group_id=assignment.group_id,
                target_amount=assignment.target
            )
            db.add(target)

    db.commit()
    return {"message": "营业部分配保存成功"}


@router.get("/{product_id}/assignments/members")
def get_member_assignments(product_id: int, group_id: int = None, db: Session = Depends(get_db)):
    """获取产品的个人任务分配"""
    from app.models import Member
    query = db.query(ProductTarget).filter(
        ProductTarget.product_id == product_id,
        ProductTarget.member_id != None
    )
    if group_id:
        query = query.filter(ProductTarget.group_id == group_id)

    assignments = query.all()

    # 获取所有相关成员ID（使用原生 SQL 避免选择不存在的 scope 列）
    member_ids = [a.member_id for a in assignments if a.member_id]
    members_map = {}
    if member_ids:
        placeholders = ', '.join([str(mid) for mid in member_ids])
        member_rows = db.execute(text(f"SELECT id, name, group_id FROM members WHERE id IN ({placeholders})")).fetchall()
        members_map = {row.id: row for row in member_rows}

    return [
        {
            "member_id": a.member_id,
            "group_id": a.group_id,
            "target": float(a.target_amount),
            "member_name": members_map.get(a.member_id).name if a.member_id and a.member_id in members_map else None
        }
        for a in assignments
    ]


@router.post("/{product_id}/assignments/members")
def save_member_assignments(
    product_id: int,
    data: SaveMemberAssignmentsRequest,
    db: Session = Depends(get_db)
):
    """保存个人任务分配"""
    # 删除该产品该营业部现有的个人分配
    db.query(ProductTarget).filter(
        ProductTarget.product_id == product_id,
        ProductTarget.group_id == data.group_id,
        ProductTarget.member_id != None
    ).delete()

    # 插入新的分配记录
    for assignment in data.assignments:
        if assignment.target > 0:
            target = ProductTarget(
                product_id=product_id,
                group_id=data.group_id,
                member_id=assignment.member_id,
                target_amount=assignment.target
            )
            db.add(target)

    db.commit()
    return {"message": "个人分配保存成功"}


# ===== 产品特定路由（放在通用路由之前） =====

@router.post("/{product_id}/archive")
def archive_product(product_id: int, db: Session = Depends(get_db)):
    """归档产品"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")
    db_product.is_archived = True
    db.commit()
    return {"message": "产品已归档"}


@router.post("/{product_id}/unarchive")
def unarchive_product(product_id: int, db: Session = Depends(get_db)):
    """解除归档产品"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")
    db_product.is_archived = False
    # 重新计算状态
    db_product.status = calculate_status(db_product.start_date, db_product.end_date)
    db.commit()
    return {"message": "产品已解除归档"}


@router.post("/{product_id}/clear-sales")
def clear_product_sales_data(product_id: int, db: Session = Depends(get_db)):
    """清空产品的已导入销售数据（只删除通过数据导入功能导入的Excel销售数据）"""
    from app.models import SalesRecord, ImportLog

    # 验证产品是否存在
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 查询该产品的所有销售记录（包括有和没有import_batch_id的记录）
    sales_records = db.query(SalesRecord).filter(
        SalesRecord.product_id == product_id
    ).all()

    if not sales_records:
        return {"message": "该产品暂无销售数据", "deleted_count": 0}

    # 删除所有销售记录（通过导入功能导入的数据都有import_batch_id，手动添加的也可能有）
    deleted_count = len(sales_records)
    for record in sales_records:
        db.delete(record)

    # 同时删除相关的导入日志记录
    import_logs = db.query(ImportLog).filter(
        ImportLog.product_id == product_id
    ).all()
    for log in import_logs:
        db.delete(log)

    db.commit()

    return {"message": "销售数据已清空", "deleted_count": deleted_count}


# ===== 产品通用路由（放在最后，避免拦截特定路由） =====

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """获取产品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """更新产品"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    for key, value in product.dict().items():
        setattr(db_product, key, value)

    # 重新计算状态
    db_product.status = calculate_status(db_product.start_date, db_product.end_date)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除产品"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")
    db.delete(db_product)
    db.commit()
    return {"message": "产品已删除"}
