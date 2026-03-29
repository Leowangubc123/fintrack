#!/usr/bin/env python3
"""
迁移2026年销售数据到私募交易表
将SalesRecord中的2026年数据迁移到PrivateFundTransaction
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models import SalesRecord, PrivateFundTransaction, PrivateFundProduct, Product, Member, Group
from sqlalchemy import func
from decimal import Decimal

def migrate_sales_to_private_fund():
    db = SessionLocal()
    try:
        # 1. 获取2026年的销售记录
        sales_records = db.query(SalesRecord).filter(
            func.extract('year', SalesRecord.sale_date) == 2026
        ).all()

        print(f"找到 {len(sales_records)} 条2026年销售记录")
        if len(sales_records) == 0:
            print("没有需要迁移的数据")
            return

        # 2. 获取所有私募产品，建立名称/code映射
        private_products = db.query(PrivateFundProduct).all()
        private_product_by_code = {p.code: p for p in private_products}
        private_product_by_name = {p.name: p for p in private_products}

        print(f"\n现有私募产品数量: {len(private_products)}")

        # 3. 获取普通产品信息，用于匹配
        products = db.query(Product).all()
        product_map = {p.id: p for p in products}

        # 4. 处理每条销售记录
        migrated = 0
        skipped = 0
        errors = []

        for record in sales_records:
            # 获取原产品信息
            product = product_map.get(record.product_id)
            if not product:
                skipped += 1
                errors.append(f"记录ID {record.id}: 找不到对应的产品ID {record.product_id}")
                continue

            # 尝试匹配私募产品
            private_product = None

            # 先尝试按名称匹配
            if product.name in private_product_by_name:
                private_product = private_product_by_name[product.name]
            # 再尝试按代码匹配
            elif product.code and product.code in private_product_by_code:
                private_product = private_product_by_code[product.code]

            if not private_product:
                skipped += 1
                errors.append(f"记录ID {record.id}: 产品 '{product.name}'({product.code}) 无对应私募产品")
                continue

            # 检查是否已存在相同的交易记录（避免重复）
            existing = db.query(PrivateFundTransaction).filter(
                PrivateFundTransaction.product_id == private_product.id,
                PrivateFundTransaction.member_id == record.member_id,
                PrivateFundTransaction.transaction_date == record.sale_date,
                PrivateFundTransaction.amount == record.amount
            ).first()

            if existing:
                skipped += 1
                continue

            # 创建私募交易记录
            sales_coefficient = float(private_product.sales_coefficient)
            assessed_amount = float(record.amount) * sales_coefficient

            transaction = PrivateFundTransaction(
                product_id=private_product.id,
                member_id=record.member_id,
                transaction_date=record.sale_date,
                amount=record.amount,
                transaction_type='sale',  # 默认为销售
                sales_coefficient=Decimal(str(sales_coefficient)),
                assessed_amount=Decimal(str(assessed_amount)),
                holding_coefficient=private_product.holding_coefficient or Decimal('1.0'),
                remark=f"从销售记录迁移: {record.remark}" if record.remark else "从销售记录迁移"
            )

            db.add(transaction)
            migrated += 1

            if migrated % 100 == 0:
                print(f"  已迁移 {migrated} 条...")

        # 提交事务
        db.commit()

        print(f"\n{'='*60}")
        print(f"迁移完成!")
        print(f"成功迁移: {migrated} 条")
        print(f"跳过: {skipped} 条")
        print(f"{'='*60}")

        if errors:
            print(f"\n警告/错误 ({len(errors)}条):")
            for e in errors[:10]:  # 只显示前10条
                print(f"  - {e}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 条")

        # 5. 验证迁移结果
        print(f"\n迁移后私募交易表统计:")
        pf_count = db.query(PrivateFundTransaction).filter(
            func.extract('year', PrivateFundTransaction.transaction_date) == 2026
        ).count()
        print(f"  2026年私募交易记录数: {pf_count}")

    except Exception as e:
        db.rollback()
        print(f"\n迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("迁移2026年销售数据到私募交易表")
    print("="*60)
    print()

    confirm = input("确认开始迁移? (yes/no): ")
    if confirm.lower() == 'yes':
        migrate_sales_to_private_fund()
    else:
        print("已取消")
