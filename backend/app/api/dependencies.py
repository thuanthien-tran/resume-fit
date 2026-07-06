from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.factory import get_auth_provider
from app.database.session import get_db
from app.models.user import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = get_auth_provider().verify_access_token(token)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Không tìm thấy người dùng")
    if user.status == "blocked":
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Tài khoản chưa được kích hoạt")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ dành cho quản trị viên")
    return current_user


def assert_owner_or_admin(resource_user_id, current_user: User) -> None:
    if current_user.role != "admin" and resource_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập")
