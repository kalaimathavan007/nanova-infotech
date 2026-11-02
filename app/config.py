import os

SECRET_KEY = os.getenv("SECRET_KEY", "nanova_infotech_super_secret_key_2025_safe_and_secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

default_db_path = "/tmp/nanova.db" if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "./nanova.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

# MongoDB Database Configuration (MongoDB Atlas Cloud Cluster)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://rajalingamrajesh70:GUD4mvvltKWWryZP@cluster0.btvmkuw.mongodb.net/?appName=Cluster0")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "nanova_infotech_db")

# Master Admin Emails allowed to access Master Admin Dashboard & reply to messages
DEFAULT_ADMIN_EMAILS = [
    "kalaimathavan007@gmail.com",
    "admin@nanovainfotech.com"
]
