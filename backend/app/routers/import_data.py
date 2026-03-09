from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
import pandas as pd
from io import BytesIO
from app.database import get_db
from app.models import SalesRecord, ImportLog, Member, Product

router = APIRouter(prefix="/api/import", tags=["import"])


def parse_excel(content: bytes, filename: str) -> pd.DataFrame:
    """解析Excel文件"""
    if filename.endswith('.csv'):
        return pd.read_csv(BytesIO(content))
    else:
        return pd.read_excel(BytesIO(content))


def auto_detect_columns(columns: List[str]) -> dict:
    """自动识别列映射"""
    mapping = {}
    keywords = {
        "member_name": ["姓名", "名字", "销售人员", "理财师", "成员", "员工"],
        "group_name": ["营业部", "团队", "部门", "所属营业部", "门店"],
        "amount": ["金额", "销售额", "认购金额", "销售", "业绩", "认购额"],
        "sale_date": ["日期", "时间", "交易日期", "销售日期", "成交日期"],
        "phone": ["手机", "电话", "联系方式", "手机号"]
    }

    for col in columns:
        for field, kw_list in keywords.items():
            if field not in mapping:
                for kw in kw_list:
                    if kw in col:
                        mapping[field] = col
                        break
    return mapping


@router.post("/preview")
async def preview_import(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """预览导入数据"""
    try:
        content = await file.read()
        df = parse_excel(content, file.filename)

        # 自动检测列映射
        suggested_mapping = auto_detect_columns(df.columns.tolist())

        # 获取所有成员用于匹配
        members = db.query(Member).all()
        members_data = [{"id": m.id, "name": m.name, "group_id": m.group_id} for m in members]

        return {
            "total_rows": len(df),
            "columns": df.columns.tolist(),
            "suggested_mapping": suggested_mapping,
            "preview": df.head(10).fillna('').to_dict('records'),
            "existing_members": members_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")


@router.post("/execute")
async def execute_import(
    product_id: int,
    records: List[dict],
    duplicate_strategy: str = "skip",
    operator: str = "admin",
    db: Session = Depends(get_db)
):
    """执行导入"""
    # 验证产品
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    batch_id = str(uuid.uuid4())
    success_count = 0
    fail_count = 0
    errors = []

    for idx, record in enumerate(records):
        try:
            # 跳过标记为错误的记录
            if record.get('error'):
                fail_count += 1
                continue

            member_name = record.get('member_name')
            amount = record.get('amount', 0)
            sale_date = record.get('sale_date')

            if not member_name or not amount or not sale_date:
                errors.append({"row": idx + 1, "error": "缺少必要字段"})
                fail_count += 1
                continue

            # 查找成员
            member = db.query(Member).filter(Member.name == member_name).first()
            if not member:
                errors.append({"row": idx + 1, "error": f"成员'{member_name}'不存在"})
                fail_count += 1
                continue

            # 解析日期
            if isinstance(sale_date, str):
                try:
                    sale_date = datetime.strptime(sale_date, '%Y-%m-%d').date()
                except:
                    sale_date = datetime.strptime(sale_date, '%Y/%m/%d').date()
            elif isinstance(sale_date, datetime):
                sale_date = sale_date.date()

            # 解析金额
            if isinstance(amount, str):
                amount = float(amount.replace(',', '').replace('万', ''))

            # 检查重复
            existing = db.query(SalesRecord).filter(
                SalesRecord.product_id == product_id,
                SalesRecord.member_id == member.id,
                SalesRecord.sale_date == sale_date
            ).first()

            if existing:
                if duplicate_strategy == "skip":
                    continue
                elif duplicate_strategy == "overwrite":
                    existing.amount = amount
                    success_count += 1
                    continue

            # 创建销售记录
            sales_record = SalesRecord(
                product_id=product_id,
                member_id=member.id,
                group_id=member.group_id,
                amount=amount,
                sale_date=sale_date,
                import_batch_id=batch_id
            )
            db.add(sales_record)
            success_count += 1

        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})
            fail_count += 1

    db.commit()

    # 记录导入日志
    log = ImportLog(
        product_id=product_id,
        operator=operator,
        total_rows=len(records),
        success_rows=success_count,
        fail_rows=fail_count,
        file_name="import.xlsx"
    )
    db.add(log)
    db.commit()

    return {
        "batch_id": batch_id,
        "total": len(records),
        "success": success_count,
        "failed": fail_count,
        "errors": errors[:10]  # 只返回前10个错误
    }
