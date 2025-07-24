# app.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.api.routes import register_routes
import config

def create_app():
    app = FastAPI(
        title="Clash of Clans Legend League API",
        description="""
        API for tracking Clash of Clans player statistics and trophy progression.
        
        **🚀 Getting Started:**
        1. Use the `/player/essentials` endpoint for optimized player data
        2. Use the `/player` endpoint for complete player information
        3. Use the `/chart` endpoint to generate trophy progression charts
        
        **📊 Available Endpoints:**
        - **Player Essentials**: Optimized data for mobile applications
        - **Full Player Data**: Complete player information from Clash of Clans API
        - **Trophy Charts**: Visual trophy progression for Legend League players
        
        **⚡ Features:**
        - High-performance caching for fast response times
        - Optimized data structures for mobile apps
        - Real-time trophy progression tracking
        """,
        version="1.0.0",
        docs_url="/",
        redoc_url="/redoc"
    )

    # Initialize Redis if it's enabled
    if config.REDIS_ENABLED:
        from src.services.redis_service import init_redis
        init_redis(app)
        print("Redis caching enabled")

    # Register API routes
    register_routes(app)

    print("API server initialized successfully")
    return app

app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=config.DEBUG)