import telebot  #pip install pyTelegramBotAPI
import os
from collections import defaultdict, deque
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

OPENROUTER_BASE = "https://openrouter.ai/api/v1" #LOCAL_API_URL ,
MODEL_NAME = "minimax-m3.1-flash:free"
MAX_HISTORY = 5

llm = ChatOpenAI(openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                 openai_api_base=OPENROUTER_BASE,
                 model_name=MODEL_NAME,
                 )

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# История сообщений по chat_id (последние MAX_HISTORY сообщений)
chat_histories = defaultdict(lambda: deque(maxlen=MAX_HISTORY))


@bot.message_handler(commands=["start", "clear"])
def handle_clear(message):
    chat_histories[message.chat.id].clear()
    bot.reply_to(message, "История чата очищена. Можем начать заново.")


@bot.message_handler(func=lambda message: True)
def handle_llm_message(message):
    if not message.text:
        return

    history = chat_histories[message.chat.id]
    try:
        print(message.text)
        history.append(HumanMessage(content=message.text))
        response = llm.invoke(list(history)).content
        history.append(AIMessage(content=response))
        print(response)
        bot.reply_to(message, response)
    except Exception as e:
        if history and isinstance(history[-1], HumanMessage):
            history.pop()
        bot.reply_to(message, f"Ошибка: {e}. Попробуйте еще раз.")


bot.polling()
