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

```
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
```

}

user_data = {}

def detect_language(text):

```
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
```

def get_next_step(step):

```
current_index = STEPS.index(step)

if current_index >= len(STEPS) - 1:
    return None

return STEPS[current_index + 1]
```

def save_answer(state, step, value):

```
state["answers"][step] = value.strip()
```

def init_user_state(user_id):

```
user_data[user_id] = {
    "lang": "uk",
    "step": "name",
    "answers": {},
    "history": [],
    "lead_sent": False
}

return user_data[user_id]
```

def looks_like_question(text):

```
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
```

async def ask_gpt(state, message):

```
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
```
