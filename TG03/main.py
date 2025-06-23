import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния для FSM
class StudentForm(StatesGroup):
    name = State()
    age = State()
    grade = State()

# Создание базы данных и таблицы
def init_db():
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            grade TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Обработка команды /start
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    await state.set_state(StudentForm.name)

# Имя
@dp.message(StudentForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(StudentForm.age)

# Возраст
@dp.message(StudentForm.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи возраст числом.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("В каком ты классе? (например: 5А или 10Б)")
    await state.set_state(StudentForm.grade)

# Класс (grade)
@dp.message(StudentForm.grade)
async def process_grade(message: types.Message, state: FSMContext):
    await state.update_data(grade=message.text)
    data = await state.get_data()

    # Сохранение в базу данных
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO students (name, age, grade)
        VALUES (?, ?, ?)
    ''', (data['name'], data['age'], data['grade']))
    conn.commit()
    conn.close()

    await message.answer(f"Спасибо! Данные сохранены:\n"
                         f"Имя: {data['name']}\n"
                         f"Возраст: {data['age']}\n"
                         f"Класс: {data['grade']}")
    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
