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
#
# PENDING_DECISIONS.md #23 (2026-09-09): this section used to resolve to
# ONE value via get_location(), unconditionally preferring the iPhone
# symbiote's pushed GPS over IP geolocation with no staleness check --
# collapsing two genuinely different things ("where is Gremlin's phone"
# and "where is Echo/the MacBook actually running") into one, which is
# wrong on its own terms even when both readings are fresh: the MacBook
# stays at the apartment on short trips while the phone can be hundreds
# of miles away. Gremlin's own direction, verbatim: "the fix isn't
# picking a winner between these two sources -- it's stopping them from
# being merged into one value at all." Split into two independent
# functions below; get_temporal_environment_context() (date/time/weather)
# now uses ONLY get_macbook_location() -- the phone's location is never
# consulted for Echo's own environmental context. get_phone_location() is
# real, staleness-annotated, and available, but deliberately not wired
# into the context string yet -- whether/how it should be surfaced to
# Echo at all is the still-open half of #23, not decided by this pass.

SYMBIOTE_LOCATION_FILE = os.path.join(
    os.path.dirname(__file__), "../../data/symbiote_location.json"
)

# The real symbiote_location.json has no timestamp field of its own (the
# phone script just overwrites lat/lon/timezone in place) -- file mtime is
# the only available staleness signal, confirmed by reading the real file
# directly before writing this. 6h is a judgment call, not a measured
# threshold: short enough to catch the "2-day-old reading on a moving
# train" case PENDING_DECISIONS #23 found live, generous enough not to
# flag a phone GPS reading from earlier the same day as stale.
_PHONE_LOCATION_STALE_AFTER_HOURS = 6.0

def get_location_from_symbiote():
    """
    Read GPS location pushed by feral_echo_symbiote.py (iPhone) --
    Gremlin's phone location, not Echo/the MacBook's. Returns None if
    unavailable. Includes staleness info (age_hours, stale) derived from
    the file's own mtime, since the file format itself carries no
    timestamp. Never used by get_temporal_environment_context() -- see
    this section's own header comment.
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
                age_hours = (time.time() - os.path.getmtime(path)) / 3600.0
                return {
                    "lat": lat, "lon": lon, "timezone": timezone,
                    "source": "symbiote",
                    "age_hours": round(age_hours, 2),
                    "stale": age_hours > _PHONE_LOCATION_STALE_AFTER_HOURS,
                }
    except Exception:
        pass
    return None

def get_phone_location():
    """Gremlin's phone location, as its own distinct signal -- never
    Echo/the MacBook's location. Thin, clearly-named wrapper around
    get_location_from_symbiote() so callers don't have to know that
    "symbiote" means "phone." Returns None if unavailable; callers should
    check the "stale" field before treating a real result as current."""
    return get_location_from_symbiote()

def get_location_from_ip():
    """
    Geolocate via outbound IP -- this machine's (the MacBook's, i.e.
    Echo's own) real physical network location, independent of Gremlin's
    phone. Returns lat, lon, timezone or None on failure.

    Uses ip-api.com, not ipapi.co: confirmed live 2026-09-09 (per
    PENDING_DECISIONS #23) that ipapi.co's free tier now returns
    HTTP 429 "RateLimited... sign up for a paid plan" unconditionally --
    a real, structural service change, not a transient outage retries
    would fix. ip-api.com is free, requires no API key, and was verified
    live to return a real result before this switch was made.
    """
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "success":
            return None
        lat = data.get("lat")
        lon = data.get("lon")
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

def get_macbook_location(default_lat=49.2057, default_lon=-122.9110,
                          default_timezone="America/Vancouver"):
    """
    Echo/the MacBook's own real physical location -- used for the actual
    environment Echo is running in (date/time/weather). Never the phone's
    location; see this section's header comment for why they're split.

    Resolution order:
    1. IP geolocation (this machine's real network location)
    2. Hardcoded default (Delta/New Westminster area)
    """
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
    Return formatted string with location, time, season, and weather --
    Echo/the MacBook's own environment. Location resolves via
    get_macbook_location() only (IP geolocation, falling back to a
    hardcoded default) -- deliberately never Gremlin's phone location;
    see the "Auto Location Detection" section header comment for why
    (PENDING_DECISIONS.md #23).
    """
    location = get_macbook_location(
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
