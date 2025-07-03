# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask settings
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
HOST = os.getenv('HOST', 'localhost')
PORT = int(os.getenv('PORT', 5001))

# API Keys
COC_API_TOKEN = os.getenv('COC_API_TOKEN', '')
CLASHPERK_API_TOKEN = os.getenv('CLASHPERK_API_TOKEN', '')

# API Endpoints
COC_API_BASE_URL = os.getenv('COC_API_BASE_URL', 'https://api.clashofclans.com/v1')
CLASHPERK_BASE_URL = os.getenv('CLASHPERK_BASE_URL', 'https://api.clashperk.com')

# Redis configuration - OPTIMIZED FOR PERFORMANCE
REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'True').lower() == 'true'  # Enable by default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Cache timeouts (in seconds) - Optimized for speed vs freshness balance
REDIS_CACHE_TIMEOUT = int(os.getenv('REDIS_CACHE_TIMEOUT', 300))  # 5 minutes default

# Specific cache timeouts for different data types
CACHE_TIMEOUTS = {
    'player_data': int(os.getenv('CACHE_PLAYER_DATA', 300)),        # 5 minutes - player data changes slowly
    'player_essentials': int(os.getenv('CACHE_PLAYER_ESSENTIALS', 300)),  # 5 minutes - processed data
    'chart_image': int(os.getenv('CACHE_CHART_IMAGE', 600)),        # 10 minutes - charts are expensive to generate
    'legend_attacks': int(os.getenv('CACHE_LEGEND_ATTACKS', 900)),  # 15 minutes - attack data
    'clashking_data': int(os.getenv('CACHE_CLASHKING_DATA', 600)),  # 10 minutes - ranking data
    'combined_player_data': int(os.getenv('CACHE_COMBINED_DATA', 1800))  # 30 minutes - expensive combined data
}

# Request timeout settings
API_REQUEST_TIMEOUT = int(os.getenv('API_REQUEST_TIMEOUT', 10))  # 10 seconds for external APIs
CHART_GENERATION_TIMEOUT = int(os.getenv('CHART_GENERATION_TIMEOUT', 30))  # 30 seconds for chart generation

# Flask-specific optimizations
JSON_SORT_KEYS = False  # Don't sort JSON keys for better performance
JSONIFY_PRETTYPRINT_REGULAR = DEBUG  # Only pretty print in debug mode