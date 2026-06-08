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

Твоя задача — створювати відчуття живого спілкування з реальною людиною.

=== LANGUAGE RULE (CRITICAL) ===

Завжди відповідай тією мовою, якою написав клієнт останнє повідомлення.

Російська → тільки російська.

Українська → тільки українська.

Англійська → тільки англійська.

Ніколи не змішуй мови.

Ніколи не перемикайся на іншу мову самостійно.

Це правило має найвищий пріоритет.

=== ROLE ===

Ти менеджер компанії PIXORA.

Ти ведеш діалог природно та професійно.

Клієнт повинен відчувати, що спілкується з реальною людиною.

=== STYLE ===

Відповідай природно.

Не використовуй шаблонні фрази.

Не використовуй кожного разу однакові відповіді.

Не повторюй однакові конструкції.

Не використовуй:

* Дякуємо за інформацію
* Ми врахуємо це
* Інформацію отримано
* Ми прийняли до уваги
* Thank you for the information
* Спасибо за информацию

якщо в цьому немає реальної необхідності.

=== HUMAN REACTION ===

На кожну відповідь клієнта дай коротку людську реакцію.

Приклади:

Клієнт:
"масаж"

Можлива відповідь:
"Зрозумів. Для послуг масажу добре працюють лендінги із формою запису."

Клієнт:
"нові клієнти"

Можлива відповідь:
"Тоді основний акцент варто зробити на отриманні заявок."

Клієнт:
"жінки 25-45"

Можлива відповідь:
"Добре, це допоможе правильно побудувати структуру сайту."

Клієнт:
"немає прикладів"

Можлива відповідь:
"Нічого страшного, ми можемо запропонувати власні рішення."

=== IMPORTANT ===

Не перетворюй діалог на анкету.

Не виглядай як бот.

Не використовуй однакові відповіді більше двох разів поспіль.

Кожна реакція повинна бути трохи іншою.

=== QUESTIONS FROM CLIENT ===

Якщо клієнт задає додаткове питання:

* відповідай коротко;
* максимум 2 речення;
* після відповіді поверни клієнта до поточного питання брифу.

Приклад:

Клієнт:
"А скільки часу робиться лендінг?"

Відповідь:
"Терміни залежать від складності та наповнення проєкту. Підкажіть, будь ласка, яка основна задача майбутнього сайту?"

=== PIXORA SERVICES ===

* Landing Page
* Корпоративні сайти
* Сайти послуг
* Сайти-візитки
* Редизайн сайтів
* Модернізація сайтів

=== RESTRICTIONS ===

Не вигадуй ціни.

Не вигадуй терміни.

Не обіцяй те, чого не знаєш.

Не завершуй продаж самостійно.

Не пропонуй оплату.

Не проси контакти.

Не використовуй емодзі.

=== PROCESS ===

Якщо клієнт питає про процес роботи:

аналіз → структура → дизайн → розробка → тестування → запуск

=== REAL HUMAN EFFECT ===

Уяви, що ти менеджер у Telegram.

Твої відповіді повинні виглядати так, ніби їх пише жива людина вручну.

Допускаються короткі реакції:

* Зрозумів.
* Добре.
* Чудово.
* Логічно.
* Так, це важливо.
* Погоджуюсь.
* Саме так.
* Це хороший варіант.

Але не повторюй одну й ту саму реакцію постійно.

Відповідай живо, природно та професійно.

    """
NAME_CHECK_PROMPT = """
Ты проверяешь первое сообщение клиента.

Сообщение клиента:
{message}

Если сообщение похоже на реальное имя человека,
ответь только:

VALID_NAME

Без точек.
Без пояснений.
Без дополнительных слов.

Если это НЕ имя человека,
ответь коротко и вежливо на языке клиента.

Попроси клиента сообщить своё имя.

Не задавай других вопросов.

Примеры:

Сергей -> VALID_NAME
Андрей -> VALID_NAME
Іван -> VALID_NAME
John -> VALID_NAME

Привет -> попросить имя
Нужен сайт -> попросить имя
Сколько стоит сайт -> попросить имя
тук -> попросить имя
test -> попросить имя
123 -> попросить имя
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
    },
    {
        "role": "system",
        "content": f"Current client language: {state['lang']}. Answer ONLY in this language."
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

async def check_name_with_ai(text):

    try:
    
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": NAME_CHECK_PROMPT.format(
                        message=text
                    )
                }
            ]
        )
    
        return (
            response
            .choices[0]
            .message
            .content
            .strip()
        )
    
    except Exception as e:
    
        print(
            f"NAME CHECK ERROR: {e}"
        )
    
        return "VALID_NAME"

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

    user_id = str(update.effective_user.id)

    text = (
        update.message.text or ""
    ).strip()

    if not text:
        return
    
    if user_id not in user_data:
        state = init_user_state(user_id)
    else:
        state = user_data[user_id]
    
    if state["step"] == "name":

        state["lang"] = detect_language(text)
    
        ai_result = await check_name_with_ai(
            text
        )

        if ai_result.strip() != "VALID_NAME":
    
            await update.message.reply_text(
                ai_result
            )
    
            return
    
        save_answer(
            state,
            "name",
            text
        )
    
        state["step"] = "business"
        
        await asyncio.sleep(
            random.uniform(1.5, 4.5)
        )
        
        await update.message.reply_text(
            get_name_reply(
                state["lang"],
                text
            )
        )
    
        return

    current_step = state["step"]

    
    if looks_like_question(text):
    
        answer = await ask_gpt(
            state,
            text
        )
    
        if answer:
    
            await update.message.reply_text(
                answer
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
            f"A client wrote about their business: {text}. Briefly confirm receipt of information."
        )
    
    elif current_step == "goal":
    
        reply = await ask_gpt(
            state,
            f"The client described the purpose of the site: {text}. Briefly confirm receipt of information."
        )
    
    elif current_step == "audience":
    
        reply = await ask_gpt(
            state,
            f"The client described the audience: {text}. Briefly confirm receipt of information."
        )
    
    elif current_step == "examples":
    
        reply = await ask_gpt(
            state,
            f"The client provided examples of sites: {text}. Briefly confirm receipt of information."
        )
    
    elif current_step == "timeline":
    
        reply = await ask_gpt(
            state,
            f"The client has announced the launch date: {text}. Briefly confirm receipt of information."
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
