from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BTN_WEATHER = InlineKeyboardButton('Weather', callback_data='weather')
BTN_WIND = InlineKeyboardButton('Wind', callback_data='wind')
WEATHER = InlineKeyboardMarkup().add(BTN_WIND)
WIND = InlineKeyboardMarkup().add(BTN_WEATHER)
HELP = InlineKeyboardMarkup().add(BTN_WEATHER, BTN_WIND)
END = InlineKeyboardMarkup()
