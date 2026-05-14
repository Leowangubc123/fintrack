from fastapi import APIRouter, Depends, UploadFile, File, Form, Body, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime
import pandas as pd
from io import BytesIO
from app.database import get_db
from app.models import SalesRecord, ImportLog, Member, Product, Group


class ImportRecord(BaseModel):
    member_name: str
    group_name: Optional[str] = None
    amount: str
    sale_date: str
    remark: Optional[str] = ""


class ImportExecuteRequest(BaseModel):
    product_id: int
    records: List[ImportRecord]
    duplicate_strategy: str = "skip"
    operator: str = "admin"

router = APIRouter(prefix="/api/import", tags=["import"])


def parse_excel(content: bytes, filename: str) -> pd.DataFrame:
    """解析Excel文件"""
    try:
        if filename.endswith('.csv'):
            # 尝试多种编码
            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']:
                try:
                    return pd.read_csv(BytesIO(content), encoding=encoding)
                except:
                    continue
            return pd.read_csv(BytesIO(content), encoding='utf-8')
        else:
            return pd.read_excel(BytesIO(content))
    except Exception as e:
        raise ValueError(f"文件解析失败: {str(e)}")


def auto_detect_columns(columns: List[str]) -> dict:
    """自动识别列映射 - 精确匹配优先，一个列名只能映射到一个字段"""
    mapping = {}
    # 已匹配的列名，防止重复映射
    matched_columns = set()

    # 按照优先级排序的字段配置（优先级高的先匹配）
    # 公募委托查询表中：开发人员优先于服务人员；委托数量为金额（元单位）
    field_configs = [
        ("member_name", ["开发人员", "销售人员", "服务人员", "姓名", "名字", "理财师", "成员", "员工"]),
        ("group_name", ["所属营业部", "营业部", "团队", "部门", "门店"]),
        ("amount", ["委托数量", "销售金额", "销售额", "认购金额", "金额", "业绩", "认购额"]),
        ("sale_date", ["委托日期", "交易日期", "销售日期", "成交日期", "开始日期", "日期", "时间"]),
        ("security_code", ["证券代码", "产品代码", "基金代码"]),
        ("order_status", ["委托状态", "状态"]),
        ("service_member", ["服务人员"]),
        ("remark", ["备注", "说明", "附注"]),
    ]

    # 将列名转换为字符串
    col_list = [str(col) for col in columns]

    # 第一轮：完全匹配
    for field, kw_list in field_configs:
        if field in mapping:
            continue
        for kw in kw_list:
            for col_str in col_list:
                if col_str in matched_columns:
                    continue
                if kw == col_str:  # 完全匹配
                    mapping[field] = col_str
                    matched_columns.add(col_str)
                    break
            if field in mapping:
                break

    # 第二轮：包含匹配（只匹配未被映射的列）
    for field, kw_list in field_configs:
        if field in mapping:
            continue
        for kw in kw_list:
            for col_str in col_list:
                if col_str in matched_columns:
                    continue
                if kw in col_str:  # 包含匹配
                    mapping[field] = col_str
                    matched_columns.add(col_str)
                    break
            if field in mapping:
                break

    return mapping


@router.post("/preview")
async def preview_import(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """预览导入数据"""
    print(f"[DEBUG] preview_import called, product_id={product_id}, file={file.filename}")
    try:
        content = await file.read()
        print(f"[DEBUG] file content size: {len(content)} bytes")
        df = parse_excel(content, file.filename)
        print(f"[DEBUG] parsed df shape: {df.shape}, columns: {df.columns.tolist()}")

        # 获取所选产品代码，用于前端做证券代码验证
        product = db.query(Product).filter(Product.id == product_id).first()
        product_code = product.code if product else None

        # 自动检测列映射
        suggested_mapping = auto_detect_columns(df.columns.tolist())

        # 获取所有成员用于匹配
        members = db.query(Member).all()
        members_data = [{"id": m.id, "name": m.name, "group_id": m.group_id} for m in members]

        # 处理预览数据，将 NaN 转为空字符串
        # 返回所有数据用于预览（前端可自行限制显示数量）
        preview_df = df.copy()
        for col in preview_df.columns:
            preview_df[col] = preview_df[col].apply(lambda x: '' if pd.isna(x) else str(x))

        return {
            "total_rows": len(df),
            "columns": df.columns.tolist(),
            "suggested_mapping": suggested_mapping,
            "preview": preview_df.to_dict('records'),
            "existing_members": members_data,
            "product_code": product_code
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")


@router.post("/execute")
async def execute_import(
    product_id: int = Query(..., description="产品ID"),
    records: List[ImportRecord] = Body(..., description="导入记录列表"),
    duplicate_strategy: str = Query("skip", description="重复处理策略"),
    operator: str = Query("admin", description="操作人"),
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

    # 预加载所有成员和营业部数据
    members = db.query(Member).all()
    groups = db.query(Group).all()
    # 创建名称映射，支持带空格和不带空格的匹配
    member_name_map = {}
    # 定义别名映射（Excel中的名称 -> 数据库中的真实姓名）
    # 用于处理Unicode字符编码问题，如"刘志页"映射到"刘志𬱖"
    name_aliases = {
        '刘志页': '刘志𬱖',
        '刘志頔': '刘志𬱖',
    }
    for m in members:
        # 原始名称
        member_name_map[m.name] = m
        # 去除空格后的名称（用于匹配Excel中姓名中间有空格的情况）
        normalized_name = m.name.replace(' ', '').replace('\u3000', '').strip()
        if normalized_name != m.name:
            member_name_map[normalized_name] = m
    group_name_map = {g.name: g for g in groups}

    for idx, record in enumerate(records):
        try:
            member_name = record.member_name
            group_name = record.group_name
            amount = record.amount
            sale_date = record.sale_date
            remark = record.remark or ''

            if not member_name or not amount or not sale_date:
                errors.append({"row": idx + 1, "error": "缺少必要字段"})
                fail_count += 1
                continue

            # 查找成员（支持带空格和不带空格的匹配，以及别名映射）
            # 先尝试原始名称，再尝试去除空格后的名称，最后尝试别名映射
            normalized_member_name = member_name.replace(' ', '').replace('\u3000', '').strip()
            # 检查是否有别名映射
            aliased_name = name_aliases.get(member_name) or name_aliases.get(normalized_member_name)
            member = member_name_map.get(member_name) or member_name_map.get(normalized_member_name) or (member_name_map.get(aliased_name) if aliased_name else None)
            if not member:
                # 记录更详细的错误信息，帮助诊断字符编码问题
                error_msg = f"成员'{member_name}'不存在"
                print(f"[IMPORT ERROR] Row {idx + 1}: {error_msg}")
                print(f"[IMPORT DEBUG] Available members: {list(member_name_map.keys())[:10]}...")
                errors.append({"row": idx + 1, "error": error_msg, "member_name": member_name})
                fail_count += 1
                continue

            # 确定营业部ID
            group_id = member.group_id
            if group_name:
                # 如果提供了营业部名称，验证是否匹配
                group = group_name_map.get(group_name)
                if group:
                    group_id = group.id
                    # 验证成员是否属于该营业部
                    if member.group_id != group_id:
                        # 成员不属于该营业部，但不阻止导入
                        pass

            # 解析日期
            if isinstance(sale_date, str):
                try:
                    sale_date = datetime.strptime(sale_date, '%Y-%m-%d').date()
                except:
                    try:
                        sale_date = datetime.strptime(sale_date, '%Y/%m/%d').date()
                    except:
                        sale_date = pd.to_datetime(sale_date).date()
            elif isinstance(sale_date, datetime):
                sale_date = sale_date.date()

            # 解析金额
            if isinstance(amount, str):
                amount_str = amount.replace(',', '').replace('万', '')
                if amount_str:
                    amount = float(amount_str)
                else:
                    amount = 0
            elif pd.isna(amount):
                amount = 0

            # 检查是否已存在相同产品+成员+日期的记录
            existing = db.query(SalesRecord).filter(
                SalesRecord.product_id == product_id,
                SalesRecord.member_id == member.id,
                SalesRecord.sale_date == sale_date
            ).first()

            if existing:
                if duplicate_strategy == "skip":
                    # 累加金额到现有记录（同一销售人员同一天的多笔销售）
                    existing.amount = float(existing.amount) + amount
                    success_count += 1
                    continue
                elif duplicate_strategy == "overwrite":
                    existing.amount = amount
                    existing.group_id = group_id
                    existing.remark = remark
                    success_count += 1
                    continue

            # 创建销售记录
            sales_record = SalesRecord(
                product_id=product_id,
                member_id=member.id,
                group_id=group_id,
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
