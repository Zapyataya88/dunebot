import logging
import asyncio
import os
import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==== НАСТРОЙКИ ====
TOKEN = "ВАШ_ТОКЕН"
CHAT_ID = -100xxxxxxxxxx
THREAD_ID = 123
DATA_FILE = "loot_data.json"

# ==== Загрузка и сохранение данных ====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

loot_data = load_data()

# ==== Команды ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(sector, callback_data=sector)] for sector in loot_data.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(
        "📘 Инструкция:\n🕐 Введи время в формате: `/lut G3 13:00`\n🔘 Используй кнопку, чтобы посмотреть оставшееся время",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loot_data.clear()
    save_data(loot_data)
    await update.message.reply_text("✅ Все сектора были очищены.")

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith("/lut"):
        parts = update.message.text.split()
        if len(parts) == 3:
            sector, time_str = parts[1], parts[2]
            try:
                r1 = datetime.strptime(time_str, "%H:%M")
                r2 = r1 + timedelta(minutes=90)
                loot_data[sector] = r1.strftime("%H:%M")
                save_data(loot_data)
                await update.message.reply_text(f"📍 Сектор {sector} сохранён: {r1.strftime('%H:%M')} - {r2.strftime('%H:%M')}")
            except:
                await update.message.reply_text("❌ Неверный формат времени. Пример: `/lut G3 13:00`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Используй: `/lut <сектор> <время>`", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sector = query.data
    if sector in loot_data:
        try:
            r1 = datetime.strptime(loot_data[sector], "%H:%M")
            r2 = r1 + timedelta(minutes=90)
            await context.bot.send_message(
                chat_id=CHAT_ID,
                message_thread_id=THREAD_ID,
                text=f"⚠️⚡ Скоро респ в секторе {sector}!\n🕒 Время: с {r1.strftime('%H:%M')} до {r2.strftime('%H:%M')}"
            )
        except Exception as e:
            await query.edit_message_text(f"⛔ Ошибка при разборе времени: {str(e)}")
    else:
        await query.edit_message_text("❌ Нет сохранённых секторов.")

# ==== Основной запуск ====
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/lut"), handle_input))
    app.add_handler(CallbackQueryHandler(button_handler))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())























































