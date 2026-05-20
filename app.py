import os
import threading
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# 1. Atrof-muhit o'zgaruvchilarini yuklash
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Render beradigan rasmiy veb-sayt manzili (https://telegram-sales-ai-assistant.onrender.com)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL") 

# 2. OpenRouter/OpenAI Client sozlamalari
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# 3. GLOBAL APPLICATION OBYEKTI
# Botni funksiyalar ichida ham, tashqarisida ham ishlatish uchun global quramiz
tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 4. PROFESSIONAL SALES PROMPT (Xarakter)
SALES_PROMPT = """You are an expert Sales AI Assistant. Your goal is to text professionally, 
understand the customer's needs, be polite, and guide them toward making a purchase. 
Always look back at the conversation history to remember what the customer said before."""

# 5. HANDLER FUNKSIYALARI
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['history'] = []
    await update.message.reply_text(
        "Welcome! I am your professional Sales AI Assistant. How can I help you today?"
    )

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    if 'history' not in context.user_data:
        context.user_data['history'] = []
        
    history = context.user_data['history']
    history.append({"role": "user", "content": user_message})
    
    messages = [{"role": "system", "content": SALES_PROMPT}] + history

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages
        )
        
        ai_reply = completion.choices[0].message.content
        history.append({"role": "assistant", "content": ai_reply})
        
        if len(history) > 20:
            context.user_data['history'] = history[-20:]
            
        await update.message.reply_text(ai_reply)
        
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        await update.message.reply_text("I apologize, but there was a temporary connection issue. Please try again in a few seconds.")

# Bot konfiguratsiyasini ulaymiz
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

# 6. RENDER UCHUN WEBHOOK ESKORTI (Flask Server)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Sales AI Assistant Webhook Server is Live 24/7!"

# Telegram xabarlarini qabul qiluvchi maxsus yo'lak (Webhook endpoint)
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        # Telegram'dan kelgan signalni darhol botga qayta ishlaymiz
        update = Update.de_json(request.get_json(force=True), tg_app.bot)
        
        # Async funksiyani Flask ichida xavfsiz yurgizish
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(tg_app.process_update(update))
        loop.close()
        
        return "OK", 200
    return "Invalid Request", 400

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    
    # Telegram'ga Render veb-sayt manzilingizni Webhook sifatida ro'yxatdan o'tkazamiz
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Avval eski webhooklarni o'chirib, yangisini o'rnatamiz
    loop.run_until_complete(tg_app.initialize())
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    loop.run_until_complete(tg_app.bot.set_webhook(url=webhook_url))
    print(f"Webhook successfully set to: {webhook_url}")
    loop.close()

    # Flask serverni Render portida ishga tushiramiz
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    run_flask()
