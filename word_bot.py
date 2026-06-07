import logging
import requests
from collections import Counter
import re
from datetime import datetime, time
import pytz
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8976114188:AAHw8JHit9lxEBkFPHKX6Wo46hiXaDWi1qs"  # توکن بات جدید از BotFather
CHAT_ID = "200322275"
NEWS_API_KEY = "fdcb19e4121e495c82c7f75a90424d84"

IRAN_TZ = pytz.timezone("Asia/Tehran")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# کلمات بی‌معنی که باید فیلتر بشن
STOPWORDS = set([
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","being","have","has","had","do","does",
    "did","will","would","could","should","may","might","shall","can","need",
    "that","this","these","those","it","its","he","she","they","we","you","i",
    "his","her","their","our","your","my","by","from","up","about","into",
    "through","during","before","after","above","below","between","out","off",
    "over","under","again","then","once","as","not","no","so","if","than",
    "too","very","just","also","more","most","other","some","such","new","said"
])

def get_top_word():
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"language": "en", "pageSize": 100, "apiKey": NEWS_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        all_text = ""
        for article in data.get("articles", []):
            if article.get("title"):
                all_text += " " + article["title"]
            if article.get("description"):
                all_text += " " + article["description"]

        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text.lower())
        filtered = [w for w in words if w not in STOPWORDS]
        counter = Counter(filtered)
        top_words = counter.most_common(20)

        # انتخاب یه کلمه از ۵ تای اول که معنی داشته باشه
        for word, count in top_words:
            meaning = get_meaning(word)
            if meaning:
                return {"word": word.capitalize(), "count": count, "meaning": meaning}

    except Exception as e:
        logger.error(f"خطا: {e}")
    return None

def get_meaning(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            meanings = data[0].get("meanings", [])
            if meanings:
                definitions = meanings[0].get("definitions", [])
                if definitions:
                    definition = definitions[0].get("definition", "")
                    example = definitions[0].get("example", "")
                    part = meanings[0].get("partOfSpeech", "")
                    return {"definition": definition, "example": example, "part": part}
    except:
        pass
    return None

def format_word_message(data):
    w = data["word"]
    count = data["count"]
    m = data["meaning"]
    msg = (
        f"📰 *کلمه پرتکرار امروز رسانه‌های جهان*\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🔤 *{w}*  _(_{m['part']}_)_\n"
        f"🔁 تکرار در اخبار امروز: `{count}` بار\n\n"
        f"📖 معنی: {m['definition']}\n"
    )
    if m['example']:
        msg += f"💬 مثال: _{m['example']}_"
    return msg

async def cmd_start(update, context):
    await update.message.reply_text(
        "سلام! 👋\n"
        "من هر روز ساعت ۱۲ ظهر پرتکرارترین کلمه انگلیسی رسانه‌های جهان رو بهت میگم 📰\n\n"
        "برای دیدن کلمه امروز بنویس /word"
    )

async def cmd_word(update, context):
    await update.message.reply_text("⏳ در حال بررسی اخبار جهان...")
    data = get_top_word()
    if data:
        await update.message.reply_text(format_word_message(data), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ خطا در دریافت اطلاعات.")

async def send_daily_word(context: ContextTypes.DEFAULT_TYPE):
    data = get_top_word()
    if data:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=format_word_message(data),
            parse_mode="Markdown"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("word", cmd_word))

    send_time = time(hour=8, minute=30, second=0, tzinfo=IRAN_TZ)  # ۱۲ ظهر ایران
    app.job_queue.run_daily(send_daily_word, time=send_time)

    logger.info("بات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
