import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from aiogram.client.default import DefaultBotProperties
from gtts import gTTS
from deep_translator import GoogleTranslator
from config import TOKEN
from aiogram.methods import SetMyCommands
from aiogram.types import BotCommand

# Логирование
logging.basicConfig(level=logging.INFO)

# Создание папок
os.makedirs("img", exist_ok=True)
os.makedirs("audio", exist_ok=True)

# Инициализация бота
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# 📸 Сохранение фото
@dp.message(F.photo)
async def save_photo(message: Message):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    filename = f"img/{photo.file_id}.jpg"
    await bot.download_file(file.file_path, filename)
    await message.reply(f"✅ Фото сохранено как: {filename}")


# 🎙️ Голосовое сообщение по команде /voice <текст>
@dp.message(Command("voice"))
async def voice_command(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Использование: /voice <текст>")

    text = parts[1].strip()
    if not text:
        return await message.reply("⚠️ Пустой текст")
    if len(text) > 500:
        return await message.reply("⚠️ Текст слишком длинный (до 500 символов)")

    filename = f"audio/{message.message_id}.mp3"

    async with ChatActionSender.record_voice(bot=bot, chat_id=message.chat.id):
        try:
            tts = gTTS(text=text, lang='ru')
            tts.save(filename)
            await message.reply_voice(types.FSInputFile(filename), caption="🔊 Ваше голосовое сообщение")
        finally:
            if os.path.exists(filename):
                os.remove(filename)


# 🌍 Перевод с русского на английский
@dp.message(F.text & ~F.text.startswith("/"))
async def translate_text(message: Message):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            translation = GoogleTranslator(source="ru", target="en").translate(message.text)
            await message.reply(f"🔤 Перевод:\n<code>{translation}</code>")
        except Exception as e:
            logging.error(f"Ошибка перевода: {e}")
            await message.reply("⚠️ Не удалось перевести текст.")


# 🚀 Запуск
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
