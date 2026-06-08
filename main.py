import os
from openai import OpenAI

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LEAD_CHAT_ID = 499657192

client = OpenAI(
    api_key=OPENAI_API_KEY
)

# =========================
# GPT PROMPT
# =========================

SYSTEM_PROMPT = """
You are a sales assistant for PIXORA.

IMPORTANT RULES:

You do NOT control the sales funnel.

You do NOT collect project information.

You do NOT ask new questions.

You only answer side questions.

Services:

- Landing Pages
- Business Websites
- Online Stores
- Blogs
- Website Redesign
- Website Support
- Logo Design
- Basic SEO

Keep answers short.

Maximum 3 sentences.

Answer in the same language as the client.

If asked about pricing:
Explain that the final price depends on project scope and functionality.

If asked about timelines:
Explain that timelines depend on project complexity.

Never start a conversation.

Never continue chatting.

Only answer the question.
"""

# =========================
# STORAGE
# =========================

user_data = {}

STEPS = [
    "name",
    "niche",
    "site_type",
    "logo",
    "content",
    "examples",
    "budget",
    "contact"
]

QUESTIONS = {

    "ru": {
        "niche": "Чем занимается ваш бизнес?",
        "site_type": "Какой сайт вас интересует?\n\n• Лендинг\n• Корпоративный сайт\n• Интернет-магазин\n• Блог\n• Другое",
        "logo": "У вас уже есть логотип?",
        "content": "Тексты и фотографии уже готовы?",
        "examples": "Есть примеры сайтов которые вам нравятся?",
        "budget": "На какой бюджет ориентируетесь?",
        "contact": "Оставьте телефон или Telegram для связи."
    },

    "uk": {
        "niche": "Чим займається ваш бізнес?",
        "site_type": "Який сайт вас цікавить?\n\n• Лендінг\n• Корпоративний сайт\n• Інтернет-магазин\n• Блог\n• Інше",
        "logo": "У вас вже є логотип?",
        "content": "Тексти та фото вже готові?",
        "examples": "Є приклади сайтів які вам подобаються?",
        "budget": "Який бюджет плануєте?",
        "contact": "Залиште номер телефону або Telegram."
    },

    "en": {
        "niche": "What does your business do?",
        "site_type": "What type of website do you need?\n\n• Landing Page\n• Corporate Website\n• Online Store\n• Blog\n• Other",
        "logo": "Do you already have a logo?",
        "content": "Do you already have texts and images?",
        "examples": "Do you have examples of websites you like?",
        "budget": "What budget are you considering?",
        "contact": "Leave your phone number or Telegram."
    }
}


# =========================
# LANGUAGE DETECTION
# =========================

def detect_language(text):

    text = text.lower()

    if any(ch in text for ch in "іїєґ"):
        return "uk"

    if any(ch in text for ch in "ыэъ"):
        return "ru"

    latin = sum(c.isascii() and c.isalpha() for c in text)

    if latin > len(text) * 0.6:
        return "en"

    return "ru"


# =========================
# GPT SIDE QUESTIONS
# =========================

async def ask_gpt(question):

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print("GPT ERROR")
        print(str(e))

        return None


# =========================
# QUESTION CHECK
# =========================

def looks_like_question(text):

    text = text.lower()

    triggers = [
        "?",
        "сколько",
        "ціна",
        "цены",
        "стоимость",
        "вартість",
        "price",
        "timeline",
        "срок",
        "термін",
        "seo",
        "логотип",
        "почему",
        "як",
        "как",
        "what",
        "when",
        "where"
    ]

    return any(t in text for t in triggers)


# =========================
# SEND LEAD
# =========================

async def send_lead(update, context, user_id):

    data = user_data[user_id]["answers"]

    username = update.effective_user.username

    username_text = (
        f"@{username}"
        if username
        else "Не вказано"
    )

    lead_text = (
        "🔥 НОВА ЗАЯВКА PIXORA\n\n"
        f"Ім'я: {data.get('name','')}\n\n"
        f"Ніша: {data.get('niche','')}\n\n"
        f"Тип сайту: {data.get('site_type','')}\n\n"
        f"Логотип: {data.get('logo','')}\n\n"
        f"Контент: {data.get('content','')}\n\n"
        f"Приклади: {data.get('examples','')}\n\n"
        f"Бюджет: {data.get('budget','')}\n\n"
        f"Контакт: {data.get('contact','')}\n\n"
        f"Username: {username_text}\n"
        f"Telegram ID: {update.effective_user.id}"
    )

    await context.bot.send_message(
        chat_id=LEAD_CHAT_ID,
        text=lead_text
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    user_data[user_id] = {
        "lang": "uk",
        "step": "name",
        "answers": {},
        "lead_sent": False
    }

    await update.message.reply_text(
        "Вітаю 👋\n\n"
        "Мене звати Андрій.\n"
        "Я менеджер компанії PIXORA.\n\n"
        "Як до вас звертатись?"
    )


# =========================
# CHAT
# =========================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    text = (update.message.text or "").strip()

    if user_id not in user_data:

        user_data[user_id] = {
            "lang": detect_language(text),
            "step": "name",
            "answers": {},
            "lead_sent": False
        }

    state = user_data[user_id]

    # Побочный вопрос

    if (
        state["step"] != "name"
        and looks_like_question(text)
    ):

        answer = await ask_gpt(text)

        if answer:

            await update.message.reply_text(answer)

        current_step = state["step"]

        await update.message.reply_text(
            QUESTIONS[state["lang"]][current_step]
        )

        return

    # Имя

    if state["step"] == "name":

        state["lang"] = detect_language(text)

        state["answers"]["name"] = text

        state["step"] = "niche"

        await update.message.reply_text(
            QUESTIONS[state["lang"]]["niche"]
        )

        return

    # Остальные шаги

    current_step = state["step"]

    state["answers"][current_step] = text

    current_index = STEPS.index(current_step)

    # Последний шаг

    if current_step == "contact":

        if not state["lead_sent"]:

            state["lead_sent"] = True

            await send_lead(
                update,
                context,
                user_id
            )

        lang = state["lang"]

        if lang == "ru":

            msg = (
                "Спасибо за информацию.\n\n"
                "Заявка успешно сформирована и передана специалисту PIXORA.\n\n"
                "Сергей свяжется с вами в ближайшее время."
            )

        elif lang == "en":

            msg = (
                "Thank you.\n\n"
                "Your request has been sent to PIXORA.\n\n"
                "Serhii will contact you shortly."
            )

        else:

            msg = (
                "Дякуємо за інформацію.\n\n"
                "Заявку успішно передано спеціалісту PIXORA.\n\n"
                "Сергій зв'яжеться з вами найближчим часом."
            )

        await update.message.reply_text(msg)

        return

    next_step = STEPS[current_index + 1]

    state["step"] = next_step

    await update.message.reply_text(
        QUESTIONS[state["lang"]][next_step]
    )


# =========================
# MAIN
# =========================

def main():

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat
        )
    )

    print("PIXORA AI Manager started")

    app.run_polling()


if __name__ == "__main__":
    main()
