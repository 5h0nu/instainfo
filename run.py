import uvicorn
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Railway passes the port to bind to via the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    
    # Disable auto-reload in production environments to reduce resources and maximize performance
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None
    is_prod = os.environ.get("ENVIRONMENT", "").lower() == "production"
    
    reload = not (is_railway or is_prod)
    
    logger.info(f"Starting InstaScope API on 0.0.0.0:{port} (reload={reload})")
    
    # Run uvicorn server
    # host='0.0.0.0' allows external routing, critical for cloud environments like Railway
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info"
    )
