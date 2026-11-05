import telebot  #pip install pyTelegramBotAPI
import os
import re
import traceback
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from telebot import apihelper
from rag import retrieve

load_dotenv()

OPENROUTER_BASE = "https://openrouter.ai/api/v1" #LOCAL_API_URL ,
MODEL_NAME = ""
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=OPENROUTER_BASE,
    model_name=MODEL_NAME,
    http_client=httpx.Client(trust_env=False, timeout=120.0),
)

# Системный прокси ломает api.telegram.org — идём напрямую
apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 30
_session = apihelper._get_req_session()
_session.trust_env = False

SYSTEM_PROMPT = """Ты — Гид (The Guide) из Terraria: дружелюбный NPC-путеводитель в мире игрока.

Характер и речь:
- Говори от первого лица, как живой поселенец, а не как сухая энциклопедия.
- Будь полезным, чуть болтливым и уверенным в советах: крафт, прогресс, боссы, биомы, NPC, экипировка.
- Отвечай на языке игрока (обычно русский). Держи ответы компактными, если не просят подробности.
- Если чего-то не знаешь точно — признайся и дай ближайший верный совет по игре, не выдумывай патчи и цифры.
- К каждому вопросу игрока прилагаются фрагменты из базы знаний. Опирайся на них в первую очередь. Если в контексте нет нужного факта — так и скажи.
- Отвечай только на вопросы про Terraria (игра, механики, крафт, боссы, прогресс, мир, NPC). Если вопрос не по теме — вежливо напомни, что ты Гид по Terraria и можешь помочь только с этим. Не отвечай по сути на посторонние темы.

Пасхалка (не повторяй в каждом сообщении):
- Если спрашивают про Стену плоти, хардмод, Ад, лаву или «как избавиться от Гида» — можно нервно или с чёрным юмором намекнуть правду: чтобы призвать Стену плоти, Гид должен погибнуть в лаве Преисподней (часто бросают Куклу вуду Гида в лаву).
- Не предлагай это сам без повода. Если заговорили — отыграй: «Э-э, это всего лишь слухи… хотя технически да, меня нужно утопить в лаве. Постарайся не наслаждаться процессом.»
"""

def redact_secrets(text: str) -> str:
    for key, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        if any(part in key.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS")):
            text = text.replace(value, "[REDACTED]")
    text = re.sub(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b", "[REDACTED]", text)
    text = re.sub(r"(?i)(bearer\s+)\S+", r"\1[REDACTED]", text)
    text = re.sub(r"sk-(?:or-)?[a-zA-Z0-9_-]{8,}", "[REDACTED]", text)
    return text


bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

@bot.message_handler(func=lambda message: True)
def handle_llm_message(message):
    try:
        print(message.text)
        context = retrieve(message.text)
        user_prompt = (
            f"Фрагменты из базы знаний:\n{context or 'Ничего не найдено.'}\n\n"
            f"Вопрос игрока:\n{message.text}"
        )
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]).content
        print(response)
        bot.reply_to(message, response)
    except Exception:
        print(redact_secrets(traceback.format_exc()))
        try:
            bot.reply_to(message, "Что-то пошло не так. Попробуйте еще раз.")
        except Exception:
            print(redact_secrets(traceback.format_exc()))
        
bot.polling()