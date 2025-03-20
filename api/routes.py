def register_routes(app):
    """Register only the two core API routes"""
    from api.player import player_bp
    from api.chart import chart_bp

    # Register blueprints
    app.register_blueprint(player_bp)
    app.register_blueprint(chart_bp)

    # Add a health check endpoint
    @app.route('/')
    def health_check():
        return "API is running", 200