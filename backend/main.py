from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database import close_mongo_connection, connect_to_mongo
from backend.routes.auth import router as auth_router
from backend.routes.calls import router as calls_router
from backend.routes.orders import router as orders_router
from backend.routes.voice import router as voice_router
from backend.utils.auth import verify_session_token


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
app.include_router(auth_router)


@app.middleware("http")
async def auth_page_guard(request: Request, call_next):
    path = request.url.path
    if path in {"/login.html", "/favicon.ico"}:
        return await call_next(request)

    token = request.cookies.get("vv_session")
    session = None
    if token:
        try:
            session = verify_session_token(token, settings.auth_session_secret)
        except ValueError:
            session = None

    if path == "/shop.html" and session is None:
        return RedirectResponse(url="/login.html", status_code=307)

    if path == "/index.html":
        if session is None or session.get("role") != "admin":
            return RedirectResponse(url="/login.html", status_code=307)

    return await call_next(request)


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/login.html")


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
