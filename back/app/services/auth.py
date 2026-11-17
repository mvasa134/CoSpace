from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

MOCK_USER = User(
    id=42,
    email="student@kpi.ua",
    full_name="Максим Василець",
    password="hashhash",
    phone_number="+380991234567"
)

def create_mock_token(user_id: int) -> str:
    return f"mock-jwt-token-for-user-{user_id}"

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    if not token.startswith("mock-jwt-token-for-user-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или истекший токен аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return MOCK_USER