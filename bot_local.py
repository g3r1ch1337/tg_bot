import telebot  #pip install pyTelegramBotAPI
import os
import time
from collections import defaultdict, deque
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from telebot import apihelper

load_dotenv()

OPENROUTER_BASE = "http://localhost:11434/v1" #LOCAL_API_URL ,
MODEL_NAME = "gemma3:4b"
MAX_HISTORY = 5

# trust_env=False — не ходить в localhost через системный прокси (иначе 503)
llm = ChatOpenAI(
    openai_api_key="fake_key",
    openai_api_base=OPENROUTER_BASE,
    model_name=MODEL_NAME,
    http_client=httpx.Client(trust_env=False, timeout=120.0),
)

# Системный прокси 127.0.0.1:10809 нестабилен для api.telegram.org — идём напрямую
apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 30
_session = apihelper._get_req_session()
_session.trust_env = False

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# История сообщений по chat_id (последние MAX_HISTORY сообщений)
chat_histories = defaultdict(lambda: deque(maxlen=MAX_HISTORY))


def reply_with_retry(message, text, attempts=3):
    last_error = None
    for i in range(attempts):
        try:
            return bot.reply_to(message, text)
        except Exception as e:
            last_error = e
            time.sleep(1 + i)
    raise last_error


@bot.message_handler(commands=["start", "clear"])
def handle_clear(message):
    chat_histories[message.chat.id].clear()
    reply_with_retry(message, "История чата очищена. Можем начать заново.")


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
    except Exception as e:
        if history and isinstance(history[-1], HumanMessage):
            history.pop()
        try:
            reply_with_retry(message, f"Ошибка модели: {e}. Попробуйте еще раз.")
        except Exception:
            print(f"Не удалось отправить ошибку в Telegram: {e}")
        return

    try:
        reply_with_retry(message, response)
    except Exception as e:
        print(f"Не удалось отправить ответ в Telegram: {e}")


bot.infinity_polling(timeout=60, long_polling_timeout=40)
