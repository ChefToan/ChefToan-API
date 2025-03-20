from flask import Blueprint, send_file, current_app
from services.data_fetcher import get_player_data
from utils.chart_generator import generate_chart

chart_bp = Blueprint('chart', __name__)


@chart_bp.route('/chart/<player_tag>')
def get_player_chart(player_tag):
    """Generate and return a chart for the player's trophy progress"""
    try:
        # Standardize the player tag
        if not player_tag.startswith('#'):
            player_tag = '#' + player_tag
        player_tag = player_tag.upper()

        # Get player data
        player_info, daily_data, final_trophies, avg_offense, avg_defense, net_gain = get_player_data(player_tag)

        # Generate chart
        chart_buf = generate_chart(
            player_info=player_info,
            daily_data=daily_data,
            final_trophies=final_trophies,
            average_offense=avg_offense,
            average_defense=avg_defense,
            net_gain=net_gain
        )

        return send_file(chart_buf, mimetype='image/png')
    except Exception as e:
        current_app.logger.error(f"Error generating chart: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return str(e), 500