import os
import ssl
import asyncpg
from utils.loggers.pretty_logs import pretty_log


async def get_pg_pool():
    internal_url = os.getenv("DATABASE_URL")
    public_url = os.getenv("DATABASE_PUBLIC_URL")

    # 💖 SSL context for cozy vibes
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # 🌸 Try internal URL
    try:
        pool = await asyncpg.create_pool(dsn=internal_url, ssl=ssl_context)
        pretty_log(
            tag="db",
            message="Connected to Postgres via internal URL!",
        )
        return pool
    except Exception as e:
        """pretty_log(
            tag="warn",
            message=f"Internal URL failed to connect: {e}",
            include_trace=True,
        )"""
        pass

    # 🧸 Try public URL fallback
    try:
        pool = await asyncpg.create_pool(dsn=public_url, ssl=ssl_context)
        pretty_log(
            tag="db",
            message="Connected to Postgres via public URL!",
        )
        return pool
    except Exception as e:
        pretty_log(
            tag="warn", message=f"Public URL failed to connect: {e}", include_trace=True
        )

    # 🌷 Both attempts failed
    pretty_log(
        tag="critical",
        message="Could not connect to either internal or public Postgres database.",
        include_trace=True,
    )
    raise ConnectionError(
        "💖 Could not connect to either internal or public Postgres database. Sending cozy vibes!"
    )
