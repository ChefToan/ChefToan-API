# src/api/chart.py
from flask import Blueprint, send_file, current_app, request
from src.services.data_fetcher import get_player_data
from src.utils.chart_generator import generate_chart
from src.services.clash_service import ServiceUnavailableError, PlayerNotFoundError, AuthenticationError

chart_bp = Blueprint('chart', __name__)


@chart_bp.route('/chart')
def get_player_chart():
    """Generate and return a chart for the player's trophy progress"""
    try:
        # Get player tag from query parameter
        player_tag = request.args.get('tag')
        if not player_tag:
            return generate_error_image(
                "Missing Player Tag",
                "Please provide a player tag using ?tag=PLAYERTAG",
                400
            )

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

    except ServiceUnavailableError as e:
        # Handle service unavailable errors (like 503)
        current_app.logger.error(f"External API unavailable: {str(e)}")
        return generate_error_image(
            "Service Temporarily Unavailable",
            "The Clash of Clans API is currently down. Please try again later.",
            503
        )

    except PlayerNotFoundError as e:
        # Handle player not found errors
        current_app.logger.error(f"Player not found: {str(e)}")
        return generate_error_image(
            "Player Not Found",
            f"Could not find player with tag {player_tag}. Please check the tag and try again.",
            404
        )

    except AuthenticationError as e:
        # Handle authentication errors
        current_app.logger.error(f"API authentication error: {str(e)}")
        return generate_error_image(
            "API Authentication Error",
            "Failed to authenticate with the Clash of Clans API. Please check API token configuration.",
            500
        )

    except Exception as e:
        # Handle all other exceptions
        current_app.logger.error(f"Error generating chart: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return generate_error_image(
            "Error Generating Chart",
            "An unexpected error occurred. Please try again later.",
            500
        )


def generate_error_image(title, message, status_code):
    """Generate a simple error image with a message"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.6, title, fontsize=24, ha='center', va='center', fontweight='bold')
    ax.text(0.5, 0.4, message, fontsize=16, ha='center', va='center')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, facecolor='#f7f7f7')
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png'), status_code