from fastapi import FastAPI

from .db_manager import async_engine
from .models import *
from .Routers.students import router as student_router

app = FastAPI(title="Pararel system")


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(student_router)
