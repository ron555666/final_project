import requests
import time


CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
geocode_cache = {}


def geocode_location(query: str):
    cache_key = query.lower().strip()
    now = time.time()

    # 1. Check cache first
    if cache_key in geocode_cache:
        cached_result, expires_at = geocode_cache[cache_key]

        if now < expires_at:
            return cached_result

        # expired cache
        del geocode_cache[cache_key]

    # 2. Call external geocoding API
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "us"
    }

    headers = {
        "User-Agent": "store-locator-api-final-project"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=3
        )

        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        result = {
            "latitude": float(data[0]["lat"]),
            "longitude": float(data[0]["lon"])
        }

        # 3. Save result to cache
        geocode_cache[cache_key] = (
            result,
            now + CACHE_TTL_SECONDS
        )

        return result

    except Exception:
        return None