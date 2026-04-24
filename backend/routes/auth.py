from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from datetime import datetime, UTC
from backend.database import get_db
from backend.config import get_settings
from backend.utils.auth import create_session_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

class SignupRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/signup")
async def signup(req: SignupRequest):
    db = get_db()
    
    if req.username == settings.admin_username:
        raise HTTPException(status_code=400, detail="Cannot register as admin")
        
    existing_user = await db.users.find_one({"username": req.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
        
    user = {
        "username": req.username,
        "password_hash": hash_password(req.password),
        "created_at": datetime.now(UTC)
    }
    await db.users.insert_one(user)
    return {"message": "User created successfully"}

@router.post("/login")
async def login(req: LoginRequest, response: Response):
    db = get_db()
    
    if req.username == settings.admin_username:
        if req.password == settings.admin_password:
            token = create_session_token({"role": "admin", "sub": req.username}, settings.auth_session_secret, settings.auth_session_ttl_minutes)
            response.set_cookie(key="vv_session", value=token, httponly=True, samesite="lax")
            return {"role": "admin"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    user = await db.users.find_one({"username": req.username})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    token = create_session_token({"role": "customer", "sub": req.username}, settings.auth_session_secret, settings.auth_session_ttl_minutes)
    response.set_cookie(key="vv_session", value=token, httponly=True, samesite="lax")
    return {"role": "customer"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="vv_session")
    return {"message": "Logged out"}
