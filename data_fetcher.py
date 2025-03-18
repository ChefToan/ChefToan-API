import os
import requests
import datetime
from datetime import timezone, timedelta
import calendar

# Load environment variables (if using python-dotenv)
from dotenv import load_dotenv
load_dotenv()

COC_API_TOKEN = os.getenv("COC_API_TOKEN", "")
CLASHPERK_API_TOKEN = os.getenv("CLASHPERK_API_TOKEN", "")
CLASHPERK_BASE_URL = 'https://api.clashperk.com'

def get_player_data(player_tag):
    """Fetch and compute daily data from CoC & ClashPerk APIs."""
    coc_url = f'https://api.clashofclans.com/v1/players/{player_tag.replace("#", "%23")}'
    headers_coc = {'Authorization': f'Bearer {COC_API_TOKEN}'}
    resp_coc = requests.get(coc_url, headers=headers_coc)
    if resp_coc.status_code != 200:
        raise Exception(f"Error from CoC API: {resp_coc.text}")
    player_json = resp_coc.json()

    player_name = player_json.get('name', 'Unknown')
    player_actual_tag = player_json.get('tag', player_tag)
    clan_name = ''
    clan_badge_url = ''
    clan_tag = ''
    if 'clan' in player_json:
        clan_name = player_json['clan'].get('name', '')
        clan_badge_url = player_json['clan']['badgeUrls'].get('small', '')
        clan_tag = player_json['clan'].get('tag', '')

    league_icon_url = ''
    if 'league' in player_json and 'iconUrls' in player_json['league']:
        league_icon_url = player_json['league']['iconUrls'].get('small', '')

    perk_url = f'{CLASHPERK_BASE_URL}/players/legend-attacks/{player_tag.replace("#", "%23")}'
    headers_perk = {'Authorization': f'Bearer {CLASHPERK_API_TOKEN}'}
    resp_perk = requests.get(perk_url, headers=headers_perk)
    if resp_perk.status_code != 200:
        raise Exception(f"Error from ClashPerk API: {resp_perk.text}")

    perk_json = resp_perk.json()
    logs = perk_json.get('logs', [])
    final_trophies = perk_json.get('trophies', 0)
    initial_trophies = perk_json.get('initial', 0)
    season_id = perk_json.get('seasonId', '')

    if season_id:
        start_date, end_date = get_season_start_end(season_id)
        season_str = make_season_string(season_id, start_date, end_date)
    else:
        start_date = datetime.datetime(2025, 2, 24, 5, 0, 0, tzinfo=timezone.utc)
        end_date   = datetime.datetime(2025, 3, 31, 5, 0, 0, tzinfo=timezone.utc)
        season_str = "Unknown Season"

    current_trophies = initial_trophies
    daily_data = []
    sum_offense = 0
    sum_defense = 0
    day_count = 0

    current_day = start_date
    while current_day < end_date:
        next_day = current_day + timedelta(days=1)
        day_offense = 0
        day_defense = 0
        day_has_logs = False

        for log_item in logs:
            ts = log_item.get('timestamp', 0)
            action_type = log_item.get('type', '')
            inc = log_item.get('inc', 0)
            log_time = datetime.datetime.utcfromtimestamp(ts / 1000).replace(tzinfo=timezone.utc)

            if current_day <= log_time < next_day:
                day_has_logs = True
                if action_type == 'attack':
                    day_offense += inc
                    current_trophies += inc
                elif action_type == 'defense':
                    day_defense += abs(inc)
                    current_trophies += inc

        if day_has_logs:
            daily_data.append({
                'date': current_day.date(),
                'offense': day_offense,
                'defense': day_defense,
                'trophies': current_trophies
            })
            sum_offense += day_offense
            sum_defense += day_defense
            day_count += 1
        else:
            daily_data.append({
                'date': current_day.date(),
                'offense': None,
                'defense': None,
                'trophies': None
            })

        current_day = next_day

    if day_count > 0:
        average_offense = sum_offense / day_count
        average_defense = sum_defense / day_count
    else:
        average_offense = 0
        average_defense = 0

    net_gain = average_offense - average_defense

    player_info = {
        'name': player_name,
        'tag': player_actual_tag,
        'clanName': clan_name,
        'clanTag': clan_tag,
        'clanBadgeUrl': clan_badge_url,
        'leagueIconUrl': league_icon_url,
        'seasonStr': season_str
    }

    return (
        player_info,
        daily_data,
        final_trophies,
        average_offense,
        average_defense,
        net_gain
    )

def get_season_start_end(season_id):
    """Return the start/end datetimes in UTC for a given season_id like '2025-03'."""
    year_str, month_str = season_id.split('-')
    year = int(year_str)
    month = int(month_str)
    start_month = month - 1
    start_year = year
    if start_month < 1:
        start_month = 12
        start_year -= 1
    start_dt = get_last_monday_of_month(start_year, start_month).replace(
        hour=5, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
    end_dt = get_last_monday_of_month(year, month).replace(
        hour=5, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
    return start_dt, end_dt

def get_last_monday_of_month(year, month):
    """Return a datetime for the last Monday of the given year/month."""
    next_month = month + 1
    next_month_year = year
    if next_month > 12:
        next_month = 1
        next_month_year += 1
    first_of_next = datetime.datetime(next_month_year, next_month, 1)
    dt = first_of_next - datetime.timedelta(days=1)
    while dt.weekday() != 0:
        dt -= datetime.timedelta(days=1)
    return dt

def make_season_string(season_id, start_dt, end_dt):
    """Build a string like 'March 2025 Season (24 Feb - 31 Mar)'."""
    year_str, month_str = season_id.split('-')
    year = int(year_str)
    month = int(month_str)
    month_name = calendar.month_name[month]
    season_title = f"{month_name} {year} Season"
    start_str = f"{start_dt.day} {start_dt.strftime('%b')}"
    end_str = f"{end_dt.day} {end_dt.strftime('%b')}"
    return f"{season_title} ({start_str} - {end_str})"
