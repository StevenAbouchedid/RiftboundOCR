"""
Main FastAPI Application
RiftboundOCR Service - Convert Chinese decklist screenshots to structured deck data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

from src.api.routes import router
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.enable_logging else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware - Allow all origins for now (can restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    try:
        logger.info("=" * 60)
        logger.info(f"🚀 {settings.app_name} v{settings.app_version}")
        logger.info("=" * 60)
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"GPU enabled: {settings.use_gpu}")
        logger.info(f"Card mapping: {settings.card_mapping_path}")
        logger.info(f"Max file size: {settings.max_file_size_mb}MB")
        logger.info(f"Max batch size: {settings.max_batch_size}")
        logger.info("=" * 60)
        logger.info("✓ Application startup complete")
        
        # Start background keep-alive logger
        import asyncio
        asyncio.create_task(keep_alive_logger())
    except Exception as e:
        logger.error(f"❌ Startup error: {e}", exc_info=True)
        raise


async def keep_alive_logger():
    """Log periodic keep-alive messages to detect crashes"""
    import asyncio
    import time
    start_time = time.time()
    counter = 0
    
    while True:
        await asyncio.sleep(60)  # Log every 60 seconds
        counter += 1
        uptime = int(time.time() - start_time)
        logger.info(f"💓 Keep-alive #{counter} - Uptime: {uptime}s ({uptime//60}m {uptime%60}s)")
        
        # Log memory usage if available
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=1)
            logger.info(f"📊 Resources: Memory={memory_mb:.1f}MB, CPU={cpu_percent:.1f}%")
        except:
            pass


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Service shutting down...")


@app.get("/")
async def root():
    """
    Root endpoint
    
    Returns basic service information and links
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
        "stats": "/api/v1/stats",
        "endpoints": {
            "process_single": "POST /api/v1/process",
            "process_batch": "POST /api/v1/process-batch",
            "health": "GET /api/v1/health",
            "stats": "GET /api/v1/stats"
        }
    }


@app.get("/health")
async def health_simple():
    """
    Simple health check endpoint (root level for frontend compatibility)
    
    Returns basic status - for full info use /api/v1/health
    """
    # Return plain dict - let CORS middleware add headers
    import time
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred processing your request"
        }
    )


# Include API routes with prefix
app.include_router(router, prefix="/api/v1", tags=["OCR"])

# Development server
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting development server on {settings.service_host}:{settings.service_port}")
    logger.info(f"Main backend API expected on port 8000 or 8001")
    
    uvicorn.run(
        "src.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.debug,
        log_level="info" if settings.enable_logging else "warning"
    )

