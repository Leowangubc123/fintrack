#!/usr/bin/env python3
"""
私募产品数据迁移脚本：从 pickle 文件迁移到数据库
"""
import os
import sys
import pickle
from decimal import Decimal
from datetime import datetime

# 添加后端目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.database import SessionLocal, engine, Base
from app.models import PrivateFundProduct


def migrate_data():
    """从 pickle 文件迁移数据到数据库"""
    pickle_path = os.path.join(backend_dir, 'data', 'private_fund_products.pkl')

    if not os.path.exists(pickle_path):
        print(f"[ERROR] pickle文件不存在: {pickle_path}")
        return False

    db = SessionLocal()
    try:
        # 加载 pickle 数据
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)

        products = data.get('products', [])
        print(f"[INFO] 从pickle文件加载了 {len(products)} 个产品")

        migrated = 0
        skipped = 0

        for p in products:
            code = p.get('code')
            if not code:
                print(f"[WARN] 跳过没有代码的产品: {p.get('name', 'Unknown')}")
                continue

            # 检查是否已存在
            existing = db.query(PrivateFundProduct).filter(PrivateFundProduct.code == code).first()
            if existing:
                print(f"[INFO] 产品已存在，跳过: {code} - {p.get('name')}")
                skipped += 1
                continue

            # 创建新产品
            db_product = PrivateFundProduct(
                name=p.get('name', ''),
                code=code,
                distribution_scope=p.get('distribution_scope', '全国'),
                strategy_type=p.get('strategy_type', ''),
                custom_strategy=p.get('custom_strategy'),
                risk_level=p.get('risk_level', 'R3'),
                lock_period=p.get('lock_period'),
                open_period=p.get('open_period'),
                sales_coefficient=Decimal(str(p.get('sales_coefficient', 1.0))),
                holding_coefficient=Decimal(str(p.get('holding_coefficient', 1.0))) if p.get('holding_coefficient') else Decimal('1.0'),
                subscription_fee=Decimal(str(p.get('subscription_fee'))) if p.get('subscription_fee') else None,
                service_fee=Decimal(str(p.get('service_fee'))) if p.get('service_fee') else None,
                management_fee=Decimal(str(p.get('management_fee'))) if p.get('management_fee') else None,
                performance_fee=p.get('performance_fee')
            )
            db.add(db_product)
            migrated += 1
            print(f"[INFO] 准备迁移: {code} - {p.get('name')}")

        # 提交事务
        db.commit()
        print(f"\n[SUCCESS] 迁移完成!")
        print(f"  - 新增: {migrated} 个产品")
        print(f"  - 跳过: {skipped} 个产品（已存在）")
        return True

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def verify_migration():
    """验证迁移结果"""
    db = SessionLocal()
    try:
        count = db.query(PrivateFundProduct).count()
        print(f"\n[INFO] 数据库中现有 {count} 个私募产品")

        # 显示前5个产品
        products = db.query(PrivateFundProduct).limit(5).all()
        if products:
            print("\n前5个产品:")
            for p in products:
                print(f"  - {p.code}: {p.name} (风险等级: {p.risk_level})")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("私募产品数据迁移工具")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 执行迁移
    success = migrate_data()

    # 验证结果
    verify_migration()

    if success:
        print("\n[SUCCESS] 迁移脚本执行完成!")
        sys.exit(0)
    else:
        print("\n[FAILED] 迁移脚本执行失败!")
        sys.exit(1)
