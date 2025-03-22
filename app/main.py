"""Main Server Module"""

from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

from app.database import (
    get_license_by_user,
    get_user,
    save_license,
    save_user,
    update_last_checked,
    user_has_license,
)
from app.encryption import encrypt_license

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()


class UserSignup(BaseModel):
    """User signup details"""

    username: str
    password: str


class UserLogin(BaseModel):
    """User login details"""

    username: str
    password: str


class LicenseRequestGeneration(BaseModel):
    """License generation request details"""

    user_id: int
    expiry_days: int


class LicenseRequestVerification(BaseModel):
    """License verification request details"""

    user_id: int
    license_key: str


@app.get("/")
def home():
    """Home route"""
    return {"message": "Welcome to the Licensing Sysytem."}


@app.post("/signup/")
def signup(user: UserSignup):
    """User signup"""
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    save_user(user.username, user.password)
    return {"user_id": get_user(user.username)[0]}


@app.post("/login/")
def login(user: UserLogin):
    """User login"""
    stored_user = get_user(user.username)
    if not stored_user or not pwd_context.verify(user.password, stored_user[2]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    user_license = user_has_license(stored_user[0])
    license_key = None if not user_license else user_license[0]
    return {"user_id": stored_user[0], "license_key": license_key}


@app.post("/generate-license/")
def generate_license(request: LicenseRequestGeneration):
    """Generate license key"""
    if user_has_license(request.user_id):
        raise HTTPException(status_code=400, detail="User already has a license")

    expiry_date = (datetime.utcnow() + timedelta(days=request.expiry_days)).strftime(
        "%Y-%m-%d"
    )
    license_data = {"expiry_date": expiry_date}
    license_key = encrypt_license(license_data)

    save_license(request.user_id, license_key, expiry_date)
    return {"license_key": license_key, "expiry_date": expiry_date}


@app.post("/verify-license/")
def verify_license(request: LicenseRequestVerification):
    """Verify license key"""
    result = get_license_by_user(request.user_id)
    print(result)

    if not result or result[0] != request.license_key:
        raise HTTPException(status_code=400, detail="Invalid license key")

    license_key, expiry_date, last_checked = result
    expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")

    if expiry_date < datetime.utcnow():
        raise HTTPException(status_code=403, detail="License has expired")

    if last_checked:
        last_checked = datetime.strptime(last_checked, "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() - last_checked < timedelta(hours=24):
            return {"status": "valid", "expiry_date": expiry_date.strftime("%Y-%m-%d")}

    update_last_checked(license_key)
    return {"status": "valid", "expiry_date": expiry_date.strftime("%Y-%m-%d")}
