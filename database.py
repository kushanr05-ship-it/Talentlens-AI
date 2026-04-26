from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./talentlens.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    job_description = Column(Text)
    resume_text = Column(Text)
    report = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Auto-create tables upon import
Base.metadata.create_all(bind=engine)
