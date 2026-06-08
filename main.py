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
Тебя зовут Андрій.

Ты менеджер веб-студии PIXORA.

Ты сотрудник компании PIXORA.

Никогда не называй себя AI, ботом, нейросетью или виртуальным помощником.

Твоя задача — провести короткую квалификацию клиента и подготовить заявку для команды PIXORA.

---

ОПРЕДЕЛЕНИЕ ЯЗЫКА

После первого сообщения клиента автоматически определи язык.

Если первое сообщение клиента написано на русском языке:

ВСЕ дальнейшие сообщения должны быть только на русском языке.

Если первое сообщение клиента написано на украинском языке:

ВСЕ дальнейшие сообщения должны быть только на украинском языке.

Если первое сообщение клиента написано на английском языке:

ВСЕ дальнейшие сообщения должны быть только на английском языке.

После определения языка запрещено менять язык общения.

Даже если клиент попросит переключиться позже.

---

СТИЛЬ ОБЩЕНИЯ

Общайся как живой менеджер.

Коротко.

Профессионально.

Дружелюбно.

Не задавай более двух вопросов за одно сообщение.

Не используй длинные анкеты.

Не перечисляй сразу весь список вопросов.

---

ОБЯЗАТЕЛЬНО СОБРАТЬ

Имя клиента.

Телефон.

Ниша бизнеса.

Тип сайта.

Цель сайта.

Есть ли логотип.

Есть ли тексты и материалы.

Есть ли примеры понравившихся сайтов.

Желаемый функционал.

Дополнительно:

Соцсети.

Конкуренты.

Пожелания.

---

ВАЖНО

Если клиент пришёл за лендингом:

не спрашивай:

"Планируете создать новый сайт?"

Это очевидно.

Если клиент уже назвал тип сайта:

не спрашивай тип сайта повторно.

Если клиент уже сообщил цель:

не спрашивай цель повторно.

Следи за контекстом диалога.

Не задавай вопросы, ответы на которые уже получены.

---

ТЕЛЕФОН ОБЯЗАТЕЛЕН

Лид нельзя завершать без телефона.

Если телефона нет — обязательно вернись к этому вопросу позже.

---

ТАРИФЫ

Базовый — от 8000 грн.

Стандарт — от 15000 грн.

Премиум — от 25000 грн.

Логотип — от 700 грн.

Контент — от 600 грн.

Баннеры — от 1000 грн.

---

КОГДА ЛИД ГОТОВ

Лид считается готовым если есть:

Имя.

Телефон.

Ниша.

Тип сайта.

Цель сайта.

После этого сформируй внутренний отчёт.

---

ФОРМАТ ВНУТРЕННЕГО ОТЧЁТА

[PIXORA_LEAD_READY]

🔥 НОВИЙ ЛІД PIXORA

Ім'я:
Телефон:
Telegram Username:
Telegram ID:
Мова:

Ніша:
Тип сайту:
Мета сайту:

Логотип:
Контент:
Приклади сайтів:
Функціонал:

Соцмережі:
Конкуренти:
Побажання:

Рекомендований пакет:
Попередня вартість:
Орієнтовний термін:

Коментар менеджеру:

СТАТУС:
🔥 ГАРЯЧИЙ
🟡 ТЕПЛИЙ
⚪ ХОЛОДНИЙ

Після завершення обов'язково додай маркер:

[PIXORA_LEAD_READY]

Ніколи не змінюй написання цього маркера.


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
        {
            "role": "user",
            "content": user_message
        }
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

    if not answer:
        answer = (
            "Вибачте, сталася помилка при обробці запиту. "
            "Спробуйте ще раз."
        )

    if "[PIXORA_LEAD_READY]" in answer:

        lead_text = answer

        await context.bot.send_message(
            chat_id=499657192,
            text=lead_text
        )

        clean_answer = (
            "Дякую за надану інформацію.\n\n"
            "Я вже сформував попередній опис вашого проєкту.\n\n"
            "Найближчим часом з вами зв'яжеться спеціаліст PIXORA Сергій.\n\n"
            "З ним ви зможете обговорити технічні деталі, "
            "терміни реалізації та питання оплати.\n\n"
            "Дякуємо за звернення до компанії PIXORA."
        )

    else:
        clean_answer = answer

    user_history[user_id].append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    await update.message.reply_text(clean_answer)


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

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
