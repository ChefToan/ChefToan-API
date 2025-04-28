from flask import Flask
from src.api.routes import register_routes
import config


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config)

    # Initialize Redis if it's enabled
    if app.config.get('REDIS_ENABLED', False):
        from src.services.redis_service import init_redis
        init_redis(app)

    # Register API routes
    register_routes(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config.get('DEBUG', False),
            host=app.config.get('HOST', 'localhost'),
            port=app.config.get('PORT', 5001))