import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bitnp_ideas.db.base import Base
from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.main import app
from bitnp_ideas.models.entities import User
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import CurrentUser
from bitnp_ideas.security.rbac import AuthContext, get_auth_context


@dataclass(frozen=True)
class SeedUsers:
    superuser: CurrentUser
    administrator: CurrentUser
    developer: CurrentUser
    outsider: CurrentUser


@dataclass
class ApiTestContext:
    client: TestClient
    sessionmaker: async_sessionmaker[AsyncSession]
    users: SeedUsers
    auth_context: AuthContext | None

    def run(self, coroutine):
        return asyncio.run(coroutine)

    def set_user(self, user: CurrentUser) -> None:
        self.auth_context = AuthContext(user=user)

    def set_api_key(self, user: CurrentUser, api_key) -> None:
        self.auth_context = AuthContext(user=user, api_key=api_key)

    def use_real_auth(self) -> None:
        app.dependency_overrides.pop(get_auth_context, None)

    def use_stub_auth(self) -> None:
        async def override_auth_context() -> AuthContext:
            if self.auth_context is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required.",
                )
            return self.auth_context

        app.dependency_overrides[get_auth_context] = override_auth_context


def current_user(user: User) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        global_role=user.global_role,
        is_active=user.is_active,
    )


async def seed_users(sessionmaker: async_sessionmaker[AsyncSession]) -> SeedUsers:
    async with sessionmaker() as session:
        superuser = User(
            sso_provider="test",
            sso_subject="superuser",
            email="superuser@example.test",
            display_name="Super User",
            global_role=GlobalRole.SUPERUSER,
            is_active=True,
        )
        administrator = User(
            sso_provider="test",
            sso_subject="administrator",
            email="administrator@example.test",
            display_name="Administrator",
            global_role=GlobalRole.ADMINISTRATOR,
            is_active=True,
        )
        developer = User(
            sso_provider="test",
            sso_subject="developer",
            email="developer@example.test",
            display_name="Developer",
            global_role=GlobalRole.DEVELOPER,
            is_active=True,
        )
        outsider = User(
            sso_provider="test",
            sso_subject="outsider",
            email="outsider@example.test",
            display_name="Outsider",
            global_role=GlobalRole.DEVELOPER,
            is_active=True,
        )
        session.add_all([superuser, administrator, developer, outsider])
        await session.commit()
        return SeedUsers(
            superuser=current_user(superuser),
            administrator=current_user(administrator),
            developer=current_user(developer),
            outsider=current_user(outsider),
        )


@pytest.fixture
def api_context(tmp_path: Path) -> AsyncGenerator[ApiTestContext]:
    database_path = tmp_path / "bitnp_ideas_test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def initialize_database() -> SeedUsers:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        return await seed_users(sessionmaker)

    users = asyncio.run(initialize_database())

    async def override_db_session() -> AsyncGenerator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    context = ApiTestContext(
        client=TestClient(app),
        sessionmaker=sessionmaker,
        users=users,
        auth_context=AuthContext(user=users.administrator),
    )
    app.dependency_overrides[get_db_session] = override_db_session
    context.use_stub_auth()

    yield context

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())
