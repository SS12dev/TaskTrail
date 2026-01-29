# Load environment variables before importing config
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.firebase import initialize_firebase
from app.routes import auth, test, tasks, projects, agent, a2a
from app.models.auth import HealthCheckResponse
import logging

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title="TaskTrail API",
    description="Task management API with Firebase Authentication and AI-powered task assistance",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI documentation
    redoc_url="/redoc"  # ReDoc documentation
)

# Configure CORS middleware to allow frontend requests
# This is essential for the React app to communicate with the API
# Allow both common development ports for flexibility
allowed_origins = [
    settings.frontend_url,
    "http://localhost:5173",  # Default Vite port
    "http://localhost:5174",  # Alternative port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.on_event("startup")
async def startup_event():
    """
    Initialize Firebase Admin SDK when the application starts.

    This event handler runs once when the FastAPI app starts up.
    It initializes the Firebase Admin SDK which is required for
    token verification and Firestore operations.
    """
    try:
        initialize_firebase()
        
        # Start background compaction scheduler
        from app.services.compaction_scheduler import get_compaction_scheduler
        scheduler = get_compaction_scheduler()
        scheduler.start()
        
        # Schedule global compaction at 3 AM daily
        scheduler.schedule_global_compaction(hour=3, minute=0)
        
        logger.info("Application startup completed successfully")
        logger.info("Background compaction scheduler initialized")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Frontend URL: {settings.frontend_url}")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Gracefully shutdown background services when the application stops.
    """
    try:
        from app.services.compaction_scheduler import get_compaction_scheduler
        scheduler = get_compaction_scheduler()
        scheduler.stop()
        logger.info("Background compaction scheduler stopped")
    except Exception as e:
        logger.warning(f"Error shutting down scheduler: {e}")


# Include API routers
# These routers contain all the endpoint definitions
app.include_router(auth.router, prefix="/api/v1")  # Auth endpoints at /api/v1/auth
app.include_router(test.router, prefix="/api/v1")  # Test endpoints at /api/v1/test
app.include_router(tasks.router, prefix="/api/v1")  # Task endpoints at /api/v1/tasks
app.include_router(projects.router, prefix="/api/v1")  # Project endpoints at /api/v1/projects
app.include_router(agent.router, prefix="/api/v1")  # Agent endpoints at /api/v1/agent

# Include A2A Protocol routes (NO prefix - uses specific A2A paths)
# A2A endpoints: /.well-known/agent-card.json, /a2a/v1/messages, /a2a/v1/ws
app.include_router(a2a.router)


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """
    Root endpoint - health check.

    This endpoint can be used to verify that the API is running
    and to check the current environment configuration.

    Returns:
        HealthCheckResponse with status and environment info
    """
    return {
        "status": "healthy",
        "message": "TaskTrail API is running",
        "environment": settings.environment
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        HealthCheckResponse with OK status
    """
    return {
        "status": "ok",
        "message": "Service is healthy",
        "environment": settings.environment
    }
