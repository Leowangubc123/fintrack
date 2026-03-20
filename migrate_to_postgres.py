#!/usr/bin/env python3
"""
数据迁移脚本：从本地 SQLite 迁移到 Railway PostgreSQL
"""

import os
import sys

# 设置环境变量使用本地 SQLite
os.environ['DATABASE_URL'] = 'sqlite:///./backend/fintrack.db'

# 导入本地数据库
sys.path.insert(0, 'backend')
from app.database import engine as sqlite_engine, SessionLocal as SQLiteSession, Base
from app.models import Group, Member, Product, ProductTarget, SalesRecord, ImportLog

# 获取 Railway PostgreSQL 连接字符串
print("=" * 60)
print("FinTrack 数据迁移工具")
print("=" * 60)

# 从环境变量读取 PostgreSQL URL
postgres_url = os.environ.get('PG_URL', '').strip()

if not postgres_url:
    print("\n请设置环境变量 PG_URL：")
    print("export PG_URL='postgresql://postgres:xxx@xxx.railway.internal:5432/railway'")
    print("\n然后从 Railway 控制台获取连接字符串：")
    print("1. 打开 https://railway.app/dashboard")
    print("2. 点击你的 PostgreSQL 服务")
    print("3. 进入 'Connect' 标签")
    print("4. 复制 'Connection String'")
    sys.exit(1)

if not postgres_url.startswith('postgresql://'):
    print("错误：连接字符串必须以 postgresql:// 开头")
    sys.exit(1)

print("\n开始迁移...")
print("-" * 60)

# 创建 PostgreSQL 引擎
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

pg_engine = create_engine(postgres_url)
PGSession = sessionmaker(bind=pg_engine)

# 创建表结构（如果不存在）
Base.metadata.create_all(bind=pg_engine)

# 迁移数据
sqlite_db = SQLiteSession()
pg_db = PGSession()

try:
    # 按顺序迁移，处理外键依赖
    tables = [
        ('组织架构', Group, sqlite_db.query(Group).all()),
        ('成员', Member, sqlite_db.query(Member).all()),
        ('产品', Product, sqlite_db.query(Product).all()),
        ('产品目标', ProductTarget, sqlite_db.query(ProductTarget).all()),
        ('销售记录', SalesRecord, sqlite_db.query(SalesRecord).all()),
        ('导入日志', ImportLog, sqlite_db.query(ImportLog).all()),
    ]

    for name, model, records in tables:
        if not records:
            print(f"  {name}: 无数据，跳过")
            continue

        count = len(records)
        print(f"  {name}: 迁移 {count} 条记录...", end='')

        for record in records:
            # 将记录转为字典
            data = {}
            for col in model.__table__.columns:
                data[col.name] = getattr(record, col.name)

            # 创建新记录
            new_record = model(**data)
            pg_db.add(new_record)

        pg_db.commit()
        print(f" 完成")

    print("-" * 60)
    print("✅ 数据迁移成功！")
    print(f"\n请访问: https://fintrack-web-production-fa12.up.railway.app")

except Exception as e:
    pg_db.rollback()
    print(f"\n❌ 迁移失败: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    sqlite_db.close()
    pg_db.close()
