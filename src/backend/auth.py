
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
from models import User

security = HTTPBearer()

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token：缺少用户ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        raise

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

def require_tester(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "tester":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此操作需要测试人员权限"
        )
    return current_user

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = decode_access_token(token)
        return payload
    except HTTPException:
        return None

def get_token_expiry(token: str) -> Optional[datetime]:
    payload = verify_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None

if __name__ == "__main__":
    print("=" * 60)
    print("认证模块测试")
    print("=" * 60)

    print("\n【测试1：密码加密】")
    password = "test123"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)

    print(f"原密码: {password}")
    print(f"加密1: {hashed1}")
    print(f"加密2: {hashed2}")
    print(f"两次结果相同？ {hashed1 == hashed2}")

    print("\n【测试2：密码验证】")
    is_correct = verify_password(password, hashed1)
    is_wrong = verify_password("wrong_password", hashed1)
    print(f"✓ 正确密码验证: {is_correct}")
    print(f"✗ 错误密码验证: {is_wrong}")

    print("\n【测试3：JWT Token生成】")
    token_data = {"sub": "test001", "role": "tester"}
    token = create_access_token(token_data)
    print(f"生成的Token: {token[:50]}...")

    print("\n【测试4：Token解码】")
    try:
        payload = decode_access_token(token)
        print(f"✓ Token解码成功:")
        print(f"  - 用户ID: {payload.get('sub')}")
        print(f"  - 角色: {payload.get('role')}")
        print(f"  - 过期时间: {datetime.fromtimestamp(payload.get('exp'))}")
    except HTTPException as e:
        print(f"✗ Token解码失败: {e.detail}")

    print("\n【测试5：过期Token】")
    expired_token = create_access_token(
        token_data,
        expires_delta=timedelta(seconds=-1)
    )
    try:
        decode_access_token(expired_token)
        print("✗ 过期Token未被检测到")
    except HTTPException as e:
        print(f"✓ 正确检测到过期: {e.detail}")

    print("\n【测试6：Token剩余时间】")
    expiry = get_token_expiry(token)
    if expiry:
        remaining = expiry - datetime.utcnow()
        print(f"✓ Token还有 {remaining.seconds} 秒过期")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
