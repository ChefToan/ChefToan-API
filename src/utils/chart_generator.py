# src/utils/chart_generator.py - CLEAN VERSION (No Debug Lines)
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
        gs = fig.add_gridspec(nrows=3, ncols=1, height_ratios=[0.20, 0.23, 0.57], hspace=0.025)
    else:
        # Default figure size if no data
        fig = plt.figure(figsize=(12, 7), facecolor='white')
        gs = fig.add_gridspec(nrows=3, ncols=1, height_ratios=[0.20, 0.23, 0.57], hspace=0.025)
        # Default trophy range for empty data
        min_trophies = 4800
        max_trophies = 5200

    ax_top = fig.add_subplot(gs[0, 0])
    ax_middle = fig.add_subplot(gs[1, 0])
    ax_chart = fig.add_subplot(gs[2, 0])

    # CRITICAL: Immediately set locators to prevent MaxTicks error
    ax_chart.yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
    ax_chart.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

    for ax in [ax_top, ax_middle]:
        ax.set_axis_off()

    # Top banner with improved layout
    ax_top.set_xlim(0, 1)
    ax_top.set_ylim(0, 1)

    p_name = player_info.get('name', 'Unknown')
    p_tag = player_info.get('tag', '')
    c_name = player_info.get('clanName', 'No Clan')
    c_tag = player_info.get('clanTag', '')
    league_icon_url = player_info.get('leagueIconUrl', '')
    clan_badge_url = player_info.get('clanBadgeUrl', '')

    # PLAYER INFO GROUP (Left side, centered around 0.2)
    player_group_center = 0.10
    icon_width = 0.08  # Width of icon area
    icon_height = 0.6  # Height of icon (60% of available height)
    icon_spacing = 0.03  # Space between icon and text

    if league_icon_url:
        league_img = fetch_and_resize_image(league_icon_url, (80, 80))  # Back to original size
        # Position icon: centered around player_group_center, shifted left
        icon_left = player_group_center - (icon_width / 2) - icon_spacing - 0.02
        icon_right = icon_left + icon_width
        icon_bottom = (1 - icon_height) / 2
        icon_top = icon_bottom + icon_height
        ax_top.imshow(league_img, extent=[icon_left, icon_right, icon_bottom, icon_top], aspect='auto')
        text_start_x = icon_right + 0.015
    else:
        text_start_x = player_group_center - 0.15

    # Player text (right of icon, with proper spacing)
    ax_top.text(text_start_x, 0.65, p_name, fontsize=17, fontweight='bold', va='center', ha='left')
    ax_top.text(text_start_x, 0.35, p_tag, fontsize=12, va='center', ha='left', color='#555555')

    # CLAN INFO GROUP (Right side, centered around 0.75)
    clan_group_center = 0.85

    if clan_badge_url:
        clan_img = fetch_and_resize_image(clan_badge_url, (80, 80))  # Back to original size
        # Position badge: centered around clan_group_center, shifted right
        badge_right = clan_group_center + (icon_width / 2) + icon_spacing + 0.02
        badge_left = badge_right - icon_width
        badge_bottom = (1 - icon_height) / 2
        badge_top = badge_bottom + icon_height
        ax_top.imshow(clan_img, extent=[badge_left, badge_right, badge_bottom, badge_top], aspect='auto')
        text_end_x = badge_left - 0.015
    else:
        text_end_x = clan_group_center + 0.15

    # Clan text (left of badge, with proper spacing)
    ax_top.text(text_end_x, 0.65, c_name, fontsize=17, fontweight='bold', va='center', ha='right')
    ax_top.text(text_end_x, 0.35, c_tag, fontsize=12, va='center', ha='right', color='#555555')

    # Middle section with improved layout
    ax_middle.set_xlim(0, 1)
    ax_middle.set_ylim(0, 1)

    # Main title - positioned higher and smaller for compact layout
    ax_middle.text(0.5, 0.85, "Legend League Trophies Progression", fontsize=18, fontweight='bold',
                   va='center', ha='center')

    # Season info - positioned closer to title and smaller
    ax_middle.text(0.5, 0.60, player_info.get('seasonStr', ''), fontsize=14, va='center',
                   ha='center', color='#333333')

    # Stats section with improved spacing and styling
    stats = [
        ("Avg Offense", f"+{average_offense:.0f}"),
        ("Avg Defense", f"-{average_defense:.0f}"),
        ("Avg Net Gain", f"{'+%.0f' % net_gain if net_gain >= 0 else '%.0f' % net_gain}"),
        ("Final Trophies", f"{final_trophies}")
    ]

    # Position stats more centrally with better spacing
    total_stats_width = 0.8  # Use 80% of available width
    start_x = (1 - total_stats_width) / 2  # Center the stats
    stat_spacing = total_stats_width / len(stats)

    for i, (label, value) in enumerate(stats):
        x_pos = start_x + (i * stat_spacing) + (stat_spacing / 2)

        # Color code the stat boxes
        if "Offense" in label:
            box_color = '#e8f5e8'
            border_color = '#4caf50'
        elif "Defense" in label:
            box_color = '#ffe8e8'
            border_color = '#f44336'
        elif "Net Gain" in label:
            box_color = '#e8f4fd' if net_gain >= 0 else '#ffe8e8'
            border_color = '#2196f3' if net_gain >= 0 else '#f44336'
        else:  # Final Trophies
            box_color = '#fff3e0'
            border_color = '#ff9800'

        ax_middle.text(
            x_pos, 0.25, f"{label}\n{value}", fontsize=12, fontweight='bold',
            va='center', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=box_color,
                      edgecolor=border_color, alpha=0.9, linewidth=1.5)
        )

    # Bottom chart with improved styling
    ax_chart.set_facecolor('#fafafa')  # Light background
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

        # Plot with improved styling
        ax_chart.plot(x_dates_mpl, y_trophies, marker='o', markersize=5, linewidth=2.5,
                      color='#1976d2', label='Trophies', markerfacecolor='white',
                      markeredgecolor='#1976d2', markeredgewidth=2)

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

    # Improved axis labels and styling
    ax_chart.set_xlabel("Date", fontsize=13, fontweight='bold', color='#333')
    ax_chart.set_ylabel("Trophies", fontsize=13, fontweight='bold', color='#333')
    plt.setp(ax_chart.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=10)
    plt.setp(ax_chart.yaxis.get_majorticklabels(), fontsize=10)

    # Improved grid
    ax_chart.grid(color='gray', linestyle='--', linewidth=0.6, alpha=0.6)
    ax_chart.set_axisbelow(True)  # Put grid behind the plot

    # Add subtle border around the chart
    for spine in ax_chart.spines.values():
        spine.set_edgecolor('#cccccc')
        spine.set_linewidth(1)

    # fig.tight_layout(pad=0.5)  # Reduced padding for tighter layout
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white', pad_inches=0.1)
    buf.seek(0)
    plt.close(fig)
    return buf


def fetch_and_resize_image(url, size):
    """Fetch an image from a URL and resize it. Returns a PIL Image."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        img = img.resize(size, Image.Resampling.LANCZOS)
        return img
    except Exception:
        return Image.new('RGBA', size, (255, 255, 255, 0))