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

Ти не друг клієнта.
Ти не ведеш особистих бесід.
Ти не жартуєш.
Ти не використовуєш емодзі.

Ти представляєш студію розробки сайтів PIXORA.

Послуги:

* Landing Page
* Корпоративні сайти
* Сайти послуг
* Сайти-візитки
* Редизайн сайтів
* Модернізація сайтів

Правила:

1. Завжди відповідай мовою клієнта.
2. Відповідай коротко.
3. Максимум 3 речення.
4. Не вигадуй ціни.
5. Не вигадуй терміни.
6. Не став нових питань.
7. Не змінюй логіку брифу.
8. Якщо клієнт питає про вартість — поясни що розрахунок залежить від обсягу робіт.
9. Якщо клієнт питає про терміни — поясни що терміни залежать від складності проєкту.
10. Якщо клієнт питає про процес — коротко поясни:
    аналіз → структура → дизайн → розробка → тестування → запуск.
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

QUESTIONS = {
"ru": {
"business": "Расскажите кратко, чем занимается ваш бизнес.",
"goal": "Какая основная задача будущего сайта?",
"audience": "Кто является вашим основным клиентом?",
"examples": "Есть ли сайты, которые вам нравятся? Если есть — отправьте ссылки.",
"timeline": "Когда планируете запуск проекта?",
"contact": "Оставьте телефон или Telegram для связи."
},

"uk": {
    "business": "Розкажіть коротко, чим займається ваш бізнес.",
    "goal": "Яка основна задача майбутнього сайту?",
    "audience": "Хто є вашим основним клієнтом?",
    "examples": "Є сайти які вам подобаються? Якщо є — надішліть посилання.",
    "timeline": "Коли плануєте запуск проєкту?",
    "contact": "Залиште телефон або Telegram для зв'язку."
},

"en": {
    "business": "Please briefly describe your business.",
    "goal": "What is the main goal of your future website?",
    "audience": "Who is your target audience?",
    "examples": "Do you have websites you like? Send links if you do.",
    "timeline": "When do you plan to launch the project?",
    "contact": "Please leave your phone number or Telegram."
}

}

user_data = {}

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
    
    if latin_count > max(1, len(text) * 0.5):
        return "en"

    return "ru"

def get_next_step(step):

    current_index = STEPS.index(step)

    if current_index >= len(STEPS) - 1:
        return None
    
    return STEPS[current_index + 1]
    
    def save_answer(state, step, value):
    
        state["answers"][step] = value.strip()

def init_user_state(user_id):

    user_data[user_id] = {
        "lang": "uk",
        "step": "name",
        "answers": {},
        "history": [],
        "lead_sent": False
    }

    return user_data[user_id]

def looks_like_question(text):

    text = text.lower().strip()
    
    if "?" in text:
        return True
    
    starters = [
        "сколько",
        "стоимость",
        "цена",
        "ціна",
        "вартість",
        "как",
        "як",
        "what",
        "when",
        "where",
        "why",
        "price",
        "cost"
    ]
    
    return any(
        text.startswith(item)
        for item in starters
    )

async def ask_gpt(state, message):

    try:
    
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]
    
        messages.extend(
            state["history"][-10:]
        )
    
        messages.append(
            {
                "role": "user",
                "content": message
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
                "content": message
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
    
        print(f"GPT ERROR: {e}")
        return None

async def send_lead(update, context, user_id):

    state = user_data[user_id]
    data = state["answers"]
    
    username = (
        f"@{update.effective_user.username}"
        if update.effective_user.username
        else "не указан"
    )
    
    lead_text = (
        "🔥 PIXORA NEW LEAD\n\n"
        f"Имя:\n{data.get('name', '-')}\n\n"
        f"Бизнес:\n{data.get('business', '-')}\n\n"
        f"Цель:\n{data.get('goal', '-')}\n\n"
        f"Аудитория:\n{data.get('audience', '-')}\n\n"
        f"Примеры:\n{data.get('examples', '-')}\n\n"
        f"Сроки:\n{data.get('timeline', '-')}\n\n"
        f"Контакт:\n{data.get('contact', '-')}\n\n"
        f"Telegram Username:\n{username}\n\n"
        f"Telegram ID:\n{update.effective_user.id}"
    )
    
    await context.bot.send_message(
        chat_id=LEAD_CHAT_ID,
        text=lead_text
    )

def get_finish_message(lang):

    if lang == "uk":
        return (
            "Дякую за надану інформацію.\n\n"
            "Бриф успішно сформовано та передано спеціалісту PIXORA.\n\n"
            "Після аналізу заявки ми зв'яжемося з вами."
        )
    
    if lang == "en":
        return (
            "Thank you for the information.\n\n"
            "Your brief has been successfully submitted.\n\n"
            "A PIXORA specialist will contact you after reviewing the request."
        )
    
    return (
        "Спасибо за предоставленную информацию.\n\n"
        "Бриф успешно сформирован и передан специалисту PIXORA.\n\n"
        "После анализа заявки мы свяжемся с вами."
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
            user_id
        )
    
    else:
    
        state = user_data[user_id]
    
    if state["step"] == "name":
    
        state["lang"] = detect_language(
            text
        )
    
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
    
        next_step = get_next_step(
            current_step
        )
        
        if not next_step:
            return
        
        state["step"] = next_step
    
        reply = None

    if current_step == "business":
    
        reply = await ask_gpt(
                state,
                f"Клієнт написав про свій бізнес: {text}. "
                f"Коротко підтвердь отримання інформації."
            )    
    
    elif current_step == "goal":
    
        reply = await ask_gpt(
            state,
            f"Клієнт описав ціль сайту: {text}. "
            f"Коротко підтвердь отримання інформації."
        )
    
    elif current_step == "audience":
    
        reply = await ask_gpt(
            state,
            f"Клієнт описав аудиторію: {text}. "
            f"Коротко підтвердь отримання інформації."
        )
    
    elif current_step == "examples":
    
        reply = await ask_gpt(
            state,
            f"Клієнт надав приклади сайтів: {text}. "
            f"Коротко підтвердь отримання інформації."
        )
    
    elif current_step == "timeline":
    
        reply = await ask_gpt(
            state,
            f"Клієнт повідомив строки запуску: {text}. "
            f"Коротко підтвердь отримання інформації."
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

    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN not found"
        )
    
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not found"
        )
    
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )
    
    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat
        )
    )
    
    print(
        "PIXORA AI Manager started"
    )
    
    application.run_polling(
        drop_pending_updates=True
    )

    if __name__ == "__main__":
        main()


    return None
