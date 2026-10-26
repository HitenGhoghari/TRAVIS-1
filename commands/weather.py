import re
import time

import requests

from config import (
    OPENWEATHER_API_KEY,
    HOME_CITY,
    HOME_COUNTRY,
    USE_IP_LOCATION,
    WEATHER_UNITS,
)

GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
IP_URL = "http://ip-api.com/json/"

RAIN_MAINS = {"Rain", "Drizzle", "Thunderstorm", "Snow"}

_user_location_cache = "unset"


# ---------- Helpers ----------
def _clean_city(raw):
    if not raw:
        return None
    city = raw.strip().strip(" .,?!")
    city = re.sub(r"^(like|in|at|for)\s+", "", city, flags=re.IGNORECASE)
    city = re.sub(
        r"\s+(today|tonight|right now|currently|now|outside|this weekend)\s*$",
        "", city, flags=re.IGNORECASE,
    )
    return city.strip() or None


def _detect_ip_location():
    try:
        r = requests.get(IP_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            return None
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            return None
        city = data.get("city") or ""
        country = data.get("countryCode", "")
        place = f"{city}, {country}" if country else city
        return {"lat": lat, "lon": lon, "place": place, "country": country}
    except requests.RequestException:
        return None


def _get_user_location():
    global _user_location_cache
    if not USE_IP_LOCATION:
        return None
    if _user_location_cache == "unset":
        _user_location_cache = _detect_ip_location()
    return _user_location_cache


def _geocode(city, prefer_country=None):
    r = requests.get(
        GEO_URL,
        params={"q": city, "limit": 5, "appid": OPENWEATHER_API_KEY},
        timeout=8,
    )
    if r.status_code == 401:
        raise RuntimeError("auth")
    r.raise_for_status()
    data = r.json()
    if not data:
        raise LookupError(city)

    if prefer_country:
        for loc in data:
            if loc.get("country", "").upper() == prefer_country.upper():
                return (
                    loc["lat"], loc["lon"],
                    loc.get("name", city), loc.get("country", ""),
                )

    loc = data[0]
    return (
        loc["lat"], loc["lon"],
        loc.get("name", city), loc.get("country", ""),
    )


def _resolve_place(raw_city):
    city = _clean_city(raw_city)
    user_loc = _get_user_location()

    # Country preference: IP-detected country if available,
    # otherwise HOME_COUNTRY from config.
    # This is what makes "Surat" resolve to IN, not FR.
    prefer_country = user_loc["country"] if user_loc else HOME_COUNTRY

    # Explicit city in the question — always honor it,
    # but still bias toward the preferred country.
    if city:
        lat, lon, name, country = _geocode(city, prefer_country=prefer_country)
        place = f"{name}, {country}" if country else name
        return lat, lon, place

    # IP-based (only if enabled)
    if user_loc:
        return user_loc["lat"], user_loc["lon"], user_loc["place"]

    # Default: HOME_CITY from config, with HOME_COUNTRY preference
    lat, lon, name, country = _geocode(HOME_CITY, prefer_country=prefer_country)
    place = f"{name}, {country}" if country else name
    return lat, lon, place


def _temp_unit():
    return "Celsius" if WEATHER_UNITS == "metric" else "Fahrenheit"


def _speed_unit():
    return "kilometres per hour" if WEATHER_UNITS == "metric" else "miles per hour"


def _speak_weather(data, place):
    main = data.get("main", {})
    wind = data.get("wind", {})
    desc = (data.get("weather") or [{}])[0].get("description", "unknown conditions")

    temp = round(main.get("temp", 0))
    feels = round(main.get("feels_like", temp))
    humidity = main.get("humidity", 0)
    wind_speed = round(wind.get("speed", 0) * (3.6 if WEATHER_UNITS == "metric" else 1))

    sentence = f"It's {temp} degrees {_temp_unit()} in {place} with {desc}."
    if abs(feels - temp) >= 2:
        sentence += f" Feels like {feels}."
    sentence += f" Humidity {humidity} percent, wind {wind_speed} {_speed_unit()}."
    return sentence


def _aqi_label(aqi):
    return {1: "good", 2: "fair", 3: "moderate", 4: "poor", 5: "very poor"}.get(aqi, "unknown")


def _friendly_error(err):
    if isinstance(err, LookupError):
        return f"I couldn't find a place called {err.args[0]}."
    if isinstance(err, RuntimeError):
        return ("My weather API key isn't active yet. "
                "New OpenWeatherMap keys can take up to two hours to activate.")
    if isinstance(err, requests.RequestException):
        return "I couldn't reach the weather service right now."
    return "Sorry, something went wrong with the weather lookup."


# ---------- Handlers ----------
def _weather(match, text):
    if not OPENWEATHER_API_KEY:
        return "Weather isn't configured yet. Add OPENWEATHER_API_KEY to your env file."
    try:
        raw_city = match.group(1) if match.groups() else None
        lat, lon, place = _resolve_place(raw_city)
        r = requests.get(
            WEATHER_URL,
            params={"lat": lat, "lon": lon, "units": WEATHER_UNITS, "appid": OPENWEATHER_API_KEY},
            timeout=8,
        )
        if r.status_code == 401:
            raise RuntimeError("auth")
        r.raise_for_status()
        return _speak_weather(r.json(), place)
    except (LookupError, RuntimeError, requests.RequestException) as e:
        return _friendly_error(e)


def _rain(match, text):
    if not OPENWEATHER_API_KEY:
        return "Weather isn't configured yet. Add OPENWEATHER_API_KEY to your env file."
    try:
        raw_city = match.group(1) if match.groups() else None
        lat, lon, place = _resolve_place(raw_city)
        r = requests.get(
            FORECAST_URL,
            params={"lat": lat, "lon": lon, "units": WEATHER_UNITS, "appid": OPENWEATHER_API_KEY},
            timeout=8,
        )
        if r.status_code == 401:
            raise RuntimeError("auth")
        r.raise_for_status()

        slots = r.json().get("list", [])
        cutoff = time.time() + 12 * 3600
        rainy = [
            s for s in slots
            if s.get("dt", 0) <= cutoff
            and any(w.get("main") in RAIN_MAINS for w in s.get("weather", []))
        ]

        if rainy:
            first = time.strftime("%H:%M", time.localtime(rainy[0]["dt"]))
            return f"Yes, rain is likely in {place} within the next 12 hours, first around {first}."
        return f"No rain expected in {place} over the next 12 hours."
    except (LookupError, RuntimeError, requests.RequestException) as e:
        return _friendly_error(e)


def _forecast(match, text):
    if not OPENWEATHER_API_KEY:
        return "Weather isn't configured yet. Add OPENWEATHER_API_KEY to your env file."
    try:
        raw_city = match.group(1) if match.groups() else None
        lat, lon, place = _resolve_place(raw_city)
        r = requests.get(
            FORECAST_URL,
            params={"lat": lat, "lon": lon, "units": WEATHER_UNITS, "appid": OPENWEATHER_API_KEY},
            timeout=8,
        )
        if r.status_code == 401:
            raise RuntimeError("auth")
        r.raise_for_status()

        slots = r.json().get("list", [])
        days = {}
        for s in slots:
            day = time.strftime("%A", time.localtime(s["dt"]))
            days.setdefault(day, []).append(s)

        summaries = []
        for day, entries in list(days.items())[:3]:
            temps = [e["main"]["temp"] for e in entries]
            descs = [e["weather"][0]["description"] for e in entries]
            common = max(set(descs), key=descs.count)
            summaries.append(
                f"{day}: around {round(sum(temps)/len(temps))} degrees with {common}"
            )

        if not summaries:
            return f"I couldn't build a forecast for {place} right now."
        return f"Forecast for {place}. " + ". ".join(summaries) + "."
    except (LookupError, RuntimeError, requests.RequestException) as e:
        return _friendly_error(e)


def _air_quality(match, text):
    if not OPENWEATHER_API_KEY:
        return "Weather isn't configured yet. Add OPENWEATHER_API_KEY to your env file."
    try:
        raw_city = match.group(1) if match.groups() else None
        lat, lon, place = _resolve_place(raw_city)
        r = requests.get(
            AIR_URL,
            params={"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY},
            timeout=8,
        )
        if r.status_code == 401:
            raise RuntimeError("auth")
        r.raise_for_status()

        data = r.json().get("list", [])
        if not data:
            return f"I couldn't get air quality for {place} right now."
        aqi = data[0]["main"]["aqi"]
        pm2 = data[0]["components"].get("pm2_5")
        pm2_text = f", particulate matter 2.5 at {round(pm2)} micrograms per cubic metre" if pm2 is not None else ""
        return f"Air quality in {place} is {_aqi_label(aqi)}{pm2_text}."
    except (LookupError, RuntimeError, requests.RequestException) as e:
        return _friendly_error(e)


# ---------- Command table ----------
COMMANDS = [
    # Current weather
    (r"\b(?:what'?s|what is|how'?s|how is)\s+(?:the\s+)?weather"
     r"(?:\s+like)?(?:\s+(?:in|at|for)\s+(.+?))?\s*[.?!]?\s*$", _weather),
    (r"\bweather\s+(?:like\s+)?(?:in|at|for)\s+(.+?)\s*[.?!]?\s*$", _weather),
    (r"\b(?:temperature|temp)\s+(?:in|at|for)\s+(.+?)\s*[.?!]?\s*$", _weather),
    (r"\b(?:what'?s|what is)\s+the\s+temperature"
     r"(?:\s+(?:in|at|for)\s+(.+?))?\s*[.?!]?\s*$", _weather),
    (r"\bhow\s+(?:hot|cold|warm)\s+is\s+it"
     r"(?:\s+in\s+(.+?))?\s*[.?!]?\s*$", _weather),

    # Rain — broadened to survive Whisper mangling "will it"
    (r"\b(?:will\s+it|is\s+it\s+(?:going\s+to|gonna))\s+rain"
     r"(?:\s+(?:today|tonight))?"
     r"(?:\s+(?:in|at)\s+(.+?))?\s*[.?!]?\s*$", _rain),
    (r"\brain\b(?:\s+(?:today|tonight))?\s+(?:in|at)\s+(.+?)\s*[.?!]?\s*$", _rain),
    (r"\bdo\s+i\s+need\s+an\s+umbrella"
     r"(?:\s+(?:in|at)\s+(.+?))?\s*[.?!]?\s*$", _rain),

    # Forecast
    (r"\b(?:forecast|weather\s+forecast)(?:\s+(?:in|at|for)\s+(.+?))?\s*[.?!]?\s*$", _forecast),
    (r"\bweather\s+(?:for\s+)?(?:the\s+)?(?:next\s+few\s+days|this\s+week|tomorrow)"
     r"(?:\s+(?:in|at)\s+(.+?))?\s*[.?!]?\s*$", _forecast),
    (r"\bforecast\s+for\s+(.+?)\s*[.?!]?\s*$", _forecast),

    # Air quality
    (r"\bair\s+quality(?:\s+(?:in|at|for)\s+(.+?))?\s*[.?!]?\s*$", _air_quality),
    (r"\bhow\s+(?:polluted|smoggy)\s+is\s+it(?:\s+(?:in|at)\s+(.+?))?\s*[.?!]?\s*$", _air_quality),
]