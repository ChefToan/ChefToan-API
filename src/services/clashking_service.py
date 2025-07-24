# src/services/clashking_service.py
import requests
import json
import config
import logging
from src.services.redis_service import cached
from src.services.retry_utils import retry_request


class ClashKingClient:
    """Client for ClashKing API with combined ranking endpoints"""

    def __init__(self):
        self.base_url = 'https://api.clashk.ing'

    def _format_tag(self, player_tag):
        """Format the player tag for API URLs"""
        if not player_tag.startswith('#'):
            player_tag = f'#{player_tag}'
        return player_tag.replace('#', '%23')

    @cached(timeout=600, use_stale_on_error=True)  # Cache for 10 minutes
    @retry_request(max_retries=3)
    def get_global_ranking(self, player_tag):
        """
        Get global ranking from ClashKing legends ranking endpoint
        Returns: {"global_rank": int} or {}
        """
        formatted_tag = self._format_tag(player_tag)
        url = f'{self.base_url}/ranking/legends/{formatted_tag}'

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Extract the rank from the response
            global_rank = data.get('rank')
            if global_rank is not None:
                logging.info(f"Retrieved global rank {global_rank} for {player_tag}")
                return {
                    'global_rank': global_rank,
                    'name': data.get('name'),
                    'trophies': data.get('trophies'),
                    'townhall': data.get('townhall')
                }
            else:
                logging.warning(f"No global rank found for {player_tag}")
                return {}

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning(f"Player {player_tag} not found in ClashKing legends ranking")
                return {}
            elif e.response.status_code == 503:
                logging.error(f"ClashKing ranking API unavailable: {str(e)}")
                return {}
            else:
                logging.error(f"ClashKing ranking API error: {str(e)}")
                return {}
        except requests.exceptions.Timeout as e:
            logging.error(f"ClashKing ranking API timeout: {str(e)}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error from ClashKing ranking API: {str(e)}")
            return {}

    @cached(timeout=900, use_stale_on_error=True)  # Cache for 15 minutes
    @retry_request(max_retries=2)
    def get_local_ranking_and_seasons(self, player_tag):
        """
        Get local ranking and season data from ClashKing stats endpoint
        Memory-efficient approach that extracts only what we need
        Returns: {"local_rank": int, "previous_season": {}, "best_season": {}} or {}
        """
        formatted_tag = self._format_tag(player_tag)
        url = f'{self.base_url}/player/{formatted_tag}/stats'

        try:
            # Try streaming approach first if ijson is available
            try:
                import ijson
                return self._parse_stats_streaming(url)
            except ImportError:
                # Fallback to regular parsing
                logging.info("ijson not available, using regular JSON parsing")
                return self._parse_stats_regular(url)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning(f"Player {player_tag} not found in ClashKing stats")
                return {}
            else:
                logging.error(f"ClashKing stats API error: {str(e)}")
                return {}
        except Exception as e:
            logging.error(f"Error getting stats data: {str(e)}")
            return {}

    def _parse_stats_streaming(self, url):
        """Parse stats using streaming JSON for memory efficiency"""
        import ijson

        with requests.get(url, stream=True, timeout=45) as response:
            response.raise_for_status()

            legends_data = {}

            # Parse the streaming JSON looking for legends data
            parser = ijson.parse(response.raw)

            for prefix, event, value in parser:
                if prefix == 'legends.local_rank':
                    legends_data['local_rank'] = value
                elif prefix.startswith('legends.previousSeason'):
                    if 'previous_season' not in legends_data:
                        legends_data['previous_season'] = {}
                    key = prefix.split('.')[-1]
                    legends_data['previous_season'][key] = value
                elif prefix.startswith('legends.bestSeason'):
                    if 'best_season' not in legends_data:
                        legends_data['best_season'] = {}
                    key = prefix.split('.')[-1]
                    legends_data['best_season'][key] = value

                # Break early if we have the essential data
                if 'local_rank' in legends_data:
                    # Continue a bit more to get season data, but don't parse the whole file
                    continue

            return legends_data

    def _parse_stats_regular(self, url):
        """Fallback regular JSON parsing"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        legends_section = data.get('legends', {})

        if legends_section:
            return {
                'local_rank': legends_section.get('local_rank'),
                'previous_season': legends_section.get('previousSeason'),
                'best_season': legends_section.get('bestSeason')
            }
        return {}

    @cached(timeout=600, use_stale_on_error=True)  # Cache for 10 minutes
    def get_combined_legends_data(self, player_tag):
        """
        Get combined legends data from both endpoints
        Returns complete legends data with global_rank, local_rank, and seasons
        """
        combined_data = {}

        # Get global ranking (fast, small response)
        global_data = self.get_global_ranking(player_tag)
        if global_data and 'global_rank' in global_data:
            combined_data['global_rank'] = global_data['global_rank']

        # Get local ranking and season data (larger response, cached longer)
        local_data = self.get_local_ranking_and_seasons(player_tag)
        if local_data:
            if 'local_rank' in local_data:
                combined_data['local_rank'] = local_data['local_rank']
            if 'previous_season' in local_data:
                combined_data['previous_season'] = local_data['previous_season']
            if 'best_season' in local_data:
                combined_data['best_season'] = local_data['best_season']

        return combined_data


class ServiceUnavailableError(Exception):
    """Raised when an external service is unavailable"""
    pass