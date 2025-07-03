# src/api/player.py
from flask import Blueprint, jsonify, current_app, request, Response
import json
import time
from src.services.clash_service import ClashApiClient
from src.services.player_essentials_service import PlayerEssentialsService
from src.services.redis_service import cache_get, cache_set

player_bp = Blueprint('player', __name__)


@player_bp.route('/player')
def get_player_info():
    """Get full player information directly from Clash of Clans API"""
    start_time = time.time()

    try:
        # Get player tag from query parameter
        player_tag = request.args.get('tag')
        if not player_tag:
            return jsonify({"error": "Missing player tag. Use ?tag=PLAYERTAG"}), 400

        # Standardize the player tag
        if not player_tag.startswith('#'):
            player_tag = '#' + player_tag
        player_tag = player_tag.upper()

        # Check cache first
        cache_key = f"player_full:{player_tag}"
        cached_data = cache_get(cache_key)

        if cached_data is not None:
            response_time = time.time() - start_time
            current_app.logger.info(f"CACHED player data served in {response_time:.3f}s for {player_tag}")

            # Add performance headers
            response = jsonify(cached_data)
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
            return response

        # Cache miss - fetch from API
        current_app.logger.info(f"Cache MISS for full player data: {player_tag}")

        # Initialize the Clash API client
        clash_client = ClashApiClient()

        # Get player data
        api_start = time.time()
        player_data = clash_client.get_player(player_tag)
        api_time = time.time() - api_start

        # Cache the result for 5 minutes
        cache_set(cache_key, player_data, timeout=300)

        response_time = time.time() - start_time
        current_app.logger.info(
            f"FRESH player data served in {response_time:.3f}s (API: {api_time:.3f}s) for {player_tag}")

        # Add performance headers
        response = jsonify(player_data)
        response.headers['X-Cache'] = 'MISS'
        response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        response.headers['X-API-Time'] = f"{api_time:.3f}s"
        return response

    except Exception as e:
        response_time = time.time() - start_time
        current_app.logger.error(f"Error fetching player data in {response_time:.3f}s: {str(e)}")
        return jsonify({"error": str(e)}), 500


@player_bp.route('/player/essentials')
def get_player_essentials():
    """Get essential player information optimized for mobile app"""
    start_time = time.time()

    try:
        # Get player tag from query parameter
        player_tag = request.args.get('tag')
        if not player_tag:
            return jsonify({"error": "Missing player tag. Use ?tag=PLAYERTAG"}), 400

        # Standardize the player tag
        if not player_tag.startswith('#'):
            player_tag = '#' + player_tag
        player_tag = player_tag.upper()

        # Check cache for processed essentials data
        essentials_cache_key = f"player_essentials:{player_tag}"
        cached_essentials = cache_get(essentials_cache_key)

        if cached_essentials is not None:
            response_time = time.time() - start_time
            current_app.logger.info(f"CACHED essentials data served in {response_time:.3f}s for {player_tag}")

            # Use custom JSON serialization to preserve OrderedDict order
            json_str = json.dumps(cached_essentials, indent=2)
            response = Response(json_str, mimetype='application/json')
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
            return response

        # Cache miss - need to fetch and process data
        current_app.logger.info(f"Cache MISS for essentials data: {player_tag}")

        # Initialize services
        clash_client = ClashApiClient()
        essentials_service = PlayerEssentialsService()

        # Get player data (this call itself should be cached)
        api_start = time.time()
        player_data = clash_client.get_player(player_tag)
        api_time = time.time() - api_start

        # Extract and format essential data
        processing_start = time.time()
        essential_data = essentials_service.format_player_essentials(player_data)
        processing_time = time.time() - processing_start

        # Cache the processed essentials data for 5 minutes
        cache_set(essentials_cache_key, essential_data, timeout=300)

        response_time = time.time() - start_time
        current_app.logger.info(
            f"FRESH essentials data served in {response_time:.3f}s "
            f"(API: {api_time:.3f}s, Processing: {processing_time:.3f}s) for {player_tag}"
        )

        # Use custom JSON serialization to preserve OrderedDict order
        json_str = json.dumps(essential_data, indent=2)
        response = Response(json_str, mimetype='application/json')
        response.headers['X-Cache'] = 'MISS'
        response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        response.headers['X-API-Time'] = f"{api_time:.3f}s"
        response.headers['X-Processing-Time'] = f"{processing_time:.3f}s"
        return response

    except Exception as e:
        response_time = time.time() - start_time
        current_app.logger.error(f"Error fetching player essentials in {response_time:.3f}s: {str(e)}")
        return jsonify({"error": str(e)}), 500