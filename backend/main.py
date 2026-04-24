from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database import close_mongo_connection, connect_to_mongo
from backend.routes.calls import router as calls_router
from backend.routes.orders import router as orders_router
from backend.routes.voice import router as voice_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    connect_to_mongo()
    yield
    close_mongo_connection()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router)
app.include_router(calls_router)
app.include_router(voice_router)


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/shop.html")


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
