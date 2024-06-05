import os
from typing import Annotated

import dotenv
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

dotenv.load_dotenv()

if os.getenv("USE_LOCAL_DB") == True:
    DATABASE_URL = "sqlite+aiosqlite:///./database_new.db"
else:
    DATABASE_URL = os.getenv("POSTGRESQL_URL")


Base = declarative_base()


async_engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)


async def get_db():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}")


db_dependancy = Annotated[async_sessionmaker, Depends(get_db)]
