from typing import Any

import httpx
from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    city: str = Field(min_length=1, max_length=50)


class WeatherToolError(ValueError):
    """Raised when weather data cannot be retrieved."""


WEATHER_CODE_MAP = {
    0: "晴",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小雨",
    53: "中雨",
    55: "大雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "阵雨",
    81: "中阵雨",
    82: "强阵雨",
    95: "雷雨",
    96: "雷雨伴冰雹",
    99: "强雷雨伴冰雹",
}


def get_weather(payload: WeatherInput, client: httpx.Client | None = None) -> dict[str, Any]:
    """Look up a city's current weather using Open-Meteo."""
    http_client = client or httpx.Client(timeout=httpx.Timeout(10.0))
    close_client = client is None
    try:
        location_response = http_client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": payload.city, "count": 1, "language": "zh", "format": "json"},
        )
        location_response.raise_for_status()
        locations = location_response.json().get("results", [])
        if not locations:
            raise WeatherToolError(f"找不到城市: {payload.city}")

        location = locations[0]
        weather_response = http_client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        weather_response.raise_for_status()
        current = weather_response.json().get("current")
        if not current:
            raise WeatherToolError("天气接口没有返回当前天气")
        return {
            "city": location.get("name", payload.city),
            "country": location.get("country", ""),
            "temperature": current.get("temperature_2m"),
            "temperature_unit": weather_response.json().get("current_units", {}).get("temperature_2m", "°C"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "weather": WEATHER_CODE_MAP.get(current.get("weather_code"), "未知天气"),
            "observed_at": current.get("time"),
        }
    except WeatherToolError:
        raise
    except httpx.TimeoutException as exc:
        raise WeatherToolError("天气服务请求超时") from exc
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise WeatherToolError("天气服务请求失败") from exc
    finally:
        if close_client:
            http_client.close()
