from flask import Flask, send_file
from data_fetcher import get_player_data
from chart_generator import generate_chart

app = Flask(__name__)


@app.route('/chart/<player_tag>')
def chart(player_tag):
    # Handle both with and without # prefix
    if not player_tag.startswith('#'):
        player_tag = '#' + player_tag

    player_tag = player_tag.upper()
    try:
        player_info, daily_data, final_trophies, avg_offense, avg_defense, net_gain = get_player_data(player_tag)
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
        # Add logging for debugging
        import traceback
        print(f"Error processing request: {str(e)}")
        print(traceback.format_exc())
        return str(e), 500


# For local development purposes, add a health check endpoint
@app.route('/')
def health_check():
    return "API is running", 200


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5001)