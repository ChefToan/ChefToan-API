from flask import Flask, send_file
from data_fetcher import get_player_data
from chart_generator import generate_chart

app = Flask(__name__)

@app.route('/chart/<player_tag>')
def chart(player_tag):
    player_tag = player_tag.upper()
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

if __name__ == '__main__':
    app.run(debug=True)
