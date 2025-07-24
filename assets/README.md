# Assets Directory

This directory contains static assets used by ChefToan's API.

## Structure

```
assets/
├── images/          # Static images
│   └── rickroll.png # Rickroll image for test endpoint
└── README.md        # This file
```

## Usage

- **Images**: Place static images that need to be served by the API
- **Other Assets**: You can add subdirectories for other types of assets (css, js, etc.)

## Adding New Images

1. Place your image files in the appropriate subdirectory
2. Reference them in your API routes using relative paths from the assets directory
3. Make sure to handle file serving properly in your FastAPI routes

## Current Assets

- `images/rickroll.png`: Fun rickroll image served by the test endpoint at `/test`