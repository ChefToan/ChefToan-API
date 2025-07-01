from flask import jsonify

def register_routes(app):
    """Register only the two core API routes"""
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
                "player": "/player?tag=PLAYERTAG - Get player information",
                "chart": "/chart?tag=PLAYERTAG - Generate trophy progression chart"
            },
            "examples": {
                "player": "/player?tag=%23ABCDEF123",
                "chart": "/chart?tag=%23ABCDEF123"
            },
            "note": "Player tags should be URL encoded (# becomes %23) or can be provided without the # symbol"
        }), 200