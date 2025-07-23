import logging
import asyncio
import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==== НАСТРОЙКИ ====
TOKEN = "7899510124:AAEMHtZUNKKTw17iURSw6uuv94mWjJL3Ypw"
CHAT_ID = -1002741686305
THREAD_ID = 286
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

# ==== Кнопки ====
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Ввести время", callback_data="input_time")],
        [InlineKeyboardButton("📋 Показать список", callback_data="show_list")],
        [InlineKeyboardButton("❌ Удалить сектор", callback_data="delete_sector")],
        [InlineKeyboardButton("♻️ Сброс", callback_data="reset_data")],
        [InlineKeyboardButton("📘 Помощь / Инструкция", callback_data="help")]
    ])

def get_sector_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(sector, callback_data=f"sector_{sector}")]
        for sector in loot_data.keys()
    ])

def format_loot_list():
    if not loot_data:
        return "❌ Нет сохранённых секторов."
    text = "📋 Список ящиков:\n"
    for s, t in loot_data.items():
        pickup = datetime.strptime(t, "%H:%M")
        r1 = (pickup + timedelta(minutes=45)).strftime("%H:%M")
        r2 = (pickup + timedelta(minutes=90)).strftime("%H:%M")
        text += f"📦 {s}: ⏫ {t} ➜ ⏳ {r1} до {r2}\n"
    return text

# ==== Хендлеры ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери действие:", reply_markup=get_main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "input_time":
        await query.message.reply_text("Выбери сектор:", reply_markup=get_sector_menu())

    elif query.data.startswith("sector_"):
        sector = query.data.split("_")[1]
        context.user_data["awaiting_time"] = sector
        await query.message.reply_text(f"🕓 Введи новое время для сектора {sector} (например: 14:00):")

    elif query.data == "show_list":
        await query.message.reply_text(format_loot_list(), reply_markup=get_main_menu())

    elif query.data == "delete_sector":
        if loot_data:
            context.user_data["deleting"] = True
            await query.message.reply_text("Выбери сектор для удаления:", reply_markup=get_sector_menu())
        else:
            await query.message.reply_text("❌ Нет сохранённых секторов.", reply_markup=get_main_menu())

    elif query.data == "reset_data":
        loot_data.clear()
        save_data(loot_data)
        await query.message.reply_text("♻️ Все сектора сброшены.", reply_markup=get_main_menu())

    elif query.data == "help":
        help_text = (
            "📘 Инструкция:\n"
            "• Введи время в формате ЧЧ:ММ (например: 14:25)\n"
            "• В начале недели добавь сектора вручную через /loot H8 14:00\n"
            "• Затем бот покажет кнопки только для них\n"
            "• Кнопка 'Сброс' удалит все сектора для новой недели"
        )
        await query.message.reply_text(help_text, reply_markup=get_main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.message_thread_id != THREAD_ID:
        return

    if context.user_data.get("awaiting_time"):
        sector = context.user_data.pop("awaiting_time")
        try:
            time_str = update.message.text.strip()
            pickup = datetime.strptime(time_str, "%H:%M")
            loot_data[sector] = pickup.strftime("%H:%M")
            save_data(loot_data)
            r1 = (pickup + timedelta(minutes=45)).strftime("%H:%M")
            r2 = (pickup + timedelta(minutes=90)).strftime("%H:%M")
            await update.message.reply_text(
                f"✅ Обновлено время для {sector}!\n⏫ {pickup.strftime('%H:%M')} ➜ ⏳ {r1} до {r2}"
            )
        except:
            await update.message.reply_text("⚠️ Неверный формат времени. Используй HH:MM")

        await update.message.reply_text(format_loot_list(), reply_markup=get_main_menu())

    elif context.user_data.get("deleting"):
        context.user_data.pop("deleting")
        sector = update.message.text.strip().upper()
        if sector in loot_data:
            del loot_data[sector]
            save_data(loot_data)
            await update.message.reply_text(f"🗑️ Сектор {sector} удалён.")
        else:
            await update.message.reply_text(f"❌ Сектор {sector} не найден.")
        await update.message.reply_text(format_loot_list(), reply_markup=get_main_menu())

    elif update.message.text.startswith("/loot"):
        try:
            _, sector, time_str = update.message.text.strip().split()
            pickup = datetime.strptime(time_str, "%H:%M")
            loot_data[sector.upper()] = pickup.strftime("%H:%M")
            save_data(loot_data)
            await update.message.reply_text(f"✅ Добавлен сектор {sector.upper()} с временем {time_str}")
        except:
            await update.message.reply_text("❌ Формат: /loot H8 14:00")

# ==== Уведомления ====
async def reminder_loop(app):
    while True:
        now = datetime.now().strftime("%H:%M")
        for s, t in loot_data.items():
            if now == (datetime.strptime(t, "%H:%M") + timedelta(minutes=35)).strftime("%H:%M"):
                r1 = (datetime.strptime(t, "%H:%M") + timedelta(minutes=45)).strftime("%H:%M")
                r2 = (datetime.strptime(t, "%H:%M") + timedelta(minutes=90)).strftime("%H:%M")
                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    message_thread_id=THREAD_ID,
                    text=f"⚡ Скоро респ в секторе {s}!\n⏰ Время: с {r1} до {r2}"
                )
        await asyncio.sleep(60)

# ==== Запуск ====
async def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("loot", handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    asyncio.create_task(reminder_loop(app))
    print("✅ Бот запущен...")
    await app.run_polling()

# Для Replit без run_until_complete
import nest_asyncio
nest_asyncio.apply()
asyncio.get_event_loop().run_until_complete(main())




















































