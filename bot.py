import telebot  #pip install pyTelegramBotAPI
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_BASE = "https://openrouter.ai/api/v1" #LOCAL_API_URL ,
MODEL_NAME = "minimax-m3.1-flash:free"
llm = ChatOpenAI(openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                 openai_api_base=OPENROUTER_BASE,
                 model_name=MODEL_NAME,
                 )

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

@bot.message_handler(func=lambda message: True)
def handle_llm_message(message):
    try:
        print(message.text)
        response = llm.invoke(message.text).content
        print(response)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}. Попробуйте еще раз.")
        

bot.polling()