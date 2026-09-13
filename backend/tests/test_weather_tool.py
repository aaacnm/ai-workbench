import httpx
import pytest

from app.tools.weather_tool import WeatherInput, WeatherToolError, get_weather


def test_get_weather_success():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding" in str(request.url):
            return httpx.Response(200, json={"results": [{"name": "北京", "country": "中国", "latitude": 39.9, "longitude": 116.4}]})
        return httpx.Response(200, json={"current": {"temperature_2m": 25, "relative_humidity_2m": 50, "wind_speed_10m": 8, "weather_code": 0, "time": "2026-09-12T12:00"}, "current_units": {"temperature_2m": "°C"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = get_weather(WeatherInput(city="北京"), client)
    assert result["city"] == "北京"
    assert result["weather"] == "晴"


def test_get_weather_city_not_found():
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"results": []})))
    with pytest.raises(WeatherToolError, match="找不到城市"):
        get_weather(WeatherInput(city="不存在的城市"), client)
