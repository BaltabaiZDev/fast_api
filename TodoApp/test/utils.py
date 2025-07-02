from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from ..main import app
from ..models import Todos, Users
from ..routers.auth import bcrypt_context
from ..database import Base



SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {"username": "zhani", "id": 1, "user_role": "admin"}


client = TestClient(app)


@pytest.fixture(autouse=True)
def test_todo():
    todo = Todos(
        title="Test Todo",
        description="This is a test todo item",
        priority=5,
        complete=False,
        owner_id=1,
    )
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos"))
        connection.commit()
        
        
        
        
@pytest.fixture(autouse=True)
def test_user():
    user = Users(
        username="zhani",
        email = "zhani@example.com",
        hashed_password=bcrypt_context.hash("test1234"),
        role="admin",
        first_name="Zhanibek",
        last_name="Baltabay",
        phone_number="1234567890"
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()
        
        
        
        