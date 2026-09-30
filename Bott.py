import json
import os
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "salom"

FILE = "hisob.json"


def load_data():
    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["➕ Berildi", "➖ Qaytarildi"],
        ["📊 Hisobot", "📜 Tarix"],
        ["🗑 Tozalash"]
    ]

    await update.message.reply_text(
        "Salom! 👋\n\n"
        "Idishlar hisob-kitob botiga xush kelibsiz.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    # HISOBOT
    if text == "📊 Hisobot":

        if not data:
            await update.message.reply_text("Hozircha hisob yo‘q.")
            return

        message = "📊 HISOBOT\n\n"
        total = 0

        for name, info in data.items():

            # Eski formatdagi ma'lumotni ham qo'llab-quvvatlaydi
            if isinstance(info, int):
                count = info
            else:
                count = info.get("count", 0)

            message += f"👤 {name} — {count} ta\n"
            total += count

        message += f"\n📦 JAMI: {total} ta"

        await update.message.reply_text(message)
        return


    # TARIX
    if text == "📜 Tarix":

        await update.message.reply_text(
            "Kimning tarixini ko‘rmoqchisiz?\n\n"
            "Masalan:\n"
            "Ali"
        )

        context.user_data["history"] = True
        return


    # TOZALASH
    if text == "🗑 Tozalash":

        data.clear()
        save_data(data)

        await update.message.reply_text(
            "🗑 Barcha hisoblar va tarixlar tozalandi."
        )
        return


    # BERILDI
    if text == "➕ Berildi":

        context.user_data["action"] = "add"

        await update.message.reply_text(
            "Kimga va nechta berilganini yozing.\n\n"
            "Masalan:\n"
            "Ali 20"
        )
        return


    # QAYTARILDI
    if text == "➖ Qaytarildi":

        context.user_data["action"] = "remove"

        await update.message.reply_text(
            "Kimdan va nechta qaytarilganini yozing.\n\n"
            "Masalan:\n"
            "Ali 5"
        )
        return


    # TARIXNI KO'RISH
    if context.user_data.get("history"):

        name = text

        if name not in data:
            await update.message.reply_text(
                f"❗ {name} bo‘yicha hisob topilmadi."
            )
            context.user_data["history"] = False
            return

        info = data[name]

        if isinstance(info, int):
            await update.message.reply_text(
                f"👤 {name}\n\n"
                f"📦 Qoldiq: {info} ta\n\n"
                "Bu eski hisob, unda tarix saqlanmagan."
            )
            context.user_data["history"] = False
            return

        history = info.get("history", [])
        count = info.get("count", 0)

        message = f"📜 {name} TARIXI\n\n"

        if not history:
            message += "Hozircha tarix yo‘q."
        else:
            for item in history:
                message += (
                    f"{item['date']} — "
                    f"{item['action']} {item['count']} ta\n"
                )

            message += f"\n📦 QOLDIQ: {count} ta"

        await update.message.reply_text(message)

        context.user_data["history"] = False
        return


    # ISM + SON
    parts = text.split()

    if len(parts) != 2:

        await update.message.reply_text(
            "❗ To‘g‘ri formatda yozing.\n\n"
            "Masalan: Ali 20"
        )
        return


    name = parts[0]

    try:
        count = int(parts[1])
    except:

        await update.message.reply_text(
            "❗ Sonni to‘g‘ri kiriting.\n\n"
            "Masalan: Ali 20"
        )
        return


    if count <= 0:

        await update.message.reply_text(
            "❗ Son 0 dan katta bo‘lishi kerak."
        )
        return


    action = context.user_data.get("action")


    # BERILDI
    if action == "add":

        if name not in data:

            data[name] = {
                "count": 0,
                "history": []
            }

        # Eski format bo'lsa
        if isinstance(data[name], int):

            old_count = data[name]

            data[name] = {
                "count": old_count,
                "history": []
            }

        data[name]["count"] += count

        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        data[name]["history"].append({
            "date": now,
            "action": "➕ Berildi",
            "count": count
        })

        save_data(data)

        await update.message.reply_text(
            f"✅ {name} hisobiga {count} ta qo‘shildi.\n"
            f"📦 Jami: {data[name]['count']} ta"
        )

        context.user_data["action"] = None
        return


    # QAYTARILDI
    if action == "remove":

        if name not in data:

            await update.message.reply_text(
                f"❗ {name} bo‘yicha hisob topilmadi."
            )
            return

        if isinstance(data[name], int):

            data[name] = {
                "count": data[name],
                "history": []
            }

        if data[name]["count"] < count:

            await update.message.reply_text(
                f"❗ {name} hisobida faqat "
                f"{data[name]['count']} ta bor."
            )
            return

        data[name]["count"] -= count

        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        data[name]["history"].append({
            "date": now,
            "action": "➖ Qaytarildi",
            "count": count
        })

        save_data(data)

        await update.message.reply_text(
            f"↩️ {name} hisobidan {count} ta ayirildi.\n"
            f"📦 Qoldiq: {data[name]['count']} ta"
        )

        context.user_data["action"] = None
        return


    await update.message.reply_text(
        "Avval ➕ Berildi yoki ➖ Qaytarildi tugmasini bosing."
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    )
)

print("Bot ishga tushdi...")

app.run_polling()
