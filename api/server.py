from fastapi import FastAPI

from .db_manager import async_engine
from .logger import db_logger, uvicorn_logger
from .models import *
from .Routers import (classes_route, invoices_route, reservations_route,
                      students_route, teachers_route)

app = FastAPI(title="Pararel system")


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(students_route.router)
app.include_router(teachers_route.router)
app.include_router(classes_route.router)
app.include_router(reservations_route.router)
app.include_router(invoices_route.router)
