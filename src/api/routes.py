def register_routes(app):
    """Register all API routes"""
    from src.api.player import player_router
    from src.api.chart import chart_router

    # Include routers
    app.include_router(player_router)
    app.include_router(chart_router)