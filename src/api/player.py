# src/api/player.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import json
import time
import config
from src.services.clash_service import ClashApiClient
from src.services.player_essentials_service import PlayerEssentialsService
from src.services.redis_service import cache_get, cache_set

player_router = APIRouter(tags=["Player Data"])


@player_router.get("/player", summary="Get full player information", description="Get complete player data directly from Clash of Clans API")
async def get_player_info(
    tag: str = Query(..., description="Player tag (with or without # prefix)")
):
    """Get full player information directly from Clash of Clans API"""
    start_time = time.time()

    try:
        # Standardize the player tag
        if not tag.startswith('#'):
            tag = '#' + tag
        player_tag = tag.upper()

        # Check cache first
        cache_key = f"player_full:{player_tag}"
        cached_data = cache_get(cache_key)

        if cached_data is not None:
            response_time = time.time() - start_time
            print(f"CACHED player data served in {response_time:.3f}s for {player_tag}")

            # Add performance headers
            headers = {
                'X-Cache': 'HIT',
                'X-Response-Time': f"{response_time:.3f}s"
            }
            return JSONResponse(content=cached_data, headers=headers)

        # Cache miss - fetch from API
        print(f"Cache MISS for full player data: {player_tag}")

        # Initialize the Clash API client with static API key from config
        clash_client = ClashApiClient(api_token=config.COC_API_TOKEN)

        # Get player data
        api_start = time.time()
        player_data = clash_client.get_player(player_tag)
        api_time = time.time() - api_start

        # Cache the result for 5 minutes
        cache_set(cache_key, player_data, timeout=300)

        response_time = time.time() - start_time
        print(f"FRESH player data served in {response_time:.3f}s (API: {api_time:.3f}s) for {player_tag}")

        # Add performance headers
        headers = {
            'X-Cache': 'MISS',
            'X-Response-Time': f"{response_time:.3f}s",
            'X-API-Time': f"{api_time:.3f}s"
        }
        return JSONResponse(content=player_data, headers=headers)

    except Exception as e:
        response_time = time.time() - start_time
        print(f"Error fetching player data in {response_time:.3f}s: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@player_router.get("/player/essentials", summary="Get essential player data", description="Get optimized player data for mobile apps - smaller payload, faster loading")
async def get_player_essentials(
    tag: str = Query(..., description="Player tag (with or without # prefix)")
):
    """Get essential player information optimized for mobile app"""
    start_time = time.time()

    try:
        # Standardize the player tag
        if not tag.startswith('#'):
            tag = '#' + tag
        player_tag = tag.upper()

        # Check cache for processed essentials data
        essentials_cache_key = f"player_essentials:{player_tag}"
        cached_essentials = cache_get(essentials_cache_key)

        if cached_essentials is not None:
            response_time = time.time() - start_time
            print(f"CACHED essentials data served in {response_time:.3f}s for {player_tag}")

            # Use custom JSON serialization to preserve OrderedDict order
            json_str = json.dumps(cached_essentials, indent=2)
            headers = {
                'X-Cache': 'HIT',
                'X-Response-Time': f"{response_time:.3f}s"
            }
            return JSONResponse(content=cached_essentials, headers=headers, media_type='application/json')

        # Cache miss - need to fetch and process data
        print(f"Cache MISS for essentials data: {player_tag}")

        # Initialize services with static API key from config
        clash_client = ClashApiClient(api_token=config.COC_API_TOKEN)
        essentials_service = PlayerEssentialsService()

        # Get player data (this call itself should be cached)
        api_start = time.time()
        player_data = clash_client.get_player(player_tag)
        api_time = time.time() - api_start

        # Extract and format essential data
        processing_start = time.time()
        essential_data = essentials_service.format_player_essentials(player_data)
        processing_time = time.time() - processing_start

        # Cache the processed essentials data for 5 minutes
        cache_set(essentials_cache_key, essential_data, timeout=300)

        response_time = time.time() - start_time
        print(
            f"FRESH essentials data served in {response_time:.3f}s "
            f"(API: {api_time:.3f}s, Processing: {processing_time:.3f}s) for {player_tag}"
        )

        # Use custom JSON serialization to preserve OrderedDict order
        headers = {
            'X-Cache': 'MISS',
            'X-Response-Time': f"{response_time:.3f}s",
            'X-API-Time': f"{api_time:.3f}s",
            'X-Processing-Time': f"{processing_time:.3f}s"
        }
        return JSONResponse(content=essential_data, headers=headers, media_type='application/json')

    except Exception as e:
        response_time = time.time() - start_time
        print(f"Error fetching player essentials in {response_time:.3f}s: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))