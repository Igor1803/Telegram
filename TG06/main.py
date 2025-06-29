import asyncio
import random
import logging
import aiohttp
import aiosqlite
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, KeyboardButton, ReplyKeyboardMarkup, BotCommand
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, EXCHANGE_API_KEY

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot and Dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Keyboards
button_registr = KeyboardButton(text="Регистрация в телеграм боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")
button_my_expenses = KeyboardButton(text="Мои расходы")

keyboards = ReplyKeyboardMarkup(
    keyboard=[
        [button_registr, button_exchange_rates],
        [button_tips, button_finances],
        [button_my_expenses]
    ], resize_keyboard=True
)

# States
class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()

# Database init
async def init_db():
    try:
        async with aiosqlite.connect("user.db") as db:
            await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                category1 TEXT,
                category2 TEXT,
                category3 TEXT,
                expenses1 REAL,
                expenses2 REAL,
                expenses3 REAL
            )''')
            await db.commit()
            logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")

# Validation functions
def validate_amount(amount_str: str) -> bool:
    """Проверяет корректность введенной суммы"""
    try:
        amount = float(amount_str)
        return amount >= 0
    except ValueError:
        return False

def validate_category(category: str) -> bool:
    """Проверяет корректность названия категории"""
    return len(category.strip()) > 0 and len(category) <= 50

# Handlers
@dp.message(CommandStart())
async def send_start(message: Message):
    await message.answer(
        "Привет! Я ваш личный финансовый помощник. 🏦\n\n"
        "Я помогу вам:\n"
        "• Отслеживать расходы по категориям\n"
        "• Узнавать актуальные курсы валют\n"
        "• Получать советы по экономии\n\n"
        "Выберите одну из опций в меню:", 
        reply_markup=keyboards
    )

@dp.message(Command("help"))
async def send_help(message: Message):
    help_text = """
📋 Доступные команды:
/start — запуск бота
/help — показать эту справку
/cancel — отменить текущую операцию

💡 Функции бота:
• Регистрация в системе
• Отслеживание курсов валют
• Советы по экономии
• Ведение личных финансов
• Просмотр ваших расходов
    """
    await message.answer(help_text)

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция отменена. ❌")

@dp.message(F.text == "Регистрация в телеграм боте")
async def registration(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    
    try:
        async with aiosqlite.connect("user.db") as db:
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                user = await cursor.fetchone()
                if user:
                    await message.answer("Вы уже зарегистрированы! ✅")
                    return
            
            await db.execute("INSERT INTO users (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
            await db.commit()
            await message.answer("Вы успешно зарегистрированы! 🎉")
    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")

@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message):
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/USD"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    await message.answer("❌ Не удалось получить курс валют. Попробуйте позже.")
                    return
                
                data = await response.json()
                usd_to_rub = data['conversion_rates']['RUB']
                eur_to_usd = data['conversion_rates']['EUR']
                eur_to_rub = usd_to_rub * eur_to_usd
                
                rates_text = f"""
💱 Актуальные курсы валют:

🇺🇸 USD → 🇷🇺 RUB: {usd_to_rub:.2f}
🇪🇺 EUR → 🇷🇺 RUB: {eur_to_rub:.2f}
🇪🇺 EUR → 🇺🇸 USD: {eur_to_usd:.4f}

📅 Обновлено: {data.get('time_last_update_utc', 'Неизвестно')}
                """
                await message.answer(rates_text)
    except asyncio.TimeoutError:
        await message.answer("⏰ Превышено время ожидания ответа от сервера.")
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")
        await message.answer("❌ Произошла ошибка при получении данных.")

@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
    tips = [
        "💰 Совет 1: Ведите бюджет и следите за расходами каждый день",
        "💳 Совет 2: Откладывайте 10-20% от каждого дохода на сбережения",
        "🛒 Совет 3: Пользуйтесь скидками, акциями и кэшбэком",
        "🏠 Совет 4: Оптимизируйте коммунальные расходы",
        "🚗 Совет 5: Используйте общественный транспорт вместо такси",
        "🍽️ Совет 6: Готовьте еду дома вместо ресторанов",
        "📱 Совет 7: Отключите ненужные подписки",
        "🎯 Совет 8: Ставьте финансовые цели и следуйте им"
    ]
    tip = random.choice(tips)
    await message.answer(f"💡 {tip}")

@dp.message(F.text == "Мои расходы")
async def show_expenses(message: Message):
    telegram_id = message.from_user.id
    
    try:
        async with aiosqlite.connect("user.db") as db:
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                user = await cursor.fetchone()
                
                if not user:
                    await message.answer("Сначала зарегистрируйтесь! 📝")
                    return
                
                if not user[3]:  # Если нет категорий
                    await message.answer("У вас пока нет сохраненных расходов. Добавьте их через 'Личные финансы'")
                    return
                
                total = 0
                expenses_text = "📊 Ваши расходы:\n\n"
                
                if user[3]:  # category1
                    expenses_text += f"• {user[3]}: {user[6]:.2f} руб.\n"
                    total += user[6] or 0
                if user[4]:  # category2
                    expenses_text += f"• {user[4]}: {user[7]:.2f} руб.\n"
                    total += user[7] or 0
                if user[5]:  # category3
                    expenses_text += f"• {user[5]}: {user[8]:.2f} руб.\n"
                    total += user[8] or 0
                
                expenses_text += f"\n💵 Общая сумма: {total:.2f} руб."
                await message.answer(expenses_text)
    except Exception as e:
        logger.error(f"Ошибка показа расходов: {e}")
        await message.answer("Произошла ошибка при получении данных.")

@dp.message(F.text == "Личные финансы")
async def start_finance_input(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    
    # Проверяем регистрацию
    try:
        async with aiosqlite.connect("user.db") as db:
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                user = await cursor.fetchone()
                if not user:
                    await message.answer("Сначала зарегистрируйтесь! 📝")
                    return
    except Exception as e:
        logger.error(f"Ошибка проверки регистрации: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
        return
    
    await state.set_state(FinancesForm.category1)
    await message.answer("Введите первую категорию расходов (например: Продукты):")

@dp.message(FinancesForm.category1)
async def input_category1(message: Message, state: FSMContext):
    category = message.text.strip()
    
    if not validate_category(category):
        await message.answer("❌ Название категории должно быть не пустым и не длиннее 50 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(category1=category)
    await state.set_state(FinancesForm.expenses1)
    await message.answer(f"Введите расходы для категории '{category}' (в рублях):")

@dp.message(FinancesForm.expenses1)
async def input_expenses1(message: Message, state: FSMContext):
    if not validate_amount(message.text):
        await message.answer("❌ Введите корректную сумму (число больше или равное 0):")
        return
    
    await state.update_data(expenses1=float(message.text))
    await state.set_state(FinancesForm.category2)
    await message.answer("Введите вторую категорию расходов (или /skip для пропуска):")

@dp.message(FinancesForm.category2)
async def input_category2(message: Message, state: FSMContext):
    if message.text.lower() == '/skip':
        await state.update_data(category2=None, expenses2=0)
        await state.set_state(FinancesForm.category3)
        await message.answer("Введите третью категорию расходов (или /skip для пропуска):")
        return
    
    category = message.text.strip()
    
    if not validate_category(category):
        await message.answer("❌ Название категории должно быть не пустым и не длиннее 50 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(category2=category)
    await state.set_state(FinancesForm.expenses2)
    await message.answer(f"Введите расходы для категории '{category}' (в рублях):")

@dp.message(FinancesForm.expenses2)
async def input_expenses2(message: Message, state: FSMContext):
    if not validate_amount(message.text):
        await message.answer("❌ Введите корректную сумму (число больше или равное 0):")
        return
    
    await state.update_data(expenses2=float(message.text))
    await state.set_state(FinancesForm.category3)
    await message.answer("Введите третью категорию расходов (или /skip для пропуска):")

@dp.message(FinancesForm.category3)
async def input_category3(message: Message, state: FSMContext):
    if message.text.lower() == '/skip':
        await state.update_data(category3=None, expenses3=0)
        await save_finances(message, state)
        return
    
    category = message.text.strip()
    
    if not validate_category(category):
        await message.answer("❌ Название категории должно быть не пустым и не длиннее 50 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(category3=category)
    await state.set_state(FinancesForm.expenses3)
    await message.answer(f"Введите расходы для категории '{category}' (в рублях):")

@dp.message(FinancesForm.expenses3)
async def input_expenses3(message: Message, state: FSMContext):
    if not validate_amount(message.text):
        await message.answer("❌ Введите корректную сумму (число больше или равное 0):")
        return
    
    await state.update_data(expenses3=float(message.text))
    await save_finances(message, state)

async def save_finances(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = message.from_user.id
    
    try:
        async with aiosqlite.connect("user.db") as db:
            await db.execute('''
                UPDATE users SET 
                    category1 = ?, expenses1 = ?,
                    category2 = ?, expenses2 = ?,
                    category3 = ?, expenses3 = ?
                WHERE telegram_id = ?
            ''', (
                data['category1'], data['expenses1'],
                data['category2'], data['expenses2'],
                data['category3'], data['expenses3'], telegram_id
            ))
            await db.commit()
        
        # Формируем отчет
        total = data['expenses1'] + (data['expenses2'] or 0) + (data['expenses3'] or 0)
        report = f"""
✅ Данные сохранены!

📊 Ваши расходы:
• {data['category1']}: {data['expenses1']:.2f} руб.
"""
        
        if data['category2']:
            report += f"• {data['category2']}: {data['expenses2']:.2f} руб.\n"
        if data['category3']:
            report += f"• {data['category3']}: {data['expenses3']:.2f} руб.\n"
        
        report += f"\n💵 Общая сумма: {total:.2f} руб."
        
        await message.answer(report)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка сохранения финансов: {e}")
        await message.answer("❌ Произошла ошибка при сохранении данных. Попробуйте позже.")
        await state.clear()

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="cancel", description="Отмена ввода"),
        BotCommand(command="myexpenses", description="Мои расходы"),
        BotCommand(command="finances", description="Личные финансы"),
        BotCommand(command="tips", description="Советы по экономии"),
        BotCommand(command="exchange", description="Курс валют"),
        BotCommand(command="register", description="Регистрация в боте"),
    ]
    await bot.set_my_commands(commands)

# Main
async def main():
    logger.info("Запуск бота...")
    await init_db()
    await set_commands(bot)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == '__main__':
    asyncio.run(main())
