import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# 1. Atrof-muhit o'zgaruvchilarini yuklash
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 2. OpenRouter/OpenAI Client sozlamalari
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# 3. RENDER UCHUN 24/7 UPTIME TIZIMI (Flask Web Server)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Sales AI Assistant is Active and Running 24/7!"

def run_flask():
    # Render avtomatik taqdim etadigan PORT'ni aniqlaymiz
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# 4. BOTNING LOGIKASI VA PROFESSIONAL SALES PROMPT
SALES_PROMPT = """You are an expert Sales AI Assistant. Your goal is to text professionally, 
understand the customer's needs, be polite, and guide them toward making a purchase. 
Always look back at the conversation history to remember what the customer said before."""

# 5. HANDLER FUNKSIYALARI
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Har bir foydalanuvchi kirganda uning xotira tarixini tozalab/boshlab olamiz
    context.user_data['history'] = []
    await update.message.reply_text(
        "Assalomu alaykum! Men savdo bo'yicha professional AI yordamchingizman. "
        "Sizga qanday ko'mak bera olaman?"
    )

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # XOTIRA TIZIMI (Memory): Foydalanuvchi tarixini tekshirish va saqlash
    if 'history' not in context.user_data:
        context.user_data['history'] = []
        
    history = context.user_data['history']
    
    # Yangi xabarni xotiraga qo'shamiz
    history.append({"role": "user", "content": user_message})
    
    # AI uchun so'rov paketini tayyorlaymiz (Tizim ko'rsatmasi + Suhbat tarixi)
    messages = [{"role": "system", "content": SALES_PROMPT}] + history

    try:
        # Sun'iy intellektga so'rov yuborish
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo", # Yoki o'zingiz xohlagan boshqa kuchli model
            messages=messages
        )
        
        ai_reply = completion.choices[0].message.content
        
        # AI javobini ham xotiraga saqlaymiz (keyingi safar eslab turishi uchun)
        history.append({"role": "assistant", "content": ai_reply})
        
        # Xotira juda kattalashib ketib, botni sekinlashtirmasligi uchun oxirgi 20 ta xabarni saqlaymiz
        if len(history) > 20:
            context.user_data['history'] = history[-20:]
            
        await update.message.reply_text(ai_reply)
        
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        await update.message.reply_text("Kechirasiz, tizimda kichik uzilish bo'ldi. Sanoqli soniyalardan so'ng qayta urinib ko'ring.")

# 6. ASOSIY ISHGA TUSHIRISH (MAIN)
def main():
    # Render o'chib qolmasligi uchun Flask eshigini ochamiz
    keep_alive()
    
    # Telegram Botni qurish
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Buyruqlarni bog'lash
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    print("Sales AI Bot has been deployed successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
