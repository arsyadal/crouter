import asyncio
import secrets
import hashlib
from datetime import datetime, timezone
import click
from sqlalchemy import select, update
from apps.gateway.api.deps import async_session_maker, init_db
from apps.gateway.models.entities import Tenant, APIKey


@click.group()
def cli():
    """CRouter CLI — Management and provisioning tool."""
    pass


@cli.group()
def keys():
    """Manage gateway API keys."""
    pass


@keys.command("create")
@click.option("--tenant", required=True, help="Tenant name")
@click.option("--rate-limit", default=60, type=int, help="Rate limit in requests per minute")
@click.option("--concurrency", default=10, type=int, help="Max in-flight concurrent requests")
@click.option("--key", default=None, help="Explicit key to use (optional, defaults to generated cr_live_...)")
def create_key(tenant: str, rate_limit: int, concurrency: int, key: str | None):
    """Create a new API key for a tenant."""

    async def _run():
        await init_db()
        raw_key = key or f"cr_live_{secrets.token_hex(16)}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        key_prefix = raw_key[:12]

        async with async_session_maker() as session:
            # Check or create tenant
            stmt = select(Tenant).where(Tenant.name == tenant)
            result = await session.execute(stmt)
            t = result.scalars().first()
            if not t:
                t = Tenant(name=tenant, is_active=True)
                session.add(t)
                await session.flush()

            new_key = APIKey(
                tenant_id=t.id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                rate_limit_rpm=rate_limit,
                max_concurrency=concurrency,
            )
            session.add(new_key)
            await session.commit()

        click.echo(f"API Key created successfully!")
        click.echo(f"Tenant:          {tenant}")
        click.echo(f"Key Prefix:      {key_prefix}...")
        click.echo(f"Rate Limit:      {rate_limit} RPM")
        click.echo(f"Max Concurrency: {concurrency}")
        click.echo(f"Generated Key:   {raw_key}")
        click.echo("WARNING: Save this key now! The raw key will never be shown again.")

    asyncio.run(_run())


@keys.command("list")
def list_keys():
    """List all gateway API keys."""

    async def _run():
        await init_db()
        async with async_session_maker() as session:
            stmt = select(APIKey)
            result = await session.execute(stmt)
            keys_list = result.scalars().all()

            if not keys_list:
                click.echo("No API keys found.")
                return

            click.echo(f"{'Key Prefix':<16} {'Rate Limit':<12} {'Concurrency':<12} {'Status':<10}")
            click.echo("-" * 55)
            for k in keys_list:
                status = "REVOKED" if k.revoked_at else "ACTIVE"
                click.echo(f"{k.key_prefix + '...':<16} {str(k.rate_limit_rpm) + ' RPM':<12} {str(k.max_concurrency):<12} {status:<10}")

    asyncio.run(_run())


@keys.command("revoke")
@click.argument("key_prefix")
def revoke_key(key_prefix: str):
    """Revoke a gateway API key by prefix."""

    async def _run():
        await init_db()
        async with async_session_maker() as session:
            stmt = select(APIKey).where(APIKey.key_prefix.like(f"{key_prefix}%"))
            result = await session.execute(stmt)
            keys_to_revoke = result.scalars().all()

            if not keys_to_revoke:
                click.echo(f"No key found matching prefix '{key_prefix}'.")
                return

            now = datetime.now(timezone.utc)
            for k in keys_to_revoke:
                k.revoked_at = now

            await session.commit()
            click.echo(f"Revoked {len(keys_to_revoke)} key(s) matching prefix '{key_prefix}'.")

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
