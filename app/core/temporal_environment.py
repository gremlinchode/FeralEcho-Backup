# FILE: app/core/temporal_environment.py
import os
import requests
from datetime import datetime
import time
import json

try:
    import pytz
except ImportError:
    pytz = None

# -----------------------------
# 1. Season Detection
# -----------------------------
def get_season(now=None):
    if now is None:
        now = datetime.now()
    month = now.month
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"

# -----------------------------
# 2. Auto Location Detection
# -----------------------------

SYMBIOTE_LOCATION_FILE = os.path.join(
    os.path.dirname(__file__), "../../data/symbiote_location.json"
)

def get_location_from_symbiote():
    """
    Read GPS location pushed by feral_echo_symbiote.py (iPhone).
    Expected format: {"lat": 49.2057, "lon": -122.9110, "timezone": "America/Vancouver"}
    Returns None if unavailable.
    """
    try:
        path = os.path.abspath(SYMBIOTE_LOCATION_FILE)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            lat = data.get("lat")
            lon = data.get("lon")
            timezone = data.get("timezone", "America/Vancouver")
            if lat and lon:
                return {"lat": lat, "lon": lon, "timezone": timezone, "source": "symbiote"}
    except Exception:
        pass
    return None

def get_location_from_ip():
    """
    Geolocate via outbound IP using ipapi.co.
    Returns lat, lon, timezone or None on failure.
    """
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        response.raise_for_status()
        data = response.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        timezone = data.get("timezone", "America/Vancouver")
        city = data.get("city", "Unknown")
        if lat and lon:
            return {
                "lat": lat,
                "lon": lon,
                "timezone": timezone,
                "city": city,
                "source": "ip"
            }
    except Exception:
        pass
    return None

def get_location(default_lat=49.2057, default_lon=-122.9110,
                 default_timezone="America/Vancouver"):
    """
    Location resolution order:
    1. iPhone symbiote GPS (most accurate)
    2. IP geolocation (good enough for weather/timezone)
    3. Hardcoded default (Delta/New Westminster area)
    """
    location = get_location_from_symbiote()
    if location:
        return location

    location = get_location_from_ip()
    if location:
        return location

    return {
        "lat": default_lat,
        "lon": default_lon,
        "timezone": default_timezone,
        "city": "Delta/New Westminster",
        "source": "default"
    }

# -----------------------------
# 3. Safe Local Time Fetch
# -----------------------------
def get_local_time(timezone="America/Vancouver"):
    """Fetch current time from worldtimeapi.org, fallback to UTC."""
    try:
        url = f"https://worldtimeapi.org/api/timezone/{timezone}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        utc_time = datetime.fromisoformat(data.get("datetime"))
    except Exception:
        utc_time = datetime.utcnow()

    if pytz:
        try:
            tz = pytz.timezone(timezone)
            local_time = utc_time.astimezone(tz)
        except Exception:
            local_time = utc_time
    else:
        local_time = utc_time

    return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")

# -----------------------------
# 4. Safe Weather Fetch
# -----------------------------
def get_weather(api_key, lat, lon):
    """Fetch weather from OpenWeatherMap, return Fahrenheit."""
    weather_data = None
    for attempt in range(3):
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            )
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            weather_data = response.json()
            break
        except requests.exceptions.RequestException:
            if attempt < 2:
                time.sleep(2)
            else:
                weather_data = {
                    "main": {"temp": 0},
                    "weather": [{"description": "unknown"}]
                }

    temp_c = weather_data["main"]["temp"]
    temp_f = temp_c * 9 / 5 + 32 if isinstance(temp_c, (int, float)) else "N/A"
    description = weather_data["weather"][0]["description"]
    return {"temperature": temp_f, "conditions": description}

# -----------------------------
# 5. Compose Temporal Context
# -----------------------------
def get_temporal_environment_context(
    timezone=None,
    lat=None,
    lon=None,
    weather_api_key=None
):
    """
    Return formatted string with location, time, season, and weather.
    Location resolves automatically: symbiote GPS > IP > default.
    """
    location = get_location(
        default_lat=lat or 49.2057,
        default_lon=lon or -122.9110,
        default_timezone=timezone or "America/Vancouver"
    )

    resolved_timezone = location["timezone"]
    resolved_lat = location["lat"]
    resolved_lon = location["lon"]
    location_source = location.get("source", "default")
    city = location.get("city", "")

    current_time = get_local_time(resolved_timezone)
    season = get_season()

    api_key = weather_api_key or os.environ.get("OPENWEATHER_API_KEY")
    if api_key:
        weather_info = get_weather(api_key, resolved_lat, resolved_lon)
    else:
        weather_info = {"temperature": "N/A", "conditions": "N/A"}

    location_label = f"{city} " if city else ""
    context = (
        f"Current date and time: {current_time}\n"
        f"Location: {location_label}({resolved_lat:.3f}, {resolved_lon:.3f})"
        f" [{location_source}]\n"
        f"Season: {season}\n"
        f"Weather: {weather_info['conditions']}, {weather_info['temperature']}°F"
    )
    return context

# -----------------------------
# 6. Example Usage
# -----------------------------
if __name__ == "__main__":
    API_KEY = os.environ.get("OPENWEATHER_API_KEY")
    context = get_temporal_environment_context(weather_api_key=API_KEY)
    print("Echo Temporal Environment Context:\n", context)
