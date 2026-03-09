from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import groups, members, products, import_data, dashboard

app = FastAPI(title="FinTrack API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据表
Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(groups.router)
app.include_router(members.router)
app.include_router(products.router)
app.include_router(import_data.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FinTrack API"}


@app.get("/")
def root():
    return {"message": "FinTrack API", "version": "1.0.0"}
