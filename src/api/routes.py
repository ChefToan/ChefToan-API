from flask import jsonify

def register_routes(app):
    """Register all API routes"""
    from src.api.player import player_bp
    from src.api.chart import chart_bp

    # Register blueprints
    app.register_blueprint(player_bp)
    app.register_blueprint(chart_bp)

    # Add a health check endpoint with API documentation
    @app.route('/')
    def health_check():
        return jsonify({
            "status": "API is running",
            "endpoints": {
                "player_full": "/player?tag=PLAYERTAG - Get full player information",
                "player_essentials": "/player/essentials?tag=PLAYERTAG - Get essential player data (optimized for mobile)",
                "chart": "/chart?tag=PLAYERTAG - Generate trophy progression chart"
            },
            "examples": {
                "player_full": "/player?tag=%23ABCDEF123",
                "player_essentials": "/player/essentials?tag=%23ABCDEF123",
                "chart": "/chart?tag=%23ABCDEF123"
            },
            "performance_notes": {
                "player_essentials": "Recommended for mobile apps - smaller payload, faster loading, includes hero equipment",
                "player_full": "Complete data from Clash of Clans API - larger payload",
                "caching": "All endpoints use Redis caching for improved performance"
            },
            "note": "Player tags should be URL encoded (# becomes %23) or can be provided without the # symbol"
        }), 200