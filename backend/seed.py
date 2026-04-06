import asyncio
import os

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

TEST_USERS = [
    {"email": "regular1@test.com", "password": "testpassword", "display_name": "Test Regular 1", "role": "regular"},
    {"email": "regular2@test.com", "password": "testpassword", "display_name": "Test Regular 2", "role": "regular"},
    {"email": "regular3@test.com", "password": "testpassword", "display_name": "Test Regular 3", "role": "regular"},
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def main():
    # Import here to avoid issues before engine is set up
    from app.models.users import User

    async with AsyncSessionLocal() as session:
        for user_data in TEST_USERS:
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"[skip] {user_data['email']} already exists")
                continue

            user = User(
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                display_name=user_data["display_name"],
                role=user_data["role"],
            )
            session.add(user)
            print(f"[created] {user_data['email']}")

        await session.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
    