from flask import Blueprint, jsonify, current_app, request
from src.services.clash_service import ClashApiClient

player_bp = Blueprint('player', __name__)


@player_bp.route('/player')
def get_player_info():
    """Get player information directly from Clash of Clans API"""
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