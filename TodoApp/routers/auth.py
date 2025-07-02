# auth.py
from datetime import datetime, timedelta, timezone
import starlette.status as status
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException,Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = '9126f198b5785532add73270f97009f18a92235a84a92ea7bffb7c716a8832b6'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


class CreateUserRequest(BaseModel):
    username: str
    email: str
    phone_number: str
    first_name: str
    last_name: str
    password: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
templates = Jinja2Templates(directory="TodoApp/templates")

### Pages ###

@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

### Endpoints ###
def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request):
    token = None
    # Header-дан іздеу
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    # Немесе cookie-ден іздеу
    elif request.cookies.get("access_token"):
        token = request.cookies.get("access_token")
    else:
        return None  # HTTPException тастамау!

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            return None
        return {"username": username, "id": user_id, "user_role": user_role}
    except JWTError:
        return None


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        username=create_user_request.username,
        email=create_user_request.email,
        phone_number=create_user_request.phone_number,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication credentials")

    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}


@router.put("/update/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    user_request: CreateUserRequest,
    db: db_dependency,
):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.username = user_request.username
    user.email = user_request.email
    user.phone_number = user_request.phone_number
    user.first_name = user_request.first_name
    user.last_name = user_request.last_name
    user.role = user_request.role
    user.hashed_password = bcrypt_context.hash(user_request.password)

    db.commit()
    db.refresh(user)
