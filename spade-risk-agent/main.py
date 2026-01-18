import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.router import router

# Configure logging for production monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="SPADE Risk Assessment Agent",
    description="Address-Based Vulnerability & Risk Assessment Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend integration
# Note: In production, restrict allow_origins to specific frontend domain(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: Replace with ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    """Basic API info"""
    return {
        "service": "SPADE Risk Assessment Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api": "/assess/"
    }


@app.get("/health")
def health_check():
    """Simple health check for monitoring/deployment"""
    return {
        "status": "healthy",
        "service": "SPADE Risk Assessment Agent"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all for unexpected errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if str(exc) else "An unexpected error occurred"
        }
    )


