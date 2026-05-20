import asyncio
import json
import os
import statistics
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import websockets
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ==========================================
# TOKEN
# ==========================================
BOT_TOKEN = "8701511595:AAFhcipS4PB4pa8ygEqwFcCJiTwHFJ9-mMU"

# ==========================================
# PORT FOR RENDER
# ==========================================
PORT = int(os.environ.get("PORT", 10000))

# ==========================================
# SIMPLE WEB SERVER
# ==========================================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"BOT IS WORKING")

def run_web():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# ==========================================
# TELEGRAM
# ==========================================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# WEBSOCKET
# ==========================================
WS_URL = "wss://ws3.gamecontent.io/"

# ==========================================
# DATA
# ==========================================
last_drops = []
site_state = "UNKNOWN"

# ==========================================
# MENU
# ==========================================
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 AI Анализ")],
        [KeyboardButton(text="🎯 Лучшие кейсы")],
        [KeyboardButton(text="⚡ AI Апгрейд")],
        [KeyboardButton(text="🧠 AI Риск")]
    ],
    resize_keyboard=True
)

# ==========================================
# AI
# ==========================================
def detect_site_state():

    global site_state

    if len(last_drops) < 20:
        return "Недостаточно данных"

    expensive = 0
    cheap = 0

    for drop in last_drops[-20:]:

        price = drop.get("price", 0)

        if price >= 100:
            expensive += 1
        else:
            cheap += 1

    if expensive > cheap:
        site_state = "СЕЙЧАС ВЫДАЕТ"
    else:
        site_state = "СЕЙЧАС СЛИВАЕТ"

    return site_state

def ai_score():

    if len(last_drops) < 10:
        return 50

    values = [x.get("price", 0) for x in last_drops[-20:]]

    avg = statistics.mean(values)

    if avg > 100:
        return 90

    if avg > 50:
        return 75

    if avg > 20:
        return 60

    return 35

def get_best_cases(balance):

    balance = float(balance)

    if balance < 5:
        return [
            "Starter Case",
            "Cheap Knife",
            "Budget Case"
        ]

    if balance < 20:
        return [
            "Knife Fever",
            "Red Boost",
            "Classified"
        ]

    if balance < 100:
        return [
            "Premium Knife",
            "Dragon Case",
            "High Roller"
        ]

    return [
        "Elite Dragon",
        "Titanium",
        "Legendary"
    ]

def ai_upgrade(balance):

    balance = float(balance)

    state = detect_site_state()

    if state == "СЕЙЧАС СЛИВАЕТ":
        return "AI советует НЕ делать апгрейд"

    if balance < 10:
        return "AI советует 20% upgrade"

    if balance < 50:
        return "AI советует 30% upgrade"

    return "AI советует 40% upgrade"

# ==========================================
# WEBSOCKET
# ==========================================
async def websocket_listener():

    global last_drops

    while True:

        try:

            async with websockets.connect(WS_URL) as ws:

                print("CONNECTED TO WS")

                while True:

                    msg = await ws.recv()

                    try:

                        data = json.loads(msg)

                        if isinstance(data, dict):

                            last_drops.append(data)

                            if len(last_drops) > 200:
                                last_drops = last_drops[-200:]

                    except:
                        pass

        except Exception as e:

            print("WS ERROR:", e)

            await asyncio.sleep(5)

# ==========================================
# START
# ==========================================
@dp.message(Command("start"))
async def start(message: types.Message):

    text = (
        "🧠 AI CASE BOT PRO V2\n\n"
        "Функции:\n"
        "• AI анализ сайта\n"
        "• AI риск движок\n"
        "• Лучшие кейсы\n"
        "• AI апгрейды\n"
    )

    await message.answer(text, reply_markup=menu)

# ==========================================
# ANALYSIS
# ==========================================
@dp.message(lambda message: message.text == "📊 AI Анализ")
async def analysis(message: types.Message):

    state = detect_site_state()
    score = ai_score()

    text = (
        f"📊 AI Анализ\n\n"
        f"Состояние сайта: {state}\n"
        f"AI SCORE: {score}/100\n"
        f"Дропов: {len(last_drops)}"
    )

    await message.answer(text)

# ==========================================
# BEST CASES
# ==========================================
@dp.message(lambda message: message.text == "🎯 Лучшие кейсы")
async def best_cases(message: types.Message):

    await message.answer("Напиши баланс")

# ==========================================
# BALANCE
# ==========================================
@dp.message(lambda message: message.text.replace('.', '').isdigit())
async def budget(message: types.Message):

    balance = float(message.text)

    cases = get_best_cases(balance)

    upgrade = ai_upgrade(balance)

    text = f"💰 Баланс: ${balance}\n\n"

    text += "🎯 Лучшие кейсы:\n"

    for case in cases:
        text += f"• {case}\n"

    text += f"\n⚡ {upgrade}"

    await message.answer(text)

# ==========================================
# RISK
# ==========================================
@dp.message(lambda message: message.text == "🧠 AI Риск")
async def risk(message: types.Message):

    state = detect_site_state()

    if state == "СЕЙЧАС СЛИВАЕТ":
        text = "🚨 AI считает что сайт сейчас сливает"
    else:
        text = "✅ AI считает что сайт сейчас выдает"

    await message.answer(text)

# ==========================================
# UPGRADE
# ==========================================
@dp.message(lambda message: message.text == "⚡ AI Апгрейд")
async def upgrade(message: types.Message):

    await message.answer(
        "Напиши баланс и AI рассчитает upgrade"
    )

# ==========================================
# MAIN
# ==========================================
async def main():

    await asyncio.gather(
        websocket_listener(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
