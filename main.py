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

SYSTEM_PROMPT = """
Ти професійний менеджер студії PIXORA.

Основна спеціалізація PIXORA:

* створення лендингів
* корпоративних сайтів
* сайтів-візиток
* сайтів послуг
* модернізація існуючих сайтів

Клієнт вже прийшов із сайту PIXORA.

Твоя задача:

1. Допомогти клієнту пройти короткий бриф.
2. Відповідати на додаткові питання клієнта.
3. Пояснювати процес роботи.
4. Виявляти потребу клієнта.
5. Зберігати діловий стиль спілкування.
6. Не вести особистих розмов.
7. Не жартувати.
8. Не переходити на дружній стиль.
9. Не використовувати емодзі.
10. Завжди бути ввічливим та професійним.

Якщо клієнт питає про ціну:
Поясни що вартість залежить від структури сайту, функціоналу та обсягу робіт. Точний розрахунок можливий після заповнення короткого брифу.

Якщо клієнт питає про терміни:
Поясни що терміни залежать від складності проєкту. Більшість лендингів запускаються від кількох днів до кількох тижнів.

Якщо клієнт питає про процес роботи:
Коротко поясни етапи:
аналіз → структура → дизайн → розробка → тестування → запуск.

Відповідай тією мовою, якою пише клієнт.

Відповідай коротко.

Максимум 3 речення.

Не став нових питань.
Не змінюй логіку брифу.
Не вигадуй ціни.
"""

STEPS = [
"name",
"business",
"goal",
"audience",
"examples",
"timeline",
"contact"
]

user_data = {}
QUESTIONS = {
"ru": {
"business": "Расскажите кратко, чем занимается ваш бизнес.",
"goal": "Какая основная задача будущего сайта? Например: заявки, продажи, запись клиентов или презентация услуг.",
"audience": "Кто является вашим основным клиентом?",
"examples": "Есть ли сайты, которые вам нравятся? Если есть — отправьте ссылки.",
"timeline": "Когда планируете запуск проекта?",
"contact": "Оставьте удобный контакт для связи: телефон или Telegram."
},

"uk": {
    "business": "Розкажіть коротко, чим займається ваш бізнес.", 
    "goal": "Яка основна задача майбутнього сайту? Наприклад: заявки, продажі, запис клієнтів або презентація послуг.",
    "audience": "Хто є вашим основним клієнтом?",
    "examples": "Є сайти, які вам подобаються? Якщо є — надішліть посилання.",
    "timeline": "Коли плануєте запуск проєкту?",
    "contact": "Залиште зручний контакт для зв'язку: телефон або Telegram."
},

"en": {
    "business": "Please briefly describe your business.",
    "goal": "What is the main purpose of the future website?",
    "audience": "Who is your primary target audience?",
    "examples": "Do you have any websites you like? If yes, please send links.",
    "timeline": "When do you plan to launch the project?",
    "contact": "Please leave your phone number or Telegram contact."
}

}

def detect_language(text):
    text = text.lower()

    if any(ch in text for ch in "іїєґ"):
        return "uk"
    
    if any(ch in text for ch in "ыэъ"):
        return "ru"
    
    latin_count = sum(
        c.isascii() and c.isalpha()
        for c in text
    )
    
    if len(text) > 0 and latin_count > len(text) * 0.6:
        return "en"
    
    return "ru"

def get_next_step(step):
    current_index = STEPS.index(step)

    if current_index >= len(STEPS) - 1:
        return None
    
    return STEPS[current_index + 1]

async def ask_gpt(state, user_message):

    try:

        history = state.get(
            "history",
            []
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        messages.extend(history[-10:])

        messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=messages
        )

        answer = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        state["history"].append(
            {
                "role": "user",
                "content": user_message
            }
        )

        state["history"].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer

    except Exception as e:

        print(
            f"GPT ERROR: {str(e)}"
        )

        return None

def looks_like_question(text):
    text = text.lower()

    triggers = [
        "?",
        "цена",
        "ціна",
        "стоимость",
        "вартість",
        "сколько",
        "термін",
        "срок",
        "логотип",
        "seo",
        "домен",
        "хостинг",
        "як",
        "как",
        "why",
        "what",
        "when",
        "where",
        "price",
        "cost"
    ]
    
    return any(
        trigger in text
        for trigger in triggers
    )

async def send_lead(update, context, user_id):

    state = user_data[user_id]
    data = state["answers"]

    username = (
        f"@{update.effective_user.username}"
        if update.effective_user.username
        else "Не указан"
    )

    summary = []

    if data.get("business"):
        summary.append(f"Ниша: {data['business']}")

    if data.get("goal"):
        summary.append(f"Цель: {data['goal']}")

    if data.get("audience"):
        summary.append(f"ЦА: {data['audience']}")

    if data.get("timeline"):
        summary.append(f"Сроки: {data['timeline']}")

    brief_summary = "\n".join(summary)

    lead_text = (
        "🔥 НОВЫЙ ЛИД PIXORA\n\n"
        f"Имя:\n{data.get('name', '-')}\n\n"
        f"Бизнес:\n{data.get('business', '-')}\n\n"
        f"Цель сайта:\n{data.get('goal', '-')}\n\n"
        f"Целевая аудитория:\n{data.get('audience', '-')}\n\n"
        f"Примеры сайтов:\n{data.get('examples', '-')}\n\n"
        f"Сроки:\n{data.get('timeline', '-')}\n\n"
        f"Контакт:\n{data.get('contact', '-')}\n\n"
        f"Telegram:\n{username}\n\n"
        f"Telegram ID:\n{update.effective_user.id}\n\n"
        f"КРАТКОЕ РЕЗЮМЕ:\n{brief_summary}"
    )

    await context.bot.send_message(
        chat_id=LEAD_CHAT_ID,
        text=lead_text
    )

def get_finish_message(lang):

    if lang == "uk":
        return (
            "Дякую за інформацію.\n\n"
            "Бриф успішно сформовано та передано спеціалісту PIXORA.\n\n"
            "Після аналізу інформації ми зв'яжемося з вами для обговорення деталей проєкту."
        )
    
    if lang == "en":
        return (
            "Thank you for the information.\n\n"
            "Your brief has been successfully submitted to the PIXORA team.\n\n"
            "After reviewing the information, we will contact you to discuss the project details."
        )
    
        return (
            "Спасибо за информацию.\n\n"
            "Бриф успешно сформирован и передан специалисту PIXORA.\n\n"
            "После анализа информации мы свяжемся с вами для обсуждения деталей проекта."
        )

def get_name_reply(lang, name):

    if lang == "uk":
        return (
            f"Дякую, {name}.\n\n"
            f"{QUESTIONS['uk']['business']}"
        )
    
    if lang == "en":
        return (
            f"Thank you, {name}.\n\n"
            f"{QUESTIONS['en']['business']}"
        )
    
    return (
        f"Спасибо, {name}.\n\n"
        f"{QUESTIONS['ru']['business']}"
    )
async def start(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
        ):
    
        user_id = str(
            update.effective_user.id
        )
        
        user_data[user_id] = {
            "lang": "uk",
            "step": "name",
            "answers": {},
            "history": [],
            "lead_sent": False
        }
    
        await update.message.reply_text(
            "Вітаю.\n\n"
            "Мене звати Андрій.\n"
            "Я менеджер студії PIXORA.\n\n"
            "Як до вас звертатися?"
        )

def init_user_state(
    user_id,
    text
    ):

    user_data[user_id] = {
        "lang": detect_language(text),
        "step": "name",
        "answers": {},
        "history": [],
        "lead_sent": False
    }

    return user_data[user_id]

def save_answer(
    state,
    step,
    value
    ):

    state["answers"][step] = value.strip()

def get_current_question(
    state
    ):
    
    lang = state["lang"]
    
    step = state["step"]

    return QUESTIONS[lang][step]

def is_brief_finished(
    state
    ):

    return (
        state["step"] == "contact"
        and "contact" in state["answers"]
    )

def move_to_next_step(
    state
    ):

    current_step = state["step"]
    
    next_step = get_next_step(
        current_step
    )

    if next_step:
        state["step"] = next_step
    
    return next_step

async def chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
    ):

    user_id = str(
        update.effective_user.id
    )
    
    text = (
        update.message.text or ""
    ).strip()

    if not text:
        return
    
    if user_id not in user_data:
    
        state = init_user_state(
            user_id,
            text
        )
    
    else:
    
        state = user_data[user_id]
    
    if state["step"] == "name":

        state["lang"] = detect_language(text)
    
        save_answer(
            state,
            "name",
            text
        )

        state["step"] = "business"

await update.message.reply_text(
    get_name_reply(
        state["lang"],
        text
    )
)

return
current_step = state["step"] 

    if looks_like_question(text):

        gpt_answer = await ask_gpt(
            state,
            text
        )

    if gpt_answer:

        await update.message.reply_text(
            gpt_answer
        )

    await update.message.reply_text(
        QUESTIONS[
            state["lang"]
        ][current_step]
    )

    return

    save_answer(
        state,
        current_step,
        text
    )

    if current_step == "contact":
    
        if not state["lead_sent"]:
    
            state["lead_sent"] = True
    
        await send_lead(
            update,
            context,
            user_id
        )
    
        await update.message.reply_text(
            get_finish_message(
                state["lang"]
            )
        )

    return

    next_step = move_to_next_step(
        state
    )
    
    if not next_step:
        return

    answer_value = text
    
    if current_step == "business":
    
        prompt = (
            f"Клієнт написав свою нішу: "
            f"{answer_value}\n\n"
            f"Дай коротку професійну відповідь "
            f"одним реченням без нових питань."
        )
    
        reply = await ask_gpt(
            state,
            prompt
        )

    if reply:

        await update.message.reply_text(
            reply
        )

    elif current_step == "goal":
    
        prompt = (
            f"Клієнт описав мету сайту: "
            f"{answer_value}\n\n"
            f"Коротко підтвердь що інформацію "
            f"отримано без нових питань."
        )
    
        reply = await ask_gpt(
            state,
            prompt
        )

    if reply:

        await update.message.reply_text(
            reply
        )

    elif current_step == "audience":
    
        prompt = (
            f"Клієнт описав цільову аудиторію: "
            f"{answer_value}\n\n"
            f"Коротко підтвердь отримання "
            f"інформації."
        )
    
        reply = await ask_gpt(
            state,
            prompt
        )

    if reply:

        await update.message.reply_text(
            reply
        )

    await update.message.reply_text(
        QUESTIONS[
            state["lang"]
        ][next_step]
    )

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

    print(
        "PIXORA AI Manager started"
    )

    app.run_polling()
