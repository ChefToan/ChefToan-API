from flask import Blueprint, jsonify, current_app, request, Response
import json
from src.services.clash_service import ClashApiClient
from src.services.player_essentials_service import PlayerEssentialsService

player_bp = Blueprint('player', __name__)


@player_bp.route('/player')
def get_player_info():
    """Get full player information directly from Clash of Clans API"""
    try:
        # Get player tag from query parameter
        player_tag = request.args.get('tag')
        if not player_tag:
            return jsonify({"error": "Missing player tag. Use ?tag=PLAYERTAG"}), 400

        # Initialize the Clash API client
        clash_client = ClashApiClient()

        # Standardize the player tag
        if not player_tag.startswith('#'):
            player_tag = '#' + player_tag
        player_tag = player_tag.upper()

        # Get player data
        player_data = clash_client.get_player(player_tag)

        return jsonify(player_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching player data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@player_bp.route('/player/essentials')
def get_player_essentials():
    """Get essential player information optimized for mobile app"""
    try:
        # Get player tag from query parameter
        player_tag = request.args.get('tag')
        if not player_tag:
            return jsonify({"error": "Missing player tag. Use ?tag=PLAYERTAG"}), 400

        # Initialize services
        clash_client = ClashApiClient()
        essentials_service = PlayerEssentialsService()

        # Standardize the player tag
        if not player_tag.startswith('#'):
            player_tag = '#' + player_tag
        player_tag = player_tag.upper()

        # Get player data
        player_data = clash_client.get_player(player_tag)

        # Extract and format essential data
        essential_data = essentials_service.format_player_essentials(player_data)

        # Use custom JSON serialization to preserve OrderedDict order
        json_str = json.dumps(essential_data, indent=2)
        return Response(json_str, mimetype='application/json')
    except Exception as e:
        current_app.logger.error(f"Error fetching player essentials: {str(e)}")
        return jsonify({"error": str(e)}), 500