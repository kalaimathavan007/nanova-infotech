import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.database import engine, Base
from app import models, mongo_dal
from app.routers import auth_router, admin_router, team_router, chat_router

# Initialize database tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database initialization notice: {e}")

app = FastAPI(
    title="Nanova Infotech Workspace API",
    description="Internal Team & Messaging Portal for Nanova Infotech",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB seeding function
@app.on_event("startup")
def startup_db_seed():
    try:
        mongo_dal.init_mongo_db()
    except Exception as e:
        print(f"MongoDB startup notice: {e}")

# Register Routers
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(team_router.router)
app.include_router(chat_router.router)

# Base project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Frontend & static directories
frontend_dir = os.path.join(BASE_DIR, "frontend")
static_dir = os.path.join(BASE_DIR, "static")

# Mount frontend/static directories for assets
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
elif os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Dedicated Guaranteed Logo Endpoints
@app.get("/logo.svg")
@app.get("/logo.jpg")
@app.get("/logo.png")
@app.get("/static/images/logo.svg")
@app.get("/static/images/logo.png")
@app.get("/static/images/logo.jpg")
@app.get("/images/logo.svg")
@app.get("/images/logo.png")
@app.get("/images/logo.jpg")
def serve_logo():
    paths = [
        os.path.join(frontend_dir, "images", "logo.png"),
        os.path.join(static_dir, "images", "logo.png"),
        os.path.join(frontend_dir, "images", "logo.jpg"),
        os.path.join(static_dir, "images", "logo.jpg"),
        os.path.join(frontend_dir, "images", "logo.svg"),
        os.path.join(static_dir, "images", "logo.svg"),
        os.path.join(frontend_dir, "logo.png"),
        os.path.join(static_dir, "logo.png"),
        os.path.join(frontend_dir, "logo.jpg"),
        os.path.join(static_dir, "logo.jpg"),
        os.path.join(frontend_dir, "logo.svg"),
        os.path.join(static_dir, "logo.svg")
    ]
    for p in paths:
        if os.path.exists(p):
            ext = os.path.splitext(p)[1].lower()
            media = "image/png" if ext == ".png" else ("image/jpeg" if ext in [".jpg", ".jpeg"] else "image/svg+xml")
            return FileResponse(p, media_type=media)
    return {"error": "Logo not found"}

@app.get("/splash.mp4")
@app.get("/images/splash.mp4")
@app.get("/static/images/splash.mp4")
def serve_splash_video():
    paths = [
        os.path.join(frontend_dir, "images", "splash.mp4"),
        os.path.join(static_dir, "images", "splash.mp4"),
        os.path.join(frontend_dir, "splash.mp4"),
        os.path.join(static_dir, "splash.mp4")
    ]
    for p in paths:
        if os.path.exists(p):
            return FileResponse(p, media_type="video/mp4")
    return {"error": "Splash video not found"}

@app.get("/")
def serve_home():
    index_file = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(index_file):
        index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Welcome to Nayagi Incubation Center Backend API. Visit /docs for OpenAPI documentation."}

@app.get("/admin.html")
def serve_admin():
    file_path = os.path.join(frontend_dir, "admin.html")
    if not os.path.exists(file_path):
        file_path = os.path.join(static_dir, "admin.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return RedirectResponse(url="/")

@app.get("/dashboard.html")
def serve_dashboard():
    file_path = os.path.join(frontend_dir, "dashboard.html")
    if not os.path.exists(file_path):
        file_path = os.path.join(static_dir, "dashboard.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return RedirectResponse(url="/")
