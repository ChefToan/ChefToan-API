# src/utils/chart_generator.py
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import matplotlib.ticker as ticker


def generate_chart(player_info, daily_data, final_trophies, average_offense, average_defense, net_gain):
    """Creates a PNG chart in memory and returns a BytesIO buffer."""
    # Disable all default locators to prevent the MaxTicks error
    plt.rcParams['axes.formatter.use_locale'] = False
    plt.rcParams['axes.formatter.useoffset'] = False

    # Get the trophy range from the data
    trophy_data = [d.get('trophies') for d in daily_data if d.get('trophies') is not None]
    if trophy_data:
        min_trophies = min(trophy_data)
        max_trophies = max(trophy_data)

        # Include the final trophies in range calculation
        max_trophies = max(max_trophies, final_trophies)

        # Calculate the range of trophies
        trophy_range = max_trophies - min_trophies

        # Ensure there's always a minimum range
        if trophy_range < 100:
            min_trophies = min_trophies - 50
            max_trophies = max_trophies + 50
            trophy_range = max_trophies - min_trophies

        # Dynamically adjust figure height based on trophy range
        base_height = 7
        if trophy_range > 1500:
            height_factor = min(trophy_range / 1000, 3)  # Cap at 3x base height
            fig_height = base_height * height_factor
        else:
            fig_height = base_height

        fig = plt.figure(figsize=(12, fig_height), facecolor='white')
        gs = fig.add_gridspec(nrows=3, ncols=1, height_ratios=[0.2, 0.25, 0.55])
    else:
        # Default figure size if no data
        fig = plt.figure(figsize=(12, 7), facecolor='white')
        gs = fig.add_gridspec(nrows=3, ncols=1, height_ratios=[0.2, 0.25, 0.55])
        # Default trophy range for empty data
        min_trophies = 4800
        max_trophies = 5200

    ax_top = fig.add_subplot(gs[0, 0])
    ax_middle = fig.add_subplot(gs[1, 0])
    ax_chart = fig.add_subplot(gs[2, 0])

    # CRITICAL: Immediately set locators to prevent MaxTicks error
    ax_chart.yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

    # This special step prevents the date-related MaxTicks error
    ax_chart.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

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

        # Convert dates to matplotlib format
        x_dates_mpl = [mdates.date2num(datetime.datetime.combine(d, datetime.time())) for d in x_dates]

        # Plot the data directly with numbers and then format the axis
        ax_chart.plot(x_dates_mpl, y_trophies, marker='o', markersize=4, linewidth=2, color='#007bff', label='Trophies')

        # Calculate appropriate y-axis limits
        min_trophies = min(y_trophies)
        max_trophies = max(y_trophies)
        padding = max((max_trophies - min_trophies) * 0.1, 50)  # At least 50 trophies padding

        # Set y-axis limits with appropriate padding
        y_min = max(0, min_trophies - padding)  # Don't go below 0
        y_max = max_trophies + padding

        # Ensure final trophy count is visible in the plot
        if final_trophies > y_max:
            y_max = final_trophies + padding

        # Make sure limits are different enough
        if (y_max - y_min) < 100:
            y_min = max(0, y_min - 50)
            y_max = y_max + 50

        ax_chart.set_ylim([y_min, y_max])

        # IMPORTANT: Set fixed ticks for y-axis
        y_range = y_max - y_min
        if y_range <= 200:
            tick_step = 20
        elif y_range <= 500:
            tick_step = 50
        elif y_range <= 1000:
            tick_step = 100
        else:
            tick_step = 200

        ax_chart.yaxis.set_major_locator(ticker.MultipleLocator(tick_step))

        # Set x-axis limits to match the data range
        ax_chart.set_xlim([min(x_dates_mpl) - 0.5, max(x_dates_mpl) + 0.5])

        # Format the date on the x-axis
        date_formatter = mdates.DateFormatter('%m/%d')
        ax_chart.xaxis.set_major_formatter(date_formatter)

        # Set date ticks directly based on available dates
        if len(x_dates) <= 10:
            # If few dates, show all
            ax_chart.set_xticks(x_dates_mpl)
        else:
            # If many dates, calculate a reasonable interval
            n_ticks = min(10, len(x_dates))
            idx_step = len(x_dates) // n_ticks
            indices = range(0, len(x_dates), max(1, idx_step))
            ax_chart.set_xticks([x_dates_mpl[i] for i in indices])
    else:
        # If no data points, show a message
        ax_chart.text(0.5, 0.5, "No trophy data available",
                      fontsize=14, ha='center', va='center')
        # Set default y-axis limits
        ax_chart.set_ylim([4800, 5200])
        ax_chart.yaxis.set_major_locator(ticker.MultipleLocator(100))

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