import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime


def generate_chart(player_info, daily_data, final_trophies, average_offense, average_defense, net_gain):
    """Creates a PNG chart in memory and returns a BytesIO buffer."""
    fig = plt.figure(figsize=(12, 7), facecolor='white')
    gs = fig.add_gridspec(nrows=3, ncols=1, height_ratios=[0.2, 0.25, 0.55])

    ax_top = fig.add_subplot(gs[0, 0])
    ax_middle = fig.add_subplot(gs[1, 0])
    ax_chart = fig.add_subplot(gs[2, 0])

    for ax in [ax_top, ax_middle]:
        ax.set_axis_off()

    # Top banner
    ax_top.set_xlim(0, 1)
    ax_top.set_ylim(0, 1)

    p_name = player_info.get('name', 'Unknown')
    p_tag = player_info.get('tag', '')
    c_name = player_info.get('clanName', 'No Clan')
    c_tag = player_info.get('clanTag', '')
    league_icon_url = player_info.get('leagueIconUrl', '')
    clan_badge_url = player_info.get('clanBadgeUrl', '')

    if league_icon_url:
        league_img = fetch_and_resize_image(league_icon_url, (80, 80))
        ax_top.imshow(league_img, extent=[0.01, 0.07, 0.2, 0.8], aspect='auto')

    ax_top.text(0.09, 0.65, p_name, fontsize=18, fontweight='bold', va='center', ha='left')
    ax_top.text(0.09, 0.40, p_tag, fontsize=12, va='center', ha='left', color='#555555')

    if clan_badge_url:
        clan_img = fetch_and_resize_image(clan_badge_url, (80, 80))
        ax_top.imshow(clan_img, extent=[0.93, 0.99, 0.2, 0.8], aspect='auto')

    ax_top.text(0.91, 0.65, c_name, fontsize=16, fontweight='bold', va='center', ha='right')
    ax_top.text(0.91, 0.40, c_tag, fontsize=12, va='center', ha='right', color='#555555')

    # Middle row
    ax_middle.set_xlim(0, 1)
    ax_middle.set_ylim(0, 1)
    ax_middle.text(0.5, 0.75, "Legend League Trophies Progression", fontsize=16, fontweight='bold', va='center',
                   ha='center')
    ax_middle.text(0.5, 0.55, player_info.get('seasonStr', ''), fontsize=12, va='center', ha='center', color='#333333')

    stats = [
        ("Avg Offense", f"+{average_offense:.0f}"),
        ("Avg Defense", f"-{average_defense:.0f}"),
        ("Avg Net Gain", f"{'+%.0f' % net_gain if net_gain >= 0 else '%.0f' % net_gain}"),
        ("Final Trophies", f"{final_trophies}")
    ]
    x_positions = [0.1, 0.33, 0.57, 0.80]
    for (label, value), x in zip(stats, x_positions):
        ax_middle.text(
            x, 0.25, f"{label}: {value}", fontsize=12, fontweight='bold',
            va='center', ha='left',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='black', alpha=0.8)
        )

    # Bottom chart
    ax_chart.set_facecolor('white')
    x_dates = []
    y_trophies = []

    for d in daily_data:
        # Skip data points without trophy information
        if d.get('trophies') is None:
            continue

        # Convert string date to datetime.date object if needed
        if isinstance(d.get('date'), str):
            try:
                date_obj = datetime.date.fromisoformat(d.get('date'))
            except ValueError:
                # If we can't parse the date, skip this data point
                continue
        else:
            # If it's already a date object, use it directly
            date_obj = d.get('date')

        x_dates.append(date_obj)
        y_trophies.append(d.get('trophies'))

    # Plot the data only if we have valid points
    if x_dates and y_trophies:
        # Sort data points by date
        sorted_data = sorted(zip(x_dates, y_trophies))
        x_dates, y_trophies = zip(*sorted_data)

        # Plot the data
        ax_chart.plot(x_dates, y_trophies, marker='o', markersize=4, linewidth=2, color='#007bff', label='Trophies')

        # Calculate appropriate y-axis limits
        min_trophies = min(y_trophies)
        max_trophies = max(y_trophies)
        padding = (max_trophies - min_trophies) * 0.1  # 10% padding

        # Set y-axis limits with appropriate padding
        y_min = max(4600, min_trophies - padding)
        y_max = min(6000, max_trophies + padding)

        # Ensure final trophy count is visible in the plot
        if final_trophies > y_max:
            y_max = final_trophies + padding

        ax_chart.set_ylim([y_min, y_max])

        # Create appropriate tick points based on the range
        range_size = y_max - y_min
        tick_step = 100 if range_size <= 600 else 200
        y_ticks = np.arange(np.floor(y_min / tick_step) * tick_step,
                            np.ceil(y_max / tick_step) * tick_step + 1,
                            tick_step)
        ax_chart.set_yticks(y_ticks)

        # Set the date format to MM/DD
        date_format = mdates.DateFormatter('%m/%d')
        ax_chart.xaxis.set_major_formatter(date_format)

        # Set the locator to show one tick per day
        ax_chart.xaxis.set_major_locator(mdates.DayLocator())
    else:
        # If no data points, show a message
        ax_chart.text(0.5, 0.5, "No trophy data available",
                      fontsize=14, ha='center', va='center')
        # Set default y-axis limits
        ax_chart.set_ylim([4800, 6000])

    ax_chart.set_xlabel("Date", fontsize=12, fontweight='bold')
    ax_chart.set_ylabel("Trophies", fontsize=12, fontweight='bold')
    plt.setp(ax_chart.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax_chart.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)

    fig.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf


def fetch_and_resize_image(url, size):
    """Fetch an image from a URL and resize it. Returns a PIL Image."""
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        img = img.resize(size, Image.Resampling.LANCZOS)
        return img
    except Exception:
        return Image.new('RGBA', size, (255, 255, 255, 0))