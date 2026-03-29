#!/usr/bin/env python3
"""
检查 2026 年销售数据是否存在
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models import SalesRecord
from sqlalchemy import func
from datetime import date

def check_sales_data():
    db = SessionLocal()
    try:
        # 统计 2026 年销售记录总数
        total_2026 = db.query(SalesRecord).filter(
            func.extract('year', SalesRecord.sale_date) == 2026
        ).count()

        print(f"2026 年销售记录总数: {total_2026}")

        if total_2026 > 0:
            # 显示前10条记录
            records = db.query(SalesRecord).filter(
                func.extract('year', SalesRecord.sale_date) == 2026
            ).limit(10).all()

            print("\n前10条记录:")
            print("-" * 80)
            for r in records:
                print(f"ID: {r.id}, 产品ID: {r.product_id}, 成员ID: {r.member_id}, "
                      f"金额: {r.amount}万, 日期: {r.sale_date}, 营业部ID: {r.group_id}")

            # 按月份统计
            print("\n按月份统计:")
            print("-" * 80)
            monthly_stats = db.query(
                func.extract('month', SalesRecord.sale_date).label('month'),
                func.count(SalesRecord.id).label('count'),
                func.sum(SalesRecord.amount).label('total')
            ).filter(
                func.extract('year', SalesRecord.sale_date) == 2026
            ).group_by(
                func.extract('month', SalesRecord.sale_date)
            ).order_by('month').all()

            for stat in monthly_stats:
                print(f"{int(stat.month)}月: {stat.count} 条记录, 总计 {float(stat.total or 0)} 万")

            # 按营业部统计
            print("\n按营业部统计:")
            print("-" * 80)
            group_stats = db.query(
                SalesRecord.group_id,
                func.count(SalesRecord.id).label('count'),
                func.sum(SalesRecord.amount).label('total')
            ).filter(
                func.extract('year', SalesRecord.sale_date) == 2026
            ).group_by(
                SalesRecord.group_id
            ).all()

            for stat in group_stats:
                print(f"营业部ID {stat.group_id}: {stat.count} 条记录, 总计 {float(stat.total or 0)} 万")

        else:
            print("\n2026 年没有任何销售记录！")
            print("\n可能的原因:")
            print("1. 数据导入时选择的年份不是 2026")
            print("2. 导入过程中出现错误")
            print("3. 数据导入到了错误的表中")

            # 检查所有年份的数据
            print("\n\n数据库中所有销售记录按年份统计:")
            print("-" * 80)
            year_stats = db.query(
                func.extract('year', SalesRecord.sale_date).label('year'),
                func.count(SalesRecord.id).label('count')
            ).group_by(
                func.extract('year', SalesRecord.sale_date)
            ).order_by('year').all()

            for stat in year_stats:
                print(f"{int(stat.year)}年: {stat.count} 条记录")

    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 80)
    print("检查 2026 年销售数据")
    print("=" * 80)
    print()
    check_sales_data()
