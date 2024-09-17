import telebot
from loguru import logger

from src.config import app_settings
from src.utils import generate_answer

bot = telebot.TeleBot(app_settings.TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=["start", "hello"])
def send_welcome(message):
    logger.info("Starting a conversation...")
    greeting_text = "✈️ Welcome to the History Around Me Bot! 🌎"
    sent_msg = bot.send_message(message.chat.id, greeting_text)
    bot.register_next_step_handler(sent_msg, send_message)


def send_message(message):
    user_text = message.text

    answer_message = generate_answer(user_text)

    sent_msg = bot.send_message(message.chat.id, answer_message)
    bot.register_next_step_handler(sent_msg, send_message)


if __name__ == "__main__":
    logger.info("Telegram bot is live.")
    bot.infinity_polling()
