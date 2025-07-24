# app.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
import config

def create_app():
    app = FastAPI(
        title="ChefToan's API",
        description="""
        🚀 ChefToan's Multi-Purpose API Platform
        
        A modular API platform hosting various services and endpoints.
        
        📊 Available API Modules:
        - Clash of Clans: Player data, trophy charts, and statistics
        - Test: API testing endpoint with optimized image serving
        - More APIs: Additional modules can be easily added
        
        ⚡ Features:
        - High-performance caching for fast response times
        - Modular architecture for easy expansion
        - Optimized data structures for mobile apps
        - Real-time data tracking and processing
        
        🎯 Getting Started:
        1. Browse available API modules below
        2. Check the documentation for each endpoint
        3. Use the interactive API explorer to test endpoints
        """,
        version="2.0.0",
        docs_url="/",
        redoc_url="/redoc"
    )

    # Initialize Redis if it's enabled
    if config.REDIS_ENABLED:
        from src.core.redis_service import init_redis
        init_redis(app)
        print("Redis caching enabled")

    # Register API routes
    register_routes(app)

    # Add health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "ChefToan's API"}

    print("ChefToan's API server initialized successfully")
    return app

def register_routes(app):
    """Register all API routes from different modules"""
    
    # Import and register Clash of Clans API routes
    from src.apis.clash_of_clans.routes import clash_router
    app.include_router(clash_router)
    
    # Import and register Test API routes
    from src.apis.test.routes import test_router
    app.include_router(test_router)
    
    # Future API modules can be added here
    # from src.apis.other_api.routes import other_router
    # app.include_router(other_router)

app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=config.DEBUG)