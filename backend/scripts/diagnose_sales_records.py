#!/usr/bin/env python3
"""
诊断SalesRecord表中的2026年数据
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models import SalesRecord, Product
from sqlalchemy import func

def diagnose_sales_records():
    db = SessionLocal()
    try:
        # 1. 获取2026年的销售记录
        sales_records = db.query(SalesRecord).filter(
            func.extract('year', SalesRecord.sale_date) == 2026
        ).all()

        print(f"2026年销售记录总数: {len(sales_records)}")

        if len(sales_records) == 0:
            print("\n没有找到2026年的销售记录")
            return

        # 2. 获取所有产品信息
        products = db.query(Product).all()
        product_map = {p.id: p for p in products}

        print("\n2026年销售记录详情:")
        print("-" * 80)

        for record in sales_records:
            product = product_map.get(record.product_id)
            product_name = product.name if product else '未知产品'
            product_code = product.code if product else '无代码'

            print(f"ID: {record.id} | 产品: {product_name} | 代码: {product_code} | "
                  f"金额: {record.amount} | 日期: {record.sale_date} | "
                  f"人员ID: {record.member_id}")

        print("-" * 80)

        # 3. 显示产品名称列表（用于匹配私募产品）
        print("\n涉及的产品名称列表:")
        product_names = set()
        for record in sales_records:
            product = product_map.get(record.product_id)
            if product:
                product_names.add(product.name)

        for name in sorted(product_names):
            print(f"  - {name}")

    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("="*80)
    print("诊断SalesRecord表2026年数据")
    print("="*80)
    print()

    diagnose_sales_records()
