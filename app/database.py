from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./diabetes_twin.db")
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass
def get_db():
 db=SessionLocal()
 try: yield db
 finally: db.close()
