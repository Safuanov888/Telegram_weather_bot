from bot import get_coordinates, get_weather


def weather(city) -> str:
    current_weather = get_weather(get_coordinates(city))
    return (f'Локация: {current_weather.location} Обстановка: {current_weather.description}, {current_weather.param}\n'
            f'Температура: {current_weather.temperature}°C, ощущается как: {current_weather.temperature_feeling}°C')


def wind(city) -> str:
    current_weather = get_weather(get_coordinates(city))
    return (f'Направление ветра: {current_weather.wind_direction}, скорость {current_weather.wind_speed} м/с')
