import os
import random
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
Ти менеджер студії PIXORA.

PIXORA займається створенням лендингів під ключ.

Клієнт вже прийшов із сайту PIXORA.

Клієнт вже зацікавлений у створенні лендингу.

НЕ потрібно:

- вітатися повторно
- знайомитися повторно
- питати "чим можу допомогти"
- питати "який сайт вас цікавить"
- вести дружню бесіду
- розтягувати діалог

Твоє завдання:

Лише коротко відповідати на додаткові питання клієнта під час заповнення брифу.

Максимум 2-3 речення.

Якщо клієнт питає про ціну:
Поясни що вартість залежить від складності проєкту та буде розрахована після короткого брифу.

Якщо клієнт питає про терміни:
Поясни що терміни залежать від обсягу робіт та зазвичай складають від кількох днів до кількох тижнів.

НІКОЛИ не використовуй:

- Чим можу допомогти?
- Як я можу допомогти?
- Радий знайомству
- Розкажіть детальніше
- Що вас цікавить?
- Як справи?

НІКОЛИ не керуй воронкою.

НІКОЛИ не став нових питань.

Ти лише відповідаєш на додаткові питання клієнта.
"""

# =========================
# STORAGE
# =========================

user_data = {}
TRANSITIONS = {

    "ru": [
        "Отлично, {name}.",
        "Понял, {name}.",
        "Спасибо.",
        "Хорошо.",
        "Отлично, это понял."
    ],

    "uk": [
        "Чудово, {name}.",
        "Зрозумів, {name}.",
        "Дякую.",
        "Добре.",
        "Чудово, це зрозумів."
    ],

    "en": [
        "Great, {name}.",
        "Got it, {name}.",
        "Thank you.",
        "Sounds good.",
        "Understood."
    ]
}
STEPS = [
    "name",
    "niche",
    "goal",
    "target_audience",
    "examples",
    "timeline",
    "contact"
]

QUESTIONS = {

    "ru": {
        "niche": "Чем занимается ваш бизнес?",

        "goal":
        "Какая главная задача будущего лендинга?\n\n"
        "Например:\n"
        "• Получение заявок\n"
        "• Запись клиентов\n"
        "• Продажа услуг\n"
        "• Продажа товаров",

        "target_audience":
        "Кто ваш основной клиент?\n\n"
        "Опишите коротко целевую аудиторию.",

        "examples":
        "Есть примеры сайтов которые вам нравятся?\n\n"
        "Если есть — отправьте ссылки.",

        "timeline":
        "Когда планируете запуск проекта?\n\n"
        "• Срочно\n"
        "• В течение недели\n"
        "• В течение месяца\n"
        "• Пока изучаю варианты",

        "contact":
        "Оставьте телефон или Telegram для связи."
    },

    "uk": {
        "niche": "Чим займається ваш бізнес?",

        "goal":
        "Яка головна задача майбутнього лендингу?\n\n"
        "Наприклад:\n"
        "• Отримання заявок\n"
        "• Запис клієнтів\n"
        "• Продаж послуг\n"
        "• Продаж товарів",

        "target_audience":
        "Хто ваш основний клієнт?\n\n"
        "Опишіть коротко вашу цільову аудиторію.",

        "examples":
        "Є приклади сайтів які вам подобаються?\n\n"
        "Якщо є — надішліть посилання.",

        "timeline":
        "Коли плануєте запуск проєкту?\n\n"
        "• Терміново\n"
        "• Протягом тижня\n"
        "• Протягом місяця\n"
        "• Поки вивчаю варіанти",

        "contact":
        "Залиште номер телефону або Telegram для зв'язку."
    },

    "en": {
        "niche": "What does your business do?",

        "goal":
        "What is the main goal of the landing page?",

        "target_audience":
        "Who is your target audience?",

        "examples":
        "Do you have examples of websites you like?",

        "timeline":
        "When do you plan to launch the project?",

        "contact":
        "Please leave your phone number or Telegram."
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
def transition(lang, name):

    phrase = random.choice(
        TRANSITIONS[lang]
    )

    return phrase.format(
        name=name
    )

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
        f"Задача лендингу: {data.get('goal','')}\n\n"
        f"Цільова аудиторія: {data.get('target_audience','')}\n\n"
        f"Приклади: {data.get('examples','')}\n\n"
        f"Терміни запуску: {data.get('timeline','')}\n\n"
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
                "Дякуємо за інформацію.\n\n"
                "Ваш бриф успішно сформовано та передано Сергію.\n\n"
                "Сергій — спеціаліст PIXORA, який буде займатися вашим проєктом та підготує попередню оцінку вартості й термінів.\n\n"
                "Найближчим часом він зв'яжеться з вами для обговорення деталей."
            )

        else:

            msg = (
                "Thank you for the information.\n\n"
                "Your brief has been successfully submitted and assigned to Serhii.\n\n"
                "Serhii is the PIXORA specialist who will be responsible for your project and prepare a preliminary estimate of cost and timeline.\n\n"
                "He will contact you shortly to discuss the details."
            )

        await update.message.reply_text(msg)

        return

            next_step = STEPS[current_index + 1]
        
        state["step"] = next_step
        
        name = state["answers"].get(
            "name",
            ""
        )
        
        await update.message.reply_text(
            f"{transition(state['lang'], name)}\n\n"
            f"{QUESTIONS[state['lang']][next_step]}"
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
