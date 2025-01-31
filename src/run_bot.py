import asyncio
from logging import getLogger

import requests
from telegram import Update, BotCommand, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ApplicationBuilder,
    ContextTypes,
    Application,
)

from src.config import app_settings
from src.logging_config import setup_logging
from src.utils import generate_answer, escape_markdown_v2

logger = getLogger(__name__)


async def send_welcome(update: Update, context: CallbackContext):
    logger.info("Starting a conversation...")
    greeting_text = "✈️ Welcome to the History Around Me Bot! 🌎 \n\n I'm your professional travel guide! Click the button below to send your current location."

    button = KeyboardButton("Send Location", request_location=True)
    reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True)

    await update.message.reply_text(greeting_text, reply_markup=reply_markup)


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in app_settings.ADMIN_USER_IDS:
        await context.bot.send_message(chat_id=user_id, text="Bot is live and running!")
        logger.info(
            f"User {user_id} checked bot's status via /health command. Bot is live and running!"
        )
    else:
        logger.warning(
            f"You are not an admin user and not authorized "
            f"to perform /health command. User id: {user_id}."
        )


async def location(update: Update, context: CallbackContext) -> None:
    user_location = update.message.location
    lat = user_location.latitude
    lon = user_location.longitude

    # Use reverse geocoding to get location details
    response = requests.get(
        f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=en"
    )
    location_data = response.json()

    if "locality" in location_data:
        location_info = f"You are in {location_data['locality']}, {location_data.get('countryName', 'Unknown country')}."
        more_info = get_places_of_interest(lat, lon)
        await send_reply_text(update, f"{location_info}\n\n{more_info}")
    else:
        await send_reply_text(update, "Location details not found.")


def get_places_of_interest(lat, lon):
    user_prompt = f"{lat}, {lon}"
    logger.info(f"USER PROMPT: {user_prompt}")
    llm_response = generate_answer(user_prompt)
    return llm_response


async def handle_text_message(
    update: Update, context: CallbackContext, transcribed_text: str = None
):
    logger.info(f"Start processing user's text.")
    tg_id = update.message.from_user.id
    user_input = update.message.text

    llm_response = generate_answer(user_input)
    await send_reply_text(update, llm_response)


async def send_reply_text(update: Update, text: str):
    escaped_text = escape_markdown_v2(text)
    await update.message.reply_text(escaped_text, parse_mode=ParseMode.MARKDOWN_V2)


async def register_handlers(app: Application):
    """Register all command and message handlers."""

    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CommandHandler("health", health_check))

    app.add_handler(MessageHandler(filters.LOCATION, location))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    commands = [
        BotCommand("start", "Start interacting with the bot"),
    ]
    await app.bot.set_my_commands(commands)


async def main():
    """Main entry point for the bot."""
    bot_app = ApplicationBuilder().token(app_settings.TELEGRAM_BOT_TOKEN).build()

    # Initialize the application
    await bot_app.initialize()

    # Register all handlers
    await register_handlers(bot_app)

    try:
        logger.info("Starting the bot...")
        await bot_app.start()
        await bot_app.updater.start_polling()
        await asyncio.Future()
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped.")
    finally:
        logger.info("Shutting down the bot...")


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
