# utils/auth_utils.py
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv  # Add dotenv to load redis url

load_dotenv()

security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    # 简单的令牌验证逻辑（可替换为实际逻辑，例如检查数据库或解码JWT）
    authorized_token = os.environ.get("AUTHORIZED_USER_TOKENS", "").split(",")
    if not authorized_token:
        raise ValueError("AUTHORIZED_USER_TOKEN environment variable not set.")
    if token not in authorized_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    return token
