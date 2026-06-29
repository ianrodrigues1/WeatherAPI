import os
import time
import unicodedata
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
OPENWEATHER_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "600"))
REQUEST_TIMEOUT = int(os.getenv("WEATHER_REQUEST_TIMEOUT", "8"))

_cache = {}


class CityNotFoundError(Exception):
    pass


class WeatherConfigurationError(Exception):
    pass


class WeatherProviderError(Exception):
    pass


def get_current_weather(city):
    normalized_city = _normalize_city(city)
    cache_key = f"weather:city:{normalized_city}"
    cached_weather = _get_from_cache(cache_key)

    if cached_weather:
        return cached_weather

    location = _get_location(normalized_city)
    weather_payload = _get_weather_by_coordinates(location["lat"], location["lon"])
    weather = _format_weather_response(location, weather_payload)

    _save_to_cache(cache_key, weather)

    return weather


def get_current_weather_by_coordinates(lat, lon, city=None, country=None):
    parsed_lat = float(lat)
    parsed_lon = float(lon)
    cache_key = f"weather:coords:{parsed_lat:.4f}:{parsed_lon:.4f}"
    cached_weather = _get_from_cache(cache_key)

    if cached_weather:
        return cached_weather

    weather_payload = _get_weather_by_coordinates(parsed_lat, parsed_lon)
    location = {
        "name": city or weather_payload.get("name"),
        "country": country or weather_payload.get("sys", {}).get("country"),
    }
    weather = _format_weather_response(location, weather_payload)

    _save_to_cache(cache_key, weather)

    return weather


def search_city_suggestions(query, limit=5):
    normalized_query = _normalize_city(query)

    if len(normalized_query) < 2:
        return []

    cache_key = f"suggestions:{normalized_query}:{limit}"
    cached_suggestions = _get_from_cache(cache_key)

    if cached_suggestions is not None:
        return cached_suggestions

    provider_limit = min(max(limit * 3, limit), 20)
    locations = _get_locations(normalized_query, provider_limit)
    suggestions = _deduplicate_suggestions(
        [_format_location_suggestion(location) for location in locations]
    )[:limit]

    _save_to_cache(cache_key, suggestions)

    return suggestions


def _normalize_city(city):
    return " ".join(city.strip().split()).lower()


def _normalize_key(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.lower().split())


def _deduplicate_suggestions(suggestions):
    unique_suggestions = []
    seen = set()

    for suggestion in suggestions:
        key = _normalize_key(suggestion.get("label"))

        if not key or key in seen:
            continue

        seen.add(key)
        unique_suggestions.append(suggestion)

    return unique_suggestions


def _get_from_cache(key):
    cached_item = _cache.get(key)

    if not cached_item:
        return None

    expires_at, payload = cached_item

    if expires_at <= time.time():
        _cache.pop(key, None)
        return None

    return payload


def _save_to_cache(key, payload):
    _cache[key] = (time.time() + DEFAULT_CACHE_TTL, payload)


def _get_location(city):
    locations = _get_locations(city, 1)

    if not locations:
        raise CityNotFoundError()

    return locations[0]


def _get_locations(query, limit):
    _ensure_api_key()

    try:
        response = requests.get(
            OPENWEATHER_GEO_URL,
            params={"q": query, "limit": limit, "appid": OPENWEATHER_API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise WeatherProviderError() from exc

    if response.status_code != 200:
        raise WeatherProviderError()

    locations = response.json()

    return locations


def _get_weather_by_coordinates(lat, lon):
    _ensure_api_key()

    try:
        response = requests.get(
            OPENWEATHER_WEATHER_URL,
            params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "pt_br",
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise WeatherProviderError() from exc

    if response.status_code == 404:
        raise CityNotFoundError()

    if response.status_code != 200:
        raise WeatherProviderError()

    return response.json()


def _format_weather_response(location, weather_payload):
    main = weather_payload.get("main", {})
    wind = weather_payload.get("wind", {})
    weather = weather_payload.get("weather", [{}])[0]

    return {
        "city": location.get("name") or weather_payload.get("name"),
        "country": _country_name(location.get("country") or weather_payload.get("sys", {}).get("country")),
        "temperature": round(main.get("temp", 0)),
        "feels_like": round(main.get("feels_like", 0)),
        "humidity": main.get("humidity"),
        "wind_speed": round((wind.get("speed") or 0) * 3.6, 1),
        "condition": weather.get("description") or weather.get("main"),
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def _format_location_suggestion(location):
    country_code = location.get("country")
    country = _country_name(country_code)
    state = location.get("state")
    parts = [location.get("name")]

    if state:
        parts.append(state)

    if country:
        parts.append(country)

    return {
        "name": location.get("name"),
        "state": state,
        "country": country,
        "country_code": country_code,
        "lat": location.get("lat"),
        "lon": location.get("lon"),
        "label": ", ".join(part for part in parts if part),
    }


def _country_name(country_code):
    if not country_code:
        return "Unknown"

    try:
        import pycountry

        country = pycountry.countries.get(alpha_2=country_code.upper())
        return country.name if country else country_code.upper()
    except ImportError:
        return country_code.upper()


def _ensure_api_key():
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "your_openweathermap_api_key_here":
        raise WeatherConfigurationError(
            "Configure a variavel OPENWEATHER_API_KEY no arquivo .env antes de consultar a API."
        )
