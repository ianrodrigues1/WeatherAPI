from flask import Blueprint, jsonify, request

from services.weather_service import (
    CityNotFoundError,
    WeatherConfigurationError,
    WeatherProviderError,
    get_current_weather_by_coordinates,
    get_current_weather,
    search_city_suggestions,
)

weather_bp = Blueprint("weather", __name__, url_prefix="/api")


@weather_bp.get("/weather")
def weather():
    city = request.args.get("city", "").strip()
    lat = request.args.get("lat", "").strip()
    lon = request.args.get("lon", "").strip()
    country = request.args.get("country", "").strip()

    if lat and lon:
        try:
            return jsonify(get_current_weather_by_coordinates(lat, lon, city=city, country=country))
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "invalid_coordinates",
                        "message": "Informe latitude e longitude validas.",
                    }
                ),
                400,
            )
        except WeatherConfigurationError as exc:
            return (
                jsonify(
                    {
                        "error": "configuration_error",
                        "message": str(exc),
                    }
                ),
                500,
            )
        except WeatherProviderError:
            return (
                jsonify(
                    {
                        "error": "weather_provider_error",
                        "message": "Nao foi possivel consultar o provedor de clima agora. Tente novamente em instantes.",
                    }
                ),
                502,
            )

    if not city:
        return (
            jsonify(
                {
                    "error": "missing_city",
                    "message": "Informe uma cidade usando o parametro ?city=NomeDaCidade.",
                }
            ),
            400,
        )

    try:
        return jsonify(get_current_weather(city))
    except CityNotFoundError:
        return (
            jsonify(
                {
                    "error": "city_not_found",
                    "message": f"Nao encontramos dados de clima para '{city}'. Verifique o nome e tente novamente.",
                }
            ),
            404,
        )
    except WeatherConfigurationError as exc:
        return (
            jsonify(
                {
                    "error": "configuration_error",
                    "message": str(exc),
                }
            ),
            500,
        )
    except WeatherProviderError:
        return (
            jsonify(
                {
                    "error": "weather_provider_error",
                    "message": "Nao foi possivel consultar o provedor de clima agora. Tente novamente em instantes.",
                }
            ),
            502,
        )


@weather_bp.get("/cities")
def cities():
    query = request.args.get("query", "").strip()

    if len(query) < 2:
        return jsonify({"query": query, "suggestions": []})

    try:
        return jsonify({"query": query, "suggestions": search_city_suggestions(query)})
    except WeatherConfigurationError as exc:
        return (
            jsonify(
                {
                    "error": "configuration_error",
                    "message": str(exc),
                }
            ),
            500,
        )
    except WeatherProviderError:
        return (
            jsonify(
                {
                    "error": "weather_provider_error",
                    "message": "Nao foi possivel buscar sugestoes de cidades agora.",
                }
            ),
            502,
        )
