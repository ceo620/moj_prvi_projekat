from datetime import datetime, timezone

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models import RefreshToken, Tenant, User
from app.schemas import RefreshRequest, UserCreate, UserLogin
from app.security import (
    create_access_token,
    create_refresh_token_payload,
    decode_token,
    generate_refresh_token_id,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token_hash,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, payload: UserCreate) -> User:
        tenant_result = await self.session.exec(select(Tenant).where(Tenant.slug == payload.tenant_slug, Tenant.is_active == True))  # noqa: E712
        tenant = tenant_result.first()
        if not tenant:
            raise NotFoundError("Tenant not found")

        existing = await self.session.exec(select(User).where(User.tenant_id == tenant.id, User.email == payload.email))
        if existing.first():
            raise ConflictError("User with this email already exists in this tenant")

        user = User(
            tenant_id=tenant.id,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=payload.role,
            is_active=True,
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(self, payload: UserLogin) -> dict:
        tenant_result = await self.session.exec(select(Tenant).where(Tenant.slug == payload.tenant_slug, Tenant.is_active == True))  # noqa: E712
        tenant = tenant_result.first()
        if not tenant:
            raise NotFoundError("Invalid credentials")

        user_result = await self.session.exec(
            select(User).where(
                User.email == payload.email,
                User.tenant_id == tenant.id,
                User.is_active == True,  # noqa: E712
            )
        )
        user = user_result.first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise NotFoundError("Invalid credentials")

        access_token = create_access_token(subject=user.email, tenant_id=user.tenant_id, role=user.role)

        jti = generate_refresh_token_id()
        refresh_token, expires_at = create_refresh_token_payload(subject=user.email, tenant_id=user.tenant_id, user_id=user.id, jti=jti)
        stored = RefreshToken(
            tenant_id=user.tenant_id,
            user_id=user.id,
            token_jti=jti,
            hashed_token=hash_refresh_token(refresh_token),
            expires_at=expires_at,
            is_revoked=False,
        )
        self.session.add(stored)
        await self.session.commit()
        return {"access_token": access_token, "refresh_token": refresh_token}

    async def refresh(self, payload: RefreshRequest) -> dict:
        try:
            decoded = decode_token(payload.refresh_token)
        except Exception as exc:
            raise NotFoundError("Invalid refresh token") from exc

        if decoded.get("type") != "refresh":
            raise NotFoundError("Invalid refresh token")

        jti = decoded.get("jti")
        user_id = decoded.get("user_id")
        tenant_id = decoded.get("tenant_id")
        email = decoded.get("sub")

        result = await self.session.exec(
            select(RefreshToken).where(
                RefreshToken.token_jti == jti,
                RefreshToken.user_id == user_id,
                RefreshToken.tenant_id == tenant_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
        stored = result.first()
        if not stored:
            raise NotFoundError("Refresh token not found or revoked")
        if not verify_refresh_token_hash(payload.refresh_token, stored.hashed_token):
            raise NotFoundError("Invalid refresh token")

        stored.is_revoked = True
        self.session.add(stored)

        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            raise NotFoundError("User inactive")

        access_token = create_access_token(subject=user.email, tenant_id=user.tenant_id, role=user.role)
        new_jti = generate_refresh_token_id()
        new_refresh_token, expires_at = create_refresh_token_payload(subject=email, tenant_id=tenant_id, user_id=user_id, jti=new_jti)
        replacement = RefreshToken(
            tenant_id=tenant_id,
            user_id=user_id,
            token_jti=new_jti,
            hashed_token=hash_refresh_token(new_refresh_token),
            expires_at=expires_at,
            is_revoked=False,
        )
        self.session.add(replacement)
        await self.session.commit()
        return {"access_token": access_token, "refresh_token": new_refresh_token}
