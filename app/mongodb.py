import os
import pymongo
from pymongo import MongoClient
try:
    import certifi
    has_certifi = True
except ImportError:
    has_certifi = False

from app.config import MONGODB_URL, MONGODB_DB_NAME

# Synchronous PyMongo Client for background tasks & seeding
mongo_client = None
mongo_db = None
connection_attempted = False

def get_mongo_db():
    global mongo_client, mongo_db, connection_attempted
    if mongo_db is not None:
        return mongo_db

    try:
        connection_kwargs = {
            "serverSelectionTimeoutMS": 1500,
            "connectTimeoutMS": 1500
        }
        if "mongodb+srv://" in MONGODB_URL or "ssl=true" in MONGODB_URL.lower():
            if has_certifi:
                connection_kwargs["tlsCAFile"] = certifi.where()
            connection_kwargs["tlsAllowInvalidCertificates"] = True

        client = MongoClient(MONGODB_URL, **connection_kwargs)
        # Test connection ping with quick timeout
        client.admin.command('ping')
        mongo_client = client
        mongo_db = mongo_client[MONGODB_DB_NAME]
        print(f"🍃 MongoDB Connected successfully to database: '{MONGODB_DB_NAME}'")
        return mongo_db
    except Exception as e:
        if not connection_attempted:
            print(f"⚠️ MongoDB Atlas Notice: Could not connect to Atlas URL ({e}).")
            print("💡 Tip: In MongoDB Atlas Dashboard, make sure Network Access has 0.0.0.0/0 (Allow from anywhere) enabled.")
            connection_attempted = True

        # Fallback to local MongoDB if available
        try:
            local_client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
            local_client.admin.command('ping')
            mongo_client = local_client
            mongo_db = local_client[MONGODB_DB_NAME]
            print(f"🍃 Connected to Local MongoDB database: '{MONGODB_DB_NAME}'")
            return mongo_db
        except Exception:
            return None

def is_mongodb_connected() -> bool:
    try:
        db = get_mongo_db()
        return db is not None
    except Exception:
        return False
