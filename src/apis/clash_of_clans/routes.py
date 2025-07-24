# src/apis/clash_of_clans/routes.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
import json
import time
import config
from src.apis.clash_of_clans.services.clash_service import ClashApiClient, ServiceUnavailableError, PlayerNotFoundError, AuthenticationError
from src.apis.clash_of_clans.services.player_essentials_service import PlayerEssentialsService
from src.apis.clash_of_clans.services.data_fetcher import get_player_data_with_keys
from src.apis.clash_of_clans.chart_generator import generate_chart
from src.core.redis_service import cache_get, cache_set
from io import BytesIO

# Create router with prefix for clash of clans API
clash_router = APIRouter(prefix="/clash-of-clans", tags=["Clash of Clans"])


@clash_router.get("/player", summary="Get full player information", description="Get complete player data directly from Clash of Clans API")
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


@clash_router.get("/player/essentials", summary="Get essential player data", description="Get optimized player data for mobile apps - smaller payload, faster loading")
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


@clash_router.get("/chart", summary="Generate player chart", description="Generate and return a trophy progression chart (for Legend League players only)")
async def get_player_chart(
    tag: str = Query(..., description="Player tag (with or without # prefix)")
):
    """Generate and return a chart for the player's trophy progress with aggressive caching"""

    # Standardize the player tag
    if not tag.startswith('#'):
        tag = '#' + tag
    player_tag = tag.upper()

    # PERFORMANCE OPTIMIZATION: Check for cached chart image first
    chart_cache_key = f"chart_image:{player_tag}"

    # Try to get cached chart (cache for 10 minutes for charts)
    cached_chart = cache_get(chart_cache_key)
    if cached_chart is not None:
        print(f"Serving cached chart for {player_tag}")
        try:
            import base64

            # Decode the base64 cached image
            chart_buf = BytesIO(base64.b64decode(cached_chart))
            return StreamingResponse(chart_buf, media_type='image/png')
        except Exception as e:
            print(f"Failed to serve cached chart: {str(e)}")
            # Continue to generate new chart if cached version fails

    try:
        start_time = time.time()

        # Get player data with static API keys from config
        player_info, daily_data, final_trophies, avg_offense, avg_defense, net_gain = get_player_data_with_keys(
            player_tag, 
            config.COC_API_TOKEN, 
            config.CLASHPERK_API_TOKEN
        )

        data_fetch_time = time.time() - start_time
        print(f"Data fetch took {data_fetch_time:.3f}s for {player_tag}")

        # Generate chart
        chart_start = time.time()
        chart_buf = generate_chart(
            player_info=player_info,
            daily_data=daily_data,
            final_trophies=final_trophies,
            average_offense=avg_offense,
            average_defense=avg_defense,
            net_gain=net_gain
        )

        chart_gen_time = time.time() - chart_start
        print(f"Chart generation took {chart_gen_time:.3f}s for {player_tag}")

        # PERFORMANCE OPTIMIZATION: Cache the generated chart image
        try:
            import base64
            chart_buf.seek(0)
            chart_data = chart_buf.read()
            chart_buf.seek(0)  # Reset buffer position

            # Cache as base64 string for 10 minutes (600 seconds)
            chart_b64 = base64.b64encode(chart_data).decode('utf-8')
            cache_set(chart_cache_key, chart_b64, timeout=600)
            print(f"Cached chart for {player_tag}")
        except Exception as e:
            print(f"Failed to cache chart: {str(e)}")

        total_time = time.time() - start_time
        print(f"Total chart request took {total_time:.3f}s for {player_tag}")

        return StreamingResponse(chart_buf, media_type='image/png')

    except ServiceUnavailableError as e:
        print(f"External API unavailable: {str(e)}")
        return generate_error_image(
            "Service Temporarily Unavailable",
            "The Clash of Clans API is currently down. Please try again later.",
            503
        )

    except PlayerNotFoundError as e:
        print(f"Player not found: {str(e)}")
        return generate_error_image(
            "Player Not Found",
            f"Could not find player with tag {player_tag}. Please check the tag and try again.",
            404
        )

    except AuthenticationError as e:
        print(f"API authentication error: {str(e)}")
        return generate_error_image(
            "API Authentication Error",
            "Failed to authenticate with the Clash of Clans API. Please check API token configuration.",
            500
        )

    except Exception as e:
        print(f"Error generating chart: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return generate_error_image(
            "Error Generating Chart",
            "An unexpected error occurred. Please try again later.",
            500
        )


def generate_error_image(title, message, status_code):
    """Generate a simple error image with a message"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # Use a smaller figure for error images
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.6, title, fontsize=20, ha='center', va='center', fontweight='bold')
    ax.text(0.5, 0.4, message, fontsize=14, ha='center', va='center')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=80, facecolor='#f7f7f7', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return StreamingResponse(buf, media_type='image/png', status_code=status_code)