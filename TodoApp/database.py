# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"

# postgresql://postgres:1234@localhost:5432/TodoApplicationDatabase
# mysql+pymysql://root:1234@127.0.0.1:3306/TodoApplicationDatabase
# sqlite:///./todosapp.db

# Only needed for SQLite -----> connect_args={"check_same_thread": False}
engine = create_engine(

    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
