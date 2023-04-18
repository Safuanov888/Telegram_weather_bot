import sys
import time

import json
from loguru import logger
from aiogram import Bot, Dispatcher, executor, types  # type: ignore
from aiogram.dispatcher.filters.state import StatesGroup, State  # type: ignore
from aiogram.dispatcher import FSMContext  # type: ignore
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # type: ignore
from dataclasses import dataclass
from urllib.request import urlopen
from typing import TypeAlias
from enum import IntEnum
from translatepy.translators.google import GoogleTranslate  # type: ignore

import key
import Inline
import messages

TOKEN = "5935561015:AAFTFufDGVRzE1q31Q-KEDmZ1cstk4az3ys"
translator = GoogleTranslate()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
Celsius: TypeAlias = float


# weather
@dataclass(slots=True, frozen=True)
class Coordinates:
    latitude: float
    longitude: float


class City(StatesGroup):
    start_name = State()


@dataclass(slots=True, frozen=True)
class Weather:
    location: str
    temperature: Celsius
    temperature_feeling: Celsius
    param: str
    description: str
    wind_speed: float
    wind_direction: str


class WindDirection(IntEnum):
    North = 0
    Northeast = 45
    East = 90
    Southeast = 135
    South = 180
    Southwest = 225
    West = 270
    Northwest = 315


def get_weather(coordinates=Coordinates) -> Weather:
    openweather_responce = _get_openweather(latitude=coordinates.latitude, longitude=coordinates.longitude)
    weather = _parse_openweather(openweather_responce)
    return weather


def _get_openweather(latitude: float, longitude: float) -> str:
    url = key.CURRENT_WEATHER_API_CALL.format(latitude=latitude, longitude=longitude)
    return urlopen(url).read()


def _parse_openweather(openweather_responce: str) -> Weather:
    openweather_dict = json.loads(openweather_responce)
    return Weather(
        location=_parse_location(openweather_dict),
        param=_parse_param(openweather_dict),
        temperature=_parse_temperature(openweather_dict),
        temperature_feeling=_parse_temperature_feeling(openweather_dict),
        description=_parse_description(openweather_dict),
        wind_speed=_parse_wind_speed(openweather_dict),
        wind_direction=_parse_wind_direction(openweather_dict)
    )


def _parse_location(openweather_dict: dict) -> str:
    translate = translator.translate(openweather_dict['name'], 'Русский')
    return translate


def _parse_param(openweather_dict: dict) -> str:
    translate = translator.translate(openweather_dict['weather'][0]['main'], 'Русский')
    return translate


def _parse_temperature(openweather_dict: dict) -> float:
    return openweather_dict['main']['temp']


def _parse_temperature_feeling(openweather_dict: dict) -> Celsius:
    return openweather_dict['main']['feels_like']


def _parse_description(openweather_dict: dict) -> str:
    translate = translator.translate(str(openweather_dict['weather'][0]['description']).capitalize(), 'Русский')
    return translate


def _parse_wind_speed(openweather_dict: dict) -> float:
    return openweather_dict['wind']['speed']


def _parse_wind_direction(openweather_dict: dict) -> str:
    degrees = openweather_dict['wind']['deg']
    degrees = round(degrees / 45) * 45
    if degrees == 360:
        degrees = 0
    translate = translator.translate(WindDirection(degrees).name, 'Русский')
    return translate


def get_coordinates_data(city: str) -> dict:
    url = f'http://nominatim.openstreetmap.org/search/{city}?format=json&addressdetails=1&limit=1&polygon_svg=1'
    responce = urlopen(url).read()
    return json.loads(responce)


def get_coordinates(city: str) -> Coordinates:
    data = get_coordinates_data(city)
    latitude = data[0]['lat']
    longitude = data[0]['lon']
    return Coordinates(latitude=latitude, longitude=longitude)


@dp.message_handler(commands='start')
async def show_weather(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name

    btn_markup = types.ReplyKeyboardMarkup()

    btn_start = types.KeyboardButton('/start')
    btn_end = types.KeyboardButton('/end')
    btn_help = types.KeyboardButton('/help')
    btn_weather = types.KeyboardButton('/weather')
    btn_wind = types.KeyboardButton('/wind')

    btn_markup.add(btn_start, btn_help, btn_end).add(btn_weather, btn_wind)

    await message.reply(f"Добро пожаловать! {user_name}")

    await message.answer(f'Кнопочки в действии', reply_markup=btn_markup)

    logger.info(f"{user_id} {user_full_name} {time.asctime()}")


@dp.message_handler(commands=['weather'], state=None)
async def start_message(message: types.Message):
    await bot.send_message(message.from_user.id,
                           text=f'Напиши город, в котором хочешь посмотреть погоду в формате:'
                                f' город, страна (через запятую)')
    await City.start_name.set()


@dp.message_handler(state=City.start_name)
async def name(message: types.Message, state: FSMContext):
    global translation_text
    text = message.text
    translation_text = ''.join(str(translator.translate(text, 'English')).split())
    await bot.send_message(message.from_user.id, text=messages.weather(translation_text),
                           reply_markup=Inline.WEATHER)
    await state.finish()


@dp.callback_query_handler(text='weather')
async def process_callback_wind(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        text=messages.weather(translation_text),
        reply_markup=Inline.WEATHER
    )


@dp.message_handler(commands='help')
async def show_help_message(message: types.Message):
    await message.answer(
        text=f'Этот бот умеет вычислять текущую погоду по IP адресу',
        reply_markup=Inline.HELP)


@dp.message_handler(commands='wind')
async def show_wind(message: types.Message):
    if City.start_name != City.start_name.set():
        await message.answer(f'Введите сначала погоду, чтобы узнать скорость ветра')
    await message.answer(
        text=messages.wind(translation_text),
        reply_markup=Inline.WIND)


@dp.callback_query_handler(text='wind')
async def process_callback_wind(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        text=messages.wind(translation_text),
        reply_markup=Inline.WIND
    )


@dp.message_handler(commands=['end'])
async def end_handler(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name

    logger.info(f"{user_id} {user_full_name} {time.asctime()}")
    await message.answer(text=f"До свидания! {user_name}",
                         reply_markup=Inline.END)
    await bot.delete_message(message.chat.id, message.message_id)
    sys.exit()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
