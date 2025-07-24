# src/api/chart.py - OPTIMIZED VERSION
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from src.services.data_fetcher import get_player_data_with_keys
from src.utils.chart_generator import generate_chart
from src.services.clash_service import ServiceUnavailableError, PlayerNotFoundError, AuthenticationError
from src.services.redis_service import cache_get, cache_set
import config
import time
from io import BytesIO

chart_router = APIRouter(tags=["Charts"])


@chart_router.get("/chart", summary="Generate player chart", description="Generate and return a trophy progression chart (for Legend League players only)")
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