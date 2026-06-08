```python
import os
import re

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

client = OpenAI(
    api_key=OPENAI_API_KEY
)

LEAD_CHAT_ID = 499657192

user_history = {}
lead_sent_users = set()


SYSTEM_PROMPT = """
ВСТАВЬ СЮДА СВОЙ НОВЫЙ PROMPT PIXORA v4.0
"""


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Вітаю 👋\n\n"
        "Мене звати Андрій.\n"
        "Я менеджер компанії PIXORA.\n\n"
        "Як до вас звертатись?"
    )


async def chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = str(
        update.effective_user.id
    )

    user_message = (
        update.message.text or ""
    ).strip()

    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append(
        {
            "role": "user",
            "content": user_message
        }
    )

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ] + user_history[user_id],
            temperature=0.7
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

    except Exception as e:

        print("OPENAI ERROR:")
        print(str(e))

        await update.message.reply_text(
            "Сталася помилка. Спробуйте ще раз трохи пізніше."
        )

        return

    print("========== GPT ANSWER ==========")
    print(answer)
    print("================================")

    if not answer:

        answer = (
            "Сталася помилка під час обробки повідомлення."
        )

    user_history[user_id].append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    phone_found = re.search(
        r'(\+?\d[\d\s\-\(\)]{8,})',
        user_message
    )

    if (
        phone_found
        and user_id not in lead_sent_users
    ):

        lead_sent_users.add(user_id)

        telegram_id = (
            update.effective_user.id
        )

        username = (
            update.effective_user.username
        )

        username_text = (
            f"@{username}"
            if username
            else "Не вказано"
        )

        lead_text = (
            "🔥 НОВИЙ ЛІД PIXORA\n\n"
            f"Telegram ID: {telegram_id}\n"
            f"Username: {username_text}\n\n"
            "====================\n"
            "ДІАЛОГ\n"
            "====================\n\n"
        )

        for msg in user_history[user_id]:

            role = (
                "КЛІЄНТ"
                if msg["role"] == "user"
                else "PIXORA"
            )

            lead_text += (
                f"{role}: "
                f"{msg['content']}\n\n"
            )

        try:

            await context.bot.send_message(
                chat_id=LEAD_CHAT_ID,
                text=lead_text[:4000]
            )

            print("LEAD SENT")

        except Exception as e:

            print("LEAD SEND ERROR:")
            print(str(e))

        final_message = (
            "Спасибо за предоставленную информацию.\n\n"
            "Я подготовил предварительное описание проекта.\n\n"
            "В ближайшее время с вами свяжется Сергей для обсуждения деталей, сроков реализации и стоимости работ.\n\n"
            "Спасибо за обращение в PIXORA."
        )

        await update.message.reply_text(
            final_message
        )

        return

    await update.message.reply_text(
        answer
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

    print("PIXORA Manager started")

    app.run_polling()


if __name__ == "__main__":
    main()
```
