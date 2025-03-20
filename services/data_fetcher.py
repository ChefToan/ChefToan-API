import datetime
from datetime import timezone, timedelta
from services.redis_service import cached
from services.clash_service import ClashApiClient
from services.clashperk_service import ClashPerkClient


@cached(timeout=1800)  # Cache for 30 minutes
def get_player_data(player_tag):
    """Fetch and compute daily data from CoC & ClashPerk APIs."""
    clash_client = ClashApiClient()
    perk_client = ClashPerkClient()

    # Get player data from CoC API
    player_json = clash_client.get_player(player_tag)

    player_name = player_json.get('name', 'Unknown')
    player_actual_tag = player_json.get('tag', player_tag)

    # Extract clan info if available
    clan_name = ''
    clan_badge_url = ''
    clan_tag = ''
    if 'clan' in player_json:
        clan_name = player_json['clan'].get('name', '')
        clan_badge_url = player_json['clan']['badgeUrls'].get('small', '')
        clan_tag = player_json['clan'].get('tag', '')

    # Extract league info if available
    league_icon_url = ''
    if 'league' in player_json and 'iconUrls' in player_json['league']:
        league_icon_url = player_json['league']['iconUrls'].get('small', '')

    # Get legend league attacks from ClashPerk API
    perk_json = perk_client.get_legend_attacks(player_tag)

    logs = perk_json.get('logs', [])
    final_trophies = perk_json.get('trophies', 0)
    initial_trophies = perk_json.get('initial', 0)
    season_id = perk_json.get('seasonId', '')

    # Determine season dates
    if season_id:
        start_date, end_date = perk_client.get_season_start_end(season_id)
        season_str = perk_client.make_season_string(season_id, start_date, end_date)
    else:
        start_date = datetime.datetime(2025, 2, 24, 5, 0, 0, tzinfo=timezone.utc)
        end_date = datetime.datetime(2025, 3, 31, 5, 0, 0, tzinfo=timezone.utc)
        season_str = "Unknown Season"

    # Process the daily data
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
                'date': current_day.date().isoformat(),  # Convert date to string format
                'offense': day_offense,
                'defense': day_defense,
                'trophies': current_trophies
            })
            sum_offense += day_offense
            sum_defense += day_defense
            day_count += 1
        else:
            daily_data.append({
                'date': current_day.date().isoformat(),  # Convert date to string format
                'offense': None,
                'defense': None,
                'trophies': None
            })

        current_day = next_day

    # Calculate averages
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