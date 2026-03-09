from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/api/products", tags=["products"])


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
    is_archived: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    """获取产品列表，支持筛选"""
    query = db.query(Product)
    if status:
        query = query.filter(Product.status == status)
    if product_type:
        query = query.filter(Product.type == product_type)
    if is_archived is not None:
        query = query.filter(Product.is_archived == is_archived)
    return query.order_by(Product.created_at.desc()).all()


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


@router.post("/{product_id}/archive")
def archive_product(product_id: int, db: Session = Depends(get_db)):
    """归档产品"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")
    db_product.is_archived = True
    db.commit()
    return {"message": "产品已归档"}


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除产品"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")
    db.delete(db_product)
    db.commit()
    return {"message": "产品已删除"}
