import requests
import datetime
from datetime import timezone, timedelta
import calendar
from flask import current_app
from src.services.redis_service import cached


class ClashPerkClient:
    """Client for ClashPerk API"""

    def __init__(self):
        self.base_url = current_app.config['CLASHPERK_BASE_URL']
        self.api_token = current_app.config['CLASHPERK_API_TOKEN']
        self.headers = {'Authorization': f'Bearer {self.api_token}'}

    def _format_tag(self, player_tag):
        """Format the player tag for API URLs"""
        if not player_tag.startswith('#'):
            player_tag = f'#{player_tag}'
        return player_tag.replace('#', '%23')

    @cached(timeout=900)  # Cache for 15 minutes
    def get_legend_attacks(self, player_tag):
        """Get legend league attacks from ClashPerk API"""
        formatted_tag = self._format_tag(player_tag)
        url = f'{self.base_url}/players/legend-attacks/{formatted_tag}'

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_last_monday_of_month(self, year, month):
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

    def get_season_start_end(self, season_id):
        """Return the start/end datetimes in UTC for a given season_id like '2025-03'."""
        year_str, month_str = season_id.split('-')
        year = int(year_str)
        month = int(month_str)
        start_month = month - 1
        start_year = year
        if start_month < 1:
            start_month = 12
            start_year -= 1
        start_dt = self.get_last_monday_of_month(start_year, start_month).replace(
            hour=5, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        end_dt = self.get_last_monday_of_month(year, month).replace(
            hour=5, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        return start_dt, end_dt

    def make_season_string(self, season_id, start_dt, end_dt):
        """Build a string like 'March 2025 Season (24 Feb - 31 Mar)'."""
        year_str, month_str = season_id.split('-')
        year = int(year_str)
        month = int(month_str)
        month_name = calendar.month_name[month]
        season_title = f"{month_name} {year} Season"
        start_str = f"{start_dt.day} {start_dt.strftime('%b')}"
        end_str = f"{end_dt.day} {end_dt.strftime('%b')}"
        return f"{season_title} ({start_str} - {end_str})"