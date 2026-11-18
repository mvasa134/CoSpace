from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import Token, User
from app.services.auth import create_mock_token, get_current_user, MOCK_USER

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    if form_data.username and form_data.password:
        access_token = create_mock_token(user_id=MOCK_USER.id)
        return Token(access_token=access_token, token_type="bearer")

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Невірний логін або пароль"
    )


@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user