import datetime
from datetime import timezone, timedelta
from src.services.redis_service import cached
from src.services.clash_service import ClashApiClient
from src.services.clashperk_service import ClashPerkClient
from flask import current_app


@cached(timeout=1800, use_stale_on_error=True)  # Cache for 30 minutes, use stale data on error
def get_player_data(player_tag):
    """Fetch and compute daily data from CoC & ClashPerk APIs."""
    clash_client = ClashApiClient()
    perk_client = ClashPerkClient()

    try:
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
        try:
            perk_json = perk_client.get_legend_attacks(player_tag)
        except Exception as e:
            # If ClashPerk API fails, we can still generate a partial chart
            # using just the basic player data from CoC API
            current_app.logger.warning(f"ClashPerk API error, using fallback data: {str(e)}")
            perk_json = {
                'logs': [],
                'trophies': player_json.get('trophies', 0),
                'initial': player_json.get('trophies', 0),
                'seasonId': ''
            }

        logs = perk_json.get('logs', [])
        final_trophies = perk_json.get('trophies', 0)
        initial_trophies = perk_json.get('initial', 0)
        season_id = perk_json.get('seasonId', '')

        # Determine season dates
        if season_id:
            try:
                start_date, end_date = perk_client.get_season_start_end(season_id)
                season_str = perk_client.make_season_string(season_id, start_date, end_date)
            except Exception:
                # Fallback if season calculation fails
                current_month = datetime.datetime.now().month
                current_year = datetime.datetime.now().year
                start_date = datetime.datetime(current_year, current_month, 1, 5, 0, 0, tzinfo=timezone.utc)
                end_date = (start_date + timedelta(days=35)).replace(day=1)
                season_str = f"Current Season"
        else:
            start_date = datetime.datetime(2025, 2, 24, 5, 0, 0, tzinfo=timezone.utc)
            end_date = datetime.datetime(2025, 3, 31, 5, 0, 0, tzinfo=timezone.utc)
            season_str = "Unknown Season"

        # Process the daily data
        # Sort logs by timestamp to ensure correct trophy progression
        sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', 0))

        # Initialize daily data structures
        daily_data = []
        day_data_dict = {}

        # Set starting trophies to initial value
        current_trophies = initial_trophies

        # Track total offense and defense for averages
        sum_offense = 0
        sum_defense = 0
        day_count = 0

        # Process each day in the season
        current_day = start_date
        while current_day <= end_date:
            current_date = current_day.date()  # Convert to date object
            next_day = current_day + timedelta(days=1)

            day_offense = 0
            day_defense = 0
            day_has_logs = False
            day_trophy_end = None

            # Process logs for this day
            for log_item in sorted_logs:
                ts = log_item.get('timestamp', 0)
                action_type = log_item.get('type', '')
                inc = log_item.get('inc', 0)
                # Important: Use 'end' value from log for the most accurate trophy count
                log_end = log_item.get('end', current_trophies)

                log_time = datetime.datetime.utcfromtimestamp(ts / 1000).replace(tzinfo=timezone.utc)

                if current_day <= log_time < next_day:
                    day_has_logs = True
                    if action_type == 'attack':
                        day_offense += inc
                    elif action_type == 'defense':
                        day_defense += abs(inc)  # Use absolute value for defense

                    # Update trophy count to the latest value in the logs for this day
                    day_trophy_end = log_end

            # Store data for this day
            date_str = current_date.isoformat()

            if day_has_logs:
                # Use the end trophy value from the last log entry of the day
                current_trophies = day_trophy_end

                day_data_dict[date_str] = {
                    'date': current_date,  # Store actual date object
                    'offense': day_offense,
                    'defense': day_defense,
                    'trophies': current_trophies
                }

                sum_offense += day_offense
                sum_defense += day_defense
                day_count += 1
            else:
                # Only add empty days if we don't already have data for this day
                # and if the day is not in the future
                if date_str not in day_data_dict and current_day <= datetime.datetime.now(timezone.utc):
                    day_data_dict[date_str] = {
                        'date': current_date,
                        'offense': None,
                        'defense': None,
                        'trophies': None
                    }

            current_day = next_day

        # Ensure the final trophy value is accurate
        # If we have logs, the last value should match the final trophy count from the API
        if sorted_logs and final_trophies != current_trophies:
            current_app.logger.warning(
                f"Trophy mismatch: calculated={current_trophies}, reported={final_trophies}. Using reported value."
            )
            # Adjust the last day with trophy data to match the final value
            for date_str in reversed(sorted(day_data_dict.keys())):
                if day_data_dict[date_str]['trophies'] is not None:
                    day_data_dict[date_str]['trophies'] = final_trophies
                    break

        # Convert the dictionary to a list, sorted by date
        daily_data = [day_data_dict[date] for date in sorted(day_data_dict.keys())]

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

    except Exception as e:
        # Add more context to the error
        current_app.logger.error(f"Error fetching data for player {player_tag}: {str(e)}")
        raise