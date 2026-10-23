"""날씨 데이터를 제공하는 MCP 서버."""

import json
from typing import Literal

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "weather",
    host="127.0.0.1",
    port=8000,
    stateless_http=True,
    json_response=True,
)

City = Literal["서울", "부산", "제주"]
WEATHER_DATA = {
    "서울": {
        "current": {"temperature": 22, "humidity": 50},
        "forecast": {"min_temperature": 18, "max_temperature": 25, "rain_probability": 20},
    },
    "부산": {
        "current": {"temperature": 24, "humidity": 65},
        "forecast": {"min_temperature": 20, "max_temperature": 27, "rain_probability": 30},
    },
    "제주": {
        "current": {"temperature": 23, "humidity": 70},
        "forecast": {"min_temperature": 19, "max_temperature": 26, "rain_probability": 60},
    },
}


@mcp.tool()
def get_current_weather(city: City) -> dict:
    """서울·부산·제주 중 한 도시의 현재 기온과 습도를 반환한다."""
    return {
        "city": city,
        "current": WEATHER_DATA[city]["current"],
        "units": {"temperature": "°C", "humidity": "%"},
    }


@mcp.tool()
def get_weather_forecast(city: City) -> dict:
    """서울·부산·제주 중 한 도시의 최저·최고 기온과 강수 확률을 반환한다."""
    return {
        "city": city,
        "forecast": WEATHER_DATA[city]["forecast"],
        "units": {"min_temperature": "°C", "max_temperature": "°C", "rain_probability": "%"},
    }


@mcp.resource("weather://cities")
def supported_cities() -> str:
    """조회할 수 있는 도시 목록을 반환한다."""
    return json.dumps(list(WEATHER_DATA), ensure_ascii=False)


@mcp.prompt()
def weather_briefing(city: City) -> str:
    """현재 날씨와 예보를 요청하는 메시지를 만든다."""
    return (
        f"{city}의 현재 날씨와 예보를 도구로 조회해 주세요. "
        "현재 값과 예보를 구분하고 단위를 포함해 정리해 주세요."
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
