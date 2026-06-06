import time
import requests
import threading
import os
import logging

logger = logging.getLogger(__name__)

def start_ping_loop():
    """
    Starts the keep-alive ping loop in a background daemon thread.
    """
    # Create the thread
    thread = threading.Thread(target=_ping_loop, daemon=True)
    thread.start()
    logger.info("Background keep-alive ping service started.")

def _ping_loop():
    """
    The background loop that pings the application endpoint every 10 minutes.
    """
    # Wait 30 seconds initially for the server to finish starting up
    time.sleep(30)
    
    # Check for APP_URL first, then RAILWAY_STATIC_URL
    app_url = os.environ.get("APP_URL")
    if not app_url:
        railway_url = os.environ.get("RAILWAY_STATIC_URL")
        if railway_url:
            # Railway static URLs don't include protocol
            if not railway_url.startswith("http"):
                app_url = f"https://{railway_url}"
            else:
                app_url = railway_url

    if not app_url:
        logger.warning(
            "Auto-ping: Neither APP_URL nor RAILWAY_STATIC_URL environment variables are configured. "
            "Auto-ping keep-alive service is inactive. "
            "Please set the APP_URL environment variable (e.g., https://your-app.up.railway.app) to enable this feature."
        )
        return

    # Normalize url (remove trailing slash)
    if app_url.endswith("/"):
        app_url = app_url[:-1]
        
    health_endpoint = f"{app_url}/api/health"
    logger.info(f"Auto-ping: Keep-alive configured to target: {health_endpoint}")
    
    # Ping interval in seconds (10 minutes)
    interval = int(os.environ.get("PING_INTERVAL", "600"))
    
    while True:
        try:
            logger.info(f"Auto-ping: Sending keep-alive request to {health_endpoint}")
            response = requests.get(health_endpoint, timeout=10)
            logger.info(f"Auto-ping: Keep-alive response status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Auto-ping: Keep-alive request failed: {str(e)}")
            
        time.sleep(interval)
