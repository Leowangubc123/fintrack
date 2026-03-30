#!/usr/bin/env python3
"""
删除SalesRecord表中的2026年私募产品销售数据
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models import SalesRecord, PrivateFundProduct, Product
from sqlalchemy import func

def delete_private_fund_sales_from_2026():
    db = SessionLocal()
    try:
        # 1. 获取所有私募产品名称和代码
        private_products = db.query(PrivateFundProduct).all()
        private_names = {p.name for p in private_products}
        private_codes = {p.code for p in private_products if p.code}

        print(f"私募产品数量: {len(private_products)}")
        print(f"私募产品名称示例: {list(private_names)[:5]}")

        # 2. 获取所有普通产品信息
        products = db.query(Product).all()
        product_map = {p.id: p for p in products}

        # 3. 获取2026年的销售记录
        sales_records = db.query(SalesRecord).filter(
            func.extract('year', SalesRecord.sale_date) == 2026
        ).all()

        print(f"\n找到 {len(sales_records)} 条2026年销售记录")

        # 4. 找出匹配私募产品的记录
        to_delete = []
        for record in sales_records:
            product = product_map.get(record.product_id)
            if not product:
                continue

            # 检查是否匹配私募产品
            if product.name in private_names or (product.code and product.code in private_codes):
                to_delete.append(record)

        print(f"\n识别出 {len(to_delete)} 条私募产品销售记录待删除:")

        if len(to_delete) == 0:
            print("没有匹配的记录需要删除")
            return

        # 显示待删除记录
        for i, record in enumerate(to_delete, 1):
            product = product_map.get(record.product_id)
            print(f"  {i}. ID:{record.id} | {product.name if product else '未知产品'} | "
                  f"金额:{record.amount} | 日期:{record.sale_date}")

        # 5. 确认删除
        print(f"\n{'='*60}")
        confirm = input(f"确认删除这 {len(to_delete)} 条记录? (yes/no): ")

        if confirm.lower() != 'yes':
            print("已取消删除")
            return

        # 6. 执行删除
        deleted_count = 0
        for record in to_delete:
            db.delete(record)
            deleted_count += 1

        db.commit()

        print(f"\n{'='*60}")
        print(f"删除完成!")
        print(f"成功删除: {deleted_count} 条记录")
        print(f"{'='*60}")

        # 7. 验证删除结果
        remaining = db.query(SalesRecord).filter(
            func.extract('year', SalesRecord.sale_date) == 2026
        ).count()
        print(f"\n2026年SalesRecord剩余记录数: {remaining}")

    except Exception as e:
        db.rollback()
        print(f"\n删除失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("删除SalesRecord中的2026年私募销售数据")
    print("="*60)
    print()

    delete_private_fund_sales_from_2026()
