from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_setup import router as setup_router
from app.api.routes_tasks import router as tasks_router
from app.config import settings

app = FastAPI(
    title="PATCHFORGE AI",
    description="Agentic software-engineering workflow: bug report to verified patch with human approval.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(setup_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "PATCHFORGE AI",
        "version": "1.0.0"
    }
