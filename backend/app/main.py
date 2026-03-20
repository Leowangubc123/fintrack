from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.routers import groups, members, products, import_data, dashboard, analysis

app = FastAPI(title="FinTrack API", version="1.0.0")

# CORS配置 - 必须在其他中间件之前
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理 - 捕获验证错误
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[ERROR] Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "参数验证失败"}
    )

# 创建数据表
Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(groups.router)
app.include_router(members.router)
app.include_router(products.router)
app.include_router(import_data.router)
app.include_router(dashboard.router)
app.include_router(analysis.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FinTrack API"}


@app.get("/")
def root():
    return {"message": "FinTrack API", "version": "1.0.0"}
