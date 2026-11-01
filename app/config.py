import os

SECRET_KEY = os.getenv("SECRET_KEY", "nanova_infotech_super_secret_key_2025_safe_and_secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

default_db_path = "/tmp/incubation.db" if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "./incubation.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

# MongoDB Database Configuration (MongoDB Atlas Cloud Cluster)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://rajalingamrajesh70:GUD4mvvltKWWryZP@cluster0.btvmkuw.mongodb.net/?appName=Cluster0")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "nanova_infotech_db")

# Default admin emails allowed to access admin dashboard
DEFAULT_ADMIN_EMAILS = [
    "admin@nanovainfotech.com",
    "rajalingamrajesh70@gmail.com",
    "admin@incubation.com",
    "kalai@nayagi.com",
    "director@incubation.com"
]
