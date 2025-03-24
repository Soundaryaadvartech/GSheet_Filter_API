import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import HTTPException


# Load environment variables
load_dotenv()

DB_USER = urllib.parse.quote_plus(os.getenv("DB_USER"))
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))
DB_HOST = os.getenv("DB_HOST")

# Dictionary of database connections
DATABASES = {
    "ZNG45F8J27LKMNQ": f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/zing",
    "PRT9X2C6YBMLV0F": f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/prathiksham",
    "BEE7W5ND34XQZRM": f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/beelittle"
}

# Maintain separate session makers for each DB
engines = {name: create_engine(url,pool_size =10 ,max_overflow=5) for name, url in DATABASES.items()}
session_makers = {name: sessionmaker(bind=eng, autocommit=False, autoflush=False) for name, eng in engines.items()}


# Function to get the database session dynamically
def get_db(business: str):
    if business not in session_makers:
        raise HTTPException(status_code=400, detail="Invalid business name")
    
    db = session_makers[business]()
    try:
        yield db
    finally:
        db.close()

BUSINESS_CODE_MAP = {
    "ZNG45F8J27LKMNQ": "zing",
    "PRT9X2C6YBMLV0F": "prathiksham",
    "BEE7W5ND34XQZRM": "beelittle"
}

def get_business_name(business_code: str) -> str:
    """Convert business code to business name."""
    return BUSINESS_CODE_MAP.get(business_code, None)