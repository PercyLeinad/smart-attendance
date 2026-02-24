from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import attendance, auth, reports
from core.ui import BASE_DIR

app = FastAPI()

# 1. Templates & Static Files Setups
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 2. Middleware
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 3. Include Routers
# Using 'tags' helps organize your automated /docs page
app.include_router(attendance.router, tags=["Attendance"])
app.include_router(auth.router, tags=["Authentication"])
app.include_router(reports.router, tags=["Reports"])

# 4. Root/Static Routes (Keep these simple)
@app.get("/")
def serve_default():
    return FileResponse(str(BASE_DIR / "templates" / "default.html"))

@app.get("/scan")
def serve_scan():
    return FileResponse(str(BASE_DIR / "templates" / "index.html"))


if __name__ == "__main__":
    print(BASE_DIR)