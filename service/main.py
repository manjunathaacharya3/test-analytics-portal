from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import database
from database.database import init_engine, init_db
from service.apis.execution import router as execution_router
from service.apis.projects import router as project_router
from service.apis.report import router as report_router
from service.cucumber_parser import CucumberParser

# ----------------------------
# App Initialization
# ----------------------------
app = FastAPI(title="Test Report Portal API", version="1.0.0")

# CORS middleware (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cucumber parser
cucumber_parser = CucumberParser()
app.include_router(project_router)
app.include_router(report_router)
app.include_router(execution_router)


@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Test Report Portal API...")
    await init_engine()
    await init_db()
    print(f"✅ Database initialized! Using backend: {str(database.engine.url)}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": str(database.engine.url) if database.engine else "not initialized",
        "timestamp": datetime.now().isoformat(),
    }


# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
