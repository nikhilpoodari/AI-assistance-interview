import os
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_mongo_client():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    return MongoClient(uri)

def get_users_collection():
    client = get_mongo_client()
    db_name = os.getenv("MONGODB_DB", "interview_bot")
    return client[db_name]["users"]

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except Exception:
        return False

def create_user(full_name: str, email: str, password: str) -> bool:
    users = get_users_collection()
    if users.find_one({"email": email}):
        return False
    doc = {
        "full_name": full_name,
        "email": email,
        "password": hash_password(password),
    }
    users.insert_one(doc)
    return True

def verify_user(email: str, password: str) -> bool:
    users = get_users_collection()
    user = users.find_one({"email": email})
    if not user:
        return False
    return check_password(password, user.get("password", b""))


