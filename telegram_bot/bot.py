import logging
from typing import Dict
from datetime import date, time
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

import pandas as pd

with open("/app/telegram_bot/token.txt") as fd:
    token = fd.readline()


async def show_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # load table
    table = pd.read_csv("/app/data/work_time_upd.csv", index_col="Date")
    if len(context.args) > 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Please send valid number of days"
        )
    elif len(context.args) == 0:
        days = 7  # len(table)
    else:
        days = int(context.args[-1])
    table = table.iloc[-days:]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=table.to_markdown()
    )


def add_time(activity_type: str, date: date, time: time):
    # load table
    table_path_name = f"/app/data/{activity_type.lower()}_time_upd.csv"
    table = pd.read_csv(table_path_name, index_col="Date")
    table.loc[str(date)] = [str(time)[:-3]]
    table.to_csv(table_path_name)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Stages
START_ROUTES, END_ROUTES = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)

CHOOSING = 0
DATE_REPLY = 1
TIME_REPLY = 2

TYPING_REPLY = 3

reply_keyboard = [
    ["Work", "Deutsch"],
    ["Record"],
]
date_keyboard = [["Today", "Enter date"]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    await update.message.reply_text(
        "Hi! My name is Doctor Botter. I will hold a more complex conversation with you. "
        "Why don't you tell me something about yourself?",
        reply_markup=markup,
    )

    return CHOOSING


async def activity_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(
        f"Choose date for {text.lower()} worktime", reply_markup=date_keyboard
    )

    return DATE_REPLY


async def record_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store date provided"""
    user_data = context.user_data
    text = update.message.text
    if text == "Today":
        work_date = date.today()
        activity_type = user_data["choice"]
        user_data[activity_type] = {"date": work_date}
        # del user_data["choice"]
        return TIME_REPLY
    else:
        await update.message.reply_text(
            "Enter date",
        )
        return


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Record user data"""
    user_data = context.user_data
    for activity_type, time in d:
        pass
    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^(Work|Deutsch)$"), activity_choice),
            ],
            DATE_REPLY: [
                MessageHandler(filters.Regex("^(Today|Enter date)$"), record_date)
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Record$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
