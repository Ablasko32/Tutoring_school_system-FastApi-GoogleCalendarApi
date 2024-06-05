from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from api.db.db_manager import async_engine
from api.db.models import *

from .logger import *
from .Routers import (auth, classes_route, invoices_route, reservations_route,
                      students_route, teacher_pay_route, teachers_route)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database
    await init_db()
    yield


app = FastAPI(title="Pararel system", lifespan=lifespan)

# alternative older
# @app.on_event("startup")
# async def on_startup():
#     await init_db()

# middlewere
app.add_middleware(BaseHTTPMiddleware, dispatch=request_logging_middleware)


# routers
app.include_router(auth.router)
app.include_router(students_route.router)
app.include_router(teachers_route.router)
app.include_router(classes_route.router)
app.include_router(reservations_route.router)
app.include_router(invoices_route.router)
app.include_router(teacher_pay_route.router)
