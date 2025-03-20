import requests
from flask import current_app
from services.redis_service import cached


class ClashApiClient:
    """Client for Clash of Clans API"""

    def __init__(self):
        self.base_url = current_app.config['COC_API_BASE_URL']
        self.api_token = current_app.config['COC_API_TOKEN']
        self.headers = {'Authorization': f'Bearer {self.api_token}'}

    def _format_tag(self, player_tag):
        """Format the player tag for API URLs"""
        if not player_tag.startswith('#'):
            player_tag = f'#{player_tag}'
        return player_tag.replace('#', '%23')

    @cached(timeout=300)  # Cache for 5 minutes
    def get_player(self, player_tag):
        """Get player information from Clash of Clans API"""
        formatted_tag = self._format_tag(player_tag)
        url = f'{self.base_url}/players/{formatted_tag}'

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()

    @cached(timeout=3600)  # Cache for 1 hour
    def get_clan(self, clan_tag):
        """Get clan information from Clash of Clans API"""
        formatted_tag = self._format_tag(clan_tag)
        url = f'{self.base_url}/clans/{formatted_tag}'

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()

    @cached(timeout=300)  # Cache for 5 minutes
    def get_clan_members(self, clan_tag):
        """Get clan members from Clash of Clans API"""
        formatted_tag = self._format_tag(clan_tag)
        url = f'{self.base_url}/clans/{formatted_tag}/members'

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()