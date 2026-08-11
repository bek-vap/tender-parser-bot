from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine_kwargs = {"pool_pre_ping": True}

# Neon database requires SSL, but local/docker postgres does not.
if "postgresql" in settings.DATABASE_URL:
    engine_kwargs.update({
        "pool_recycle": 300,
        "pool_size": 10,               # increased from 5 to allow more concurrent connections
        "max_overflow": 5,             # allow up to 5 extra connections in spikes
        "pool_timeout": 30,            # seconds to wait for a free connection before raising timeout
    })
    if "localhost" not in settings.DATABASE_URL and "127.0.0.1" not in settings.DATABASE_URL and "postgres" not in settings.DATABASE_URL:
        engine_kwargs.update({
            "connect_args": {"sslmode": "require"}
        })


engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
