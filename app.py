import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# 1. Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 2. Configure OpenRouter/OpenAI Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# 3. RENDER 24/7 UPTIME SYSTEM (Flask Web Server)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Sales AI Assistant is Active and Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# 4. PROFESSIONAL SALES PROMPT
SALES_PROMPT = """You are an expert Sales AI Assistant. Your goal is to text professionally, 
understand the customer's needs, be polite, and guide them toward making a purchase. 
Always look back at the conversation history to remember what the customer said before."""

# 5. HANDLER FUNCTIONS
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
        print(f"Error: {e}")
        await update.message.reply_text("I apologize, but there was a temporary connection issue. Please try again in a few seconds.")

# 6. MAIN APPLICATION
def main():
    keep_alive()
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    print("Sales AI Bot has been deployed successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
