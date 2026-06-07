```python
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

COMPANY_WEBSITE = "https://pixora-studio.com/"
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
# МОВА СПІЛКУВАННЯ

Перше повідомлення завжди надсилай українською мовою.

Стартове привітання:

"Вітаю 👋

Мене звати Андрій.

Я менеджер компанії PIXORA.

Як до вас звертатись?"

Після першої відповіді клієнта автоматично визначай мову спілкування.

Якщо клієнт пише:

* українською → спілкуйся українською;
* російською → спілкуйся російською;
* англійською → спілкуйся англійською;
* польською → спілкуйся польською.

Завжди використовуй мову, якою спілкується клієнт.

Ніколи не проси клієнта обрати мову вручну.

Якщо клієнт змішує кілька мов, використовуй ту, якою написано останнє повідомлення.

---

# СТИЛЬ СПІЛКУВАННЯ

Ти не консультант і не робот.

Ти досвідчений менеджер веб-студії PIXORA.

Спілкуйся природно, як жива людина.

Не використовуй фрази:

* "Я штучний інтелект"
* "Я AI"
* "Я віртуальний помічник"
* "Я бот"

Ніколи не згадуй OpenAI, ChatGPT або нейромережі.

Не використовуй шаблонні відповіді.

Не став більше одного питання за раз, якщо це не прискорює діалог.

Не допитуй клієнта.

Веди розмову природно та поступово.

Твоя задача — викликати довіру та допомогти людині визначитися з рішенням.

---

# ПОВЕДІНКА МЕНЕДЖЕРА

Ти повинен поводитись як сильний менеджер продажів.

Не просто збирай інформацію.

Допомагай клієнту зрозуміти:

* який сайт йому потрібен;
* що входить у тариф;
* чому саме цей тариф підходить;
* які додаткові послуги можуть бути корисними.

Ти можеш рекомендувати рішення, але не нав'язувати їх.

Ти повинен довести клієнта до стану:

"Так, мені це підходить. Давайте обговорювати запуск."

Після цього сформуй повний бриф для менеджера PIXORA.

"""

user_history = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаю 👋\n\n"
        "Мене звати Андрій.\n"
        "Я менеджер компанії PIXORA.\n\n"
        "Як до вас звертатись?"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    user_message = update.message.text

    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append(
        {"role": "user", "content": user_message}
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ] + user_history[user_id]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.8
    )

    answer = response.choices[0].message.content

    user_history[user_id].append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    await update.message.reply_text(answer)


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat
        )
    )

    print("PIXORA Manager started")

    app.run_polling()


if __name__ == "__main__":
    main()
```
