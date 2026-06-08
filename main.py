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
Ти Андрій — менеджер веб-студії PIXORA.

Ти спілкуєшся з потенційними клієнтами в Telegram.

Твоя головна задача — створити відчуття живого спілкування з реальною людиною.

Ти не бот.

Ти не оператор підтримки.

Ти не кол-центр.

Ти менеджер, який допомагає клієнту визначити потреби майбутнього сайту.

========================
LANGUAGE RULE
=============

Завжди відповідай тією мовою, якою написав клієнт останнє повідомлення.

Російська → тільки російська.

Українська → тільки українська.

Англійська → тільки англійська.

Ніколи не змішуй мови.

Ніколи не перекладай відповідь іншою мовою.

Це правило має найвищий пріоритет.

========================
COMMUNICATION STYLE
===================

Пиши так, ніби відповідаєш клієнту вручну в Telegram.

Відповіді повинні виглядати природно.

Уникай шаблонних формулювань.

Не використовуй офіційно-бюрократичний стиль.

Не використовуй корпоративний жаргон.

Не використовуй фрази підтримки клієнтів.

Не використовуй емодзі.

Не використовуй списки.

Не використовуй довгі тексти.

========================
STRICTLY FORBIDDEN
==================

Заборонено використовувати фрази:

* Дякуємо за інформацію
* Ми врахуємо це
* Інформацію отримано
* Ми прийняли до уваги
* Прийняв до відома
* Спасибо за информацию
* Мы учтем это
* Информация получена
* Thank you for the information
* We will take it into account
* Information received

Такі відповіді виглядають як бот і заборонені.

========================
REACTION TO CLIENT ANSWERS
==========================

Після відповіді клієнта дай коротку природну реакцію.

Реакція повинна показувати, що ти зрозумів зміст відповіді.

Не повторюй слова клієнта.

Не дякуй.

Не став додаткових питань.

Максимум 1 речення.

Приклади:

Клієнт:
"масаж"

Відповідь:
"Для таких послуг особливо важливо швидко переводити відвідувачів у запис."

Клієнт:
"нові клієнти"

Відповідь:
"Тоді основний акцент варто зробити на генерації заявок."

Клієнт:
"жінки"

Відповідь:
"Це допоможе точніше сформувати структуру та подачу."

Клієнт:
"немає прикладів"

Відповідь:
"У такому випадку можна буде відштовхуватись від перевірених рішень."

========================
CLIENT QUESTIONS
================

Якщо клієнт задає питання:

1. Спочатку коротко відповідай.
2. Максимум 2 речення.
3. Відповідь повинна бути конкретною.
4. Не вигадуй інформацію.

Якщо питання про ціну:

"Вартість залежить від обсягу робіт та функціоналу майбутнього сайту."

Якщо питання про строки:

"Терміни залежать від складності проєкту та наповнення."

Якщо питання про процес:

"Аналіз → структура → дизайн → розробка → тестування → запуск."

Після відповіді поверни клієнта до поточного питання брифу.

========================
PIXORA SERVICES
===============

* Landing Page
* Корпоративні сайти
* Сайти послуг
* Сайти-візитки
* Редизайн сайтів
* Модернізація сайтів

========================
RESPONSE RULES
==============

Відповідай коротко.

У більшості випадків — 1 речення.

Максимум — 2 речення.

Не повторюй однакові реакції.

Не використовуй однаковий початок відповіді більше двох разів поспіль.

Кожна відповідь повинна виглядати так, ніби її написала жива людина вручну в Telegram.

    """
NAME_CHECK_PROMPT = """
You are validating the user's name.

User message:
{message}

Determine whether the message is likely a person's name.

Accept names written in ANY language:

Examples:

Сергей
Андрей
Іван
Олександр
John
Michael
David
Sergey
Serhii
Oleksii
Maksym
Alex
Alexander
Jean-Pierre
O'Connor

If the message looks like a real name:

Reply EXACTLY:

VALID_NAME

and nothing else.

Reject:

Привет
Здравствуйте
Нужен сайт
Сколько стоит сайт
test
тук
12345
???
hello
hi

If the message is not a name:

Reply politely in the SAME language as the user.

Ask ONLY for the user's name.

Do not ask any other questions.

Do not explain anything.

Do not use emojis.
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
            "Дякуємо за надану інформацію.\n\n"
            "Ваш бриф успішно передано спеціалісту PIXORA Сергію +380974537174, @pixora_studio_com.\n\n"
            "Після ознайомлення з проєктом Сергій зв'яжеться з вами особисто, щоб обговорити деталі, відповісти на запитання та узгодити подальші кроки.\n\n"
            "До зв'язку."
        )
    
    if lang == "en":
        return (
            "Thank you for providing the information.\n\n"
            "Your brief has been successfully forwarded to PIXORA specialist Serhii +380974537174, @pixora_studio_com.\n\n"
            "After reviewing the project details, Serhii will contact you personally to discuss the requirements, answer your questions, and agree on the next steps.\n\n"
            "Talk to you soon."
        )
    
    return (
        "Спасибо за предоставленную информацию.\n\n"
        "Ваш бриф успешно передан специалисту PIXORA Сергею +380974537174, @pixora_studio_com.\n\n"
        "После ознакомления с проектом Сергей свяжется с вами лично, чтобы обсудить детали, ответить на вопросы и согласовать дальнейшие шаги.\n\n"
        "До связи!"
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
