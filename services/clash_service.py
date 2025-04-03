# services/clash_service.py
import requests
from flask import current_app
from services.redis_service import cached
from services.retry_utils import retry_request


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

    @cached(timeout=300, use_stale_on_error=True)  # Cache for 5 minutes, use stale data on error
    @retry_request(max_retries=3)
    def get_player(self, player_tag):
        """Get player information from Clash of Clans API"""
        formatted_tag = self._format_tag(player_tag)
        url = f'{self.base_url}/players/{formatted_tag}'

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                current_app.logger.error(f"Clash of Clans API is currently unavailable: {str(e)}")
                raise ServiceUnavailableError("Clash of Clans API is currently unavailable. Please try again later.")
            elif e.response.status_code == 403:
                current_app.logger.error(f"API authentication error: {str(e)}")
                raise AuthenticationError("API authentication failed. Please check your API token.")
            elif e.response.status_code == 404:
                current_app.logger.error(f"Player not found: {player_tag}")
                raise PlayerNotFoundError(f"Player {player_tag} not found.")
            else:
                raise

    @cached(timeout=3600, use_stale_on_error=True)  # Cache for 1 hour, use stale data on error
    @retry_request(max_retries=3)
    def get_clan(self, clan_tag):
        """Get clan information from Clash of Clans API"""
        formatted_tag = self._format_tag(clan_tag)
        url = f'{self.base_url}/clans/{formatted_tag}'

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                current_app.logger.error(f"Clash of Clans API is currently unavailable: {str(e)}")
                raise ServiceUnavailableError("Clash of Clans API is currently unavailable. Please try again later.")
            else:
                raise

    @cached(timeout=300, use_stale_on_error=True)  # Cache for 5 minutes, use stale data on error
    @retry_request(max_retries=3)
    def get_clan_members(self, clan_tag):
        """Get clan members from Clash of Clans API"""
        formatted_tag = self._format_tag(clan_tag)
        url = f'{self.base_url}/clans/{formatted_tag}/members'

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                current_app.logger.error(f"Clash of Clans API is currently unavailable: {str(e)}")
                raise ServiceUnavailableError("Clash of Clans API is currently unavailable. Please try again later.")
            else:
                raise


# Custom exceptions
class ServiceUnavailableError(Exception):
    """Raised when an external service is unavailable"""
    pass


class AuthenticationError(Exception):
    """Raised when API authentication fails"""
    pass


class PlayerNotFoundError(Exception):
    """Raised when a requested player is not found"""
    pass