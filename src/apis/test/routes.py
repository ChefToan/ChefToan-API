# src/apis/test/routes.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from io import BytesIO

# Create router for test API
test_router = APIRouter(prefix="/test", tags=["Test"])

# Get the base directory (project root)
BASE_DIR = Path(__file__).parent.parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"

@test_router.get("/", summary="API Test Endpoint", description="Returns a test image")
async def get_test_image():
    """
    Returns a test image for API testing purposes.
    """
    rickroll_path = ASSETS_DIR / "images" / "rickroll.png"
    
    # Check if the file exists
    if not rickroll_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Test image not found"
        )
    
    # Read the image file into BytesIO buffer (same as chart endpoint)
    with open(rickroll_path, "rb") as image_file:
        image_content = image_file.read()
    
    # Create BytesIO buffer like the chart endpoint
    image_buf = BytesIO(image_content)
    
    # Return StreamingResponse exactly like chart endpoint (no custom headers)
    return StreamingResponse(image_buf, media_type='image/png')