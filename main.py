import os
import random
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import get_new_configured_app
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

user_state = {}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return {"ok": True}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_state[message.chat.id] = 0
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Следующий вопрос", "Рандомный вопрос", "В начало")
    await message.answer("Выберите опцию:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Следующий вопрос")
async def next_question(message: types.Message):
    idx = user_state.get(message.chat.id, 0)
    questions = sheet.col_values(1)
    if idx < len(questions):
        await message.answer(questions[idx])
        user_state[message.chat.id] = idx + 1
    else:
        await message.answer("Проработка завершена. Нажмите 'В начало', чтобы начать заново.")

@dp.message_handler(lambda message: message.text == "Рандомный вопрос")
async def random_question(message: types.Message):
    random_questions = sheet.col_values(2)
    if random_questions:
        await message.answer(random.choice(random_questions))
    else:
        await message.answer("Список рандомных вопросов пуст.")

@dp.message_handler(lambda message: message.text == "В начало")
async def reset_progress(message: types.Message):
    user_state[message.chat.id] = 0
    await message.answer("Начинаем сначала.")