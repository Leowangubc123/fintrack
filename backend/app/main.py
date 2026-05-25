from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.routers import groups, members, products, import_data, dashboard, analysis, private_fund, advisory, margin_trading

app = FastAPI(title="FinTrack API", version="1.0.0")

# CORS配置 - 必须在其他中间件之前
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理 - 捕获验证错误（添加 CORS 头）
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[ERROR] Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "参数验证失败"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# 处理其他异常，确保也有 CORS 头
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "message": "服务器内部错误"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# 创建数据表
Base.metadata.create_all(bind=engine)

# 迁移：为 members 表添加 scope 列（如果不存在）
try:
    inspector = inspect(engine)
    member_columns = [c['name'] for c in inspector.get_columns('members')]
    if 'scope' not in member_columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE members ADD COLUMN scope VARCHAR(100) DEFAULT 'public_fund,private_fund,advisory,margin_trading'"))
            conn.commit()
            print("[MIGRATION] Added scope column to members")
except Exception as e:
    print(f"[MIGRATION WARNING] members scope: {e}")

# 迁移：为 investment_advisory_targets 添加缺失列并修复约束
try:
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('investment_advisory_targets')]

    # 添加 current_income 列（如果不存在）
    if 'current_income' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE investment_advisory_targets ADD COLUMN current_income NUMERIC(15, 2) DEFAULT 0"))
            conn.commit()
            print("[MIGRATION] Added current_income column to investment_advisory_targets")

    # 添加 current_households 列（如果不存在）
    if 'current_households' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE investment_advisory_targets ADD COLUMN current_households INTEGER DEFAULT 0"))
            conn.commit()
            print("[MIGRATION] Added current_households column to investment_advisory_targets")

    # 添加 assessed_households 列（如果不存在）
    if 'assessed_households' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE investment_advisory_targets ADD COLUMN assessed_households INTEGER DEFAULT 0"))
            conn.commit()
            print("[MIGRATION] Added assessed_households column to investment_advisory_targets")

    # 修复 UNIQUE 约束：从 UNIQUE(group_id) 改为 UNIQUE(group_id, year)
    unique_constraints = inspector.get_unique_constraints('investment_advisory_targets')
    has_correct_constraint = any(
        c.get('name') == 'uq_group_year' for c in unique_constraints
    )
    has_old_constraint = any(
        c.get('column_names') == ['group_id'] for c in unique_constraints
    )

    if has_old_constraint and not has_correct_constraint:
        print("[MIGRATION] Rebuilding investment_advisory_targets to fix UNIQUE constraint...")
        with engine.connect() as conn:
            # 备份数据
            conn.execute(text("""
                CREATE TABLE investment_advisory_targets_backup AS
                SELECT * FROM investment_advisory_targets
            """))
            # 删除旧表
            conn.execute(text("DROP TABLE investment_advisory_targets"))
            # 创建新表（正确的约束）
            conn.execute(text("""
                CREATE TABLE investment_advisory_targets (
                    id INTEGER NOT NULL PRIMARY KEY,
                    group_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    income_target NUMERIC(15, 2),
                    households_target INTEGER,
                    current_income NUMERIC(15, 2) DEFAULT 0,
                    current_households INTEGER DEFAULT 0,
                    assessed_households INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    CONSTRAINT uq_group_year UNIQUE (group_id, year),
                    FOREIGN KEY(group_id) REFERENCES groups (id)
                )
            """))
            # 恢复数据
            conn.execute(text("""
                INSERT INTO investment_advisory_targets
                (id, group_id, year, income_target, households_target, current_income,
                 current_households, assessed_households, created_at, updated_at)
                SELECT id, group_id, year, income_target, households_target,
                       COALESCE(current_income, 0), COALESCE(current_households, 0),
                       COALESCE(assessed_households, 0), created_at, updated_at
                FROM investment_advisory_targets_backup
            """))
            # 删除备份表
            conn.execute(text("DROP TABLE investment_advisory_targets_backup"))
            conn.commit()
            print("[MIGRATION] Rebuilt investment_advisory_targets with correct UNIQUE constraint")
except Exception as e:
    print(f"[MIGRATION WARNING] {e}")

# 注册路由
app.include_router(groups.router)
app.include_router(members.router)
app.include_router(products.router)
app.include_router(import_data.router)
app.include_router(dashboard.router)
app.include_router(analysis.router)
app.include_router(private_fund.router)
app.include_router(advisory.router)
app.include_router(margin_trading.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FinTrack API"}


@app.get("/")
def root():
    return {"message": "FinTrack API", "version": "1.0.0"}
