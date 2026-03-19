from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from typing import Optional

router = APIRouter(prefix="/auth", tags=["认证"])

# JWT 配置
SECRET_KEY = "fintrack-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 固定用户配置
ADMIN_USERNAME = "admin123"
ADMIN_PASSWORD = "cczqsh"

security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class UserInfo(BaseModel):
    username: str


def create_access_token(username: str) -> str:
    """创建 JWT token"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """验证 JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="认证令牌已过期")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """用户登录"""
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(request.username)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserInfo)
def get_current_user(username: str = Depends(verify_token)):
    """获取当前用户信息"""
    return {"username": username}


@router.post("/logout")
def logout():
    """用户登出（前端清除 token 即可）"""
    return {"message": "登出成功"}
