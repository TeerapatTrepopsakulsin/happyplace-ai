from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.auth_service import login_user, register_user


router = APIRouter()


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        role=request.role,
        db=db,
    )
    return RegisterResponse(id=str(user.id), email=str(user.email), role=str(user.role))


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    access_token = await login_user(
        email=request.email, password=request.password, db=db
    )
    return LoginResponse(access_token=access_token)
