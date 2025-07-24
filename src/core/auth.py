# src/auth.py
from fastapi import HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from typing import Dict, Optional

# Separate security schemes for each API key
coc_security = APIKeyHeader(
    name="X-CoC-API-Key",
    scheme_name="Clash of Clans API Key",
    description="Your Clash of Clans API key from developer.clashofclans.com",
    auto_error=False
)

clashperk_security = APIKeyHeader(
    name="X-ClashPerk-API-Key", 
    scheme_name="ClashPerk API Key",
    description="Your ClashPerk API key (optional - for enhanced legend league data)",
    auto_error=False
)

def get_api_keys(
    coc_key: Optional[str] = Security(coc_security),
    clashperk_key: Optional[str] = Security(clashperk_security)
) -> Dict[str, str]:
    """
    Extract API keys from separate headers.
    CoC API key is required, ClashPerk key is optional.
    """
    
    # CoC API key is required
    if not coc_key:
        raise HTTPException(
            status_code=401,
            detail="Clash of Clans API key is required. Get one from developer.clashofclans.com"
        )
    
    return {
        "coc_api_key": coc_key,
        "clashperk_api_key": clashperk_key or ""
    }