import hashlib
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.gateway.api.deps import get_db
from apps.gateway.models.entities import APIKey, Tenant
from apps.gateway.schemas.admin import (
    KeyCreateRequest,
    KeyCreateResponse,
    KeyItemResponse,
    KeyListResponse,
)

router = APIRouter(prefix="/keys", tags=["Admin - Keys"])


@router.get("", response_model=KeyListResponse)
async def list_keys(db: AsyncSession = Depends(get_db)):
    """List all gateway API keys with tenant information."""
    stmt = (
        select(APIKey)
        .options(selectinload(APIKey.tenant))
        .order_by(APIKey.created_at.desc())
    )
    result = await db.execute(stmt)
    keys = result.scalars().all()

    items = [
        KeyItemResponse(
            id=k.id,
            tenant=k.tenant.name if k.tenant else "unknown",
            key_prefix=k.key_prefix,
            rate_limit_rpm=k.rate_limit_rpm,
            max_concurrency=k.max_concurrency,
            is_active=k.is_active,
            revoked_at=k.revoked_at.isoformat() if k.revoked_at else None,
            created_at=k.created_at.isoformat() if k.created_at else "",
        )
        for k in keys
    ]
    return KeyListResponse(data=items)


@router.post("", response_model=KeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_key(req: KeyCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new API key for a tenant. Returns the raw secret token once."""
    tenant_name = req.tenant.strip()
    if not tenant_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant name cannot be empty or whitespace.",
        )

    raw_key = req.key.strip() if req.key else f"cr_live_{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    key_prefix = raw_key[:12]

    # Check for duplicate key hash
    stmt_existing = select(APIKey).where(APIKey.key_hash == key_hash)
    existing_key = (await db.execute(stmt_existing)).scalars().first()
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An API key with this token already exists.",
        )

    # Find or create tenant
    stmt = select(Tenant).where(Tenant.name == tenant_name)
    result = await db.execute(stmt)
    tenant = result.scalars().first()
    if not tenant:
        tenant = Tenant(name=tenant_name, is_active=True)
        db.add(tenant)
        await db.flush()
    elif not tenant.is_active:
        tenant.is_active = True

    new_key = APIKey(
        tenant_id=tenant.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        rate_limit_rpm=req.rate_limit_rpm,
        max_concurrency=req.max_concurrency,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return KeyCreateResponse(
        id=new_key.id,
        tenant=tenant.name,
        key=raw_key,
        key_prefix=key_prefix,
        rate_limit_rpm=new_key.rate_limit_rpm,
        max_concurrency=new_key.max_concurrency,
        created_at=new_key.created_at.isoformat(),
    )


@router.post("/{key_id}/revoke", response_model=KeyItemResponse)
async def revoke_key(key_id: str, db: AsyncSession = Depends(get_db)):
    """Revoke an API key by its unique ID."""
    stmt = (
        select(APIKey)
        .where(APIKey.id == key_id)
        .options(selectinload(APIKey.tenant))
    )
    result = await db.execute(stmt)
    key = result.scalars().first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with id '{key_id}' not found.",
        )

    if key.revoked_at is None:
        key.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(key)

    return KeyItemResponse(
        id=key.id,
        tenant=key.tenant.name if key.tenant else "unknown",
        key_prefix=key.key_prefix,
        rate_limit_rpm=key.rate_limit_rpm,
        max_concurrency=key.max_concurrency,
        is_active=key.is_active,
        revoked_at=key.revoked_at.isoformat() if key.revoked_at else None,
        created_at=key.created_at.isoformat() if key.created_at else "",
    )


@router.delete("/{key_id}", response_model=KeyItemResponse)
async def delete_key(key_id: str, db: AsyncSession = Depends(get_db)):
    """Revoke an API key (DELETE method equivalent)."""
    return await revoke_key(key_id=key_id, db=db)
