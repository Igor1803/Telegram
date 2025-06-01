import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import random
from config import TOKEN
from config import YANDEX_WEATHER_API_KEY
import requests

bot = Bot(token = TOKEN)
dp = Dispatcher()

@dp.message(F.photo)
async def res_photo(message: Message):
    print("Фото получено!")
    responses = ['Ого, какая фотка!', 'Непонятно, что это такое', 'Не отправляй мне такое больше']
    rand_answ = random.choice(responses)
    await message.answer(rand_answ)


@dp.message(Command('photo'))
async def photo(message: Message):
    print("Фото отправлено!")
    responses = ['https://upload.wikimedia.org/wikipedia/commons/5/5e/Tesla-optimus-bot-gen-2-scaled_%28cropped%29.jpg', 'https://i.pinimg.com/originals/87/84/15/878415254c567bde84994c1e73dc52a2.png', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSbJ4uY_BFChBLYaa2zJ3R_JMKcjMB14XHIiQ&s', 'https://s0.rbk.ru/v6_top_pics/resized/960xH/media/img/6/97/756430096603976.jpg']
    rand_photo = random.choice(responses)
    await message.answer_photo(rand_photo, caption ='Это супер крутая картинка')

@dp.message(F.text == 'Что такое ИИ?')
async def aitext(message: Message):
    await message.answer("ИИ это искуственный интелект")

@dp.message(Command("help"))
async def help(message: Message):
    await message.answer("Вот список команд:\n/start\n/help\n/photo\n/weather")

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Приветики, я бот!")


@dp.message(Command("weather"))
async def weather_handler(message: Message):
    lat, lon = 55.7558, 37.6176  # Москва

    url = f'https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}&lang=ru_RU'
    headers = {'X-Yandex-Weather-Key': YANDEX_WEATHER_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        await message.answer("Не удалось получить погоду.")
        return

    data = response.json()
    fact = data.get('fact', {})
    condition = fact.get('condition', 'неизвестно')
    temp = fact.get('temp', 'н/д')

    conditions = {
        "clear": "Ясно ☀️",
        "partly-cloudy": "Малооблачно 🌤",
        "cloudy": "Облачно ☁️",
        "overcast": "Пасмурно 🌫",
        "rain": "Дождь 🌧",
        "light-rain": "Небольшой дождь 🌦",
    }

    desc = conditions.get(condition, condition)

    await message.answer(f"🌆 Москва\n🌡 Температура: {temp}°C\n☁️ Состояние: {desc}")



async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


