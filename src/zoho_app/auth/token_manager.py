# zoho_app/auth/token_manager.py

import os
import time
import requests
from functools import lru_cache

TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"

@lru_cache(maxsize=1)
def get_access_token() -> str:
    """Refresh access token using long-lived refresh token."""
    response = requests.post(
        TOKEN_URL,
        params={
            "refresh_token": os.environ["REFRESH_TOKEN"],
            "client_id": os.environ["CLIENT_ID"],
            "client_secret": os.environ["CLIENT_SECRET"],
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if "access_token" not in data:
        raise RuntimeError(f"Zoho auth failed: {data}")
    return data["access_token"]