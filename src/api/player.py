from flask import Blueprint, jsonify, current_app
from src.services.clash_service import ClashApiClient

player_bp = Blueprint('player', __name__)


@player_bp.route('/player/<player_tag>')
def get_player_info(player_tag):
    """Get player information directly from Clash of Clans API"""
    try:
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