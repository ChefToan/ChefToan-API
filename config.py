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

# API Endpoints - Updated to use api.cheftoan.com
COC_API_BASE_URL = 'https://api.cheftoan.com'
CLASHPERK_BASE_URL = os.getenv('CLASHPERK_BASE_URL', 'https://api.clashperk.com')

# Redis configuration - FIXED with explicit defaults
REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'False').lower() == 'true'
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_CACHE_TIMEOUT = int(os.getenv('REDIS_CACHE_TIMEOUT', 3600))  # 1 hour default