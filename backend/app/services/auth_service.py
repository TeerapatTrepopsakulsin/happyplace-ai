from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.users import User
from app.services.errors import BadRequestError, ConflictError, ForbiddenError

ALLOWED_ROLES = {"regular", "therapist", "guardian"}


async def register_user(
    *, email: str, password: str, display_name: str | None, role: str, db: AsyncSession
) -> User:
    if role not in ALLOWED_ROLES:
        raise BadRequestError(
            "Invalid role. Must be one of: regular, therapist, guardian"
        )

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictError("Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(*, email: str, password: str, db: AsyncSession) -> str:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise ForbiddenError("Invalid email or password")

    if not verify_password(password, str(user.password_hash)):
        raise ForbiddenError("Invalid email or password")

    token_data = {"sub": str(user.id), "role": user.role}
    return create_access_token(token_data)
