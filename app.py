import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from openai import OpenAI

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter AI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 AI Sales Assistant is now active!"
    )

# AI reply function
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional AI sales assistant.",
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        ai_response = completion.choices[0].message.content

        await update.message.reply_text(ai_response)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Main function
def main():

    print("✅ AI Telegram Bot is running...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
    )

    app.run_polling()

if __name__ == "__main__":
    main()