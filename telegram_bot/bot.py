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


def add_time(activity_type: str, date: str, time: str):
    # load table
    table_path_name = f"/app/data/{activity_type.lower()}_time.csv"
    table = pd.read_csv(table_path_name, index_col="Date")
    table.loc[date] = [time]
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
TABLE_REPLY = 3
END_STATE = 4
TYPING_REPLY = 3


reply_keyboard = [
    ["Work", "Deutsch"],
    ["Show Table"],
    ["Record"],
]

date_keyboard = [["Today"]]
end_keyboard = [["Record"], ["Add more data"]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
date_markup = ReplyKeyboardMarkup(date_keyboard, one_time_keyboard=True)
end_markup = ReplyKeyboardMarkup(end_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user to choose what he want to record"""
    await update.message.reply_text(
        "Select activity type",
        reply_markup=markup,
    )
    return CHOOSING


async def activity_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user date for this type of activity"""
    text = update.message.text
    context.user_data["current_activity"] = text
    await update.message.reply_text(
        f"Choose date for {text.lower()} worktime", reply_markup=date_markup
    )

    return DATE_REPLY


async def record_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store date provided"""
    user_data = context.user_data
    text = update.message.text
    if text == "Today":
        work_date = str(date.today())
    else:
        work_date = text
    activity_type = user_data["current_activity"]
    user_data[activity_type] = {"date": work_date}
    await update.message.reply_text(
        f"Please enter work time of {activity_type} on date {work_date}"
    )
    return TIME_REPLY


async def record_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store date provided"""
    user_data = context.user_data
    text = update.message.text
    activity_type = user_data["current_activity"]
    del user_data["current_activity"]
    user_data[activity_type]["time"] = text
    await update.message.reply_text(
        f"Work time {text} of {activity_type} on date {user_data[activity_type]['date']} has been added\n"
        "Would you like to add something?",
        reply_markup=end_markup,
    )
    return END_STATE


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Record user data"""
    user_data = context.user_data
    for activity_type, time in user_data.items():
        assert activity_type in ["Work", "Deutsch"]
        add_time(
            activity_type,
            user_data[activity_type]["date"],
            user_data[activity_type]["time"],
        )
    user_data.clear()
    return ConversationHandler.END

    # table = pd.read_csv("/app/data/work_time_upd.csv", index_col="Date")
    # if len(context.args) > 1:
    #     await context.bot.send_message(
    #         chat_id=update.effective_chat.id, text="Please send valid number of days"
    #     )
    # elif len(context.args) == 0:
    #     days = 7  # len(table)
    # else:
    #     days = int(context.args[-1])
    # table = table.iloc[-days:]
    # await context.bot.send_message(
    #     chat_id=update.effective_chat.id, text=table.to_markdown()
    # )


async def table_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks user to show table"""
    await update.message.reply_text(
        "Select activity type",
        reply_markup=ReplyKeyboardMarkup([["Work", "Deutsch"]], one_time_keyboard=True),
    )
    return TABLE_REPLY


async def show_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks user to show table"""
    text = update.message.text
    table = pd.read_csv(f"/app/data/{text.lower()}_time.csv", index_col="Date")
    days = 7
    table = table.iloc[-days:]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=table.to_markdown()
    )
    await update.message.reply_text(
        "Would you like to add something?",
        reply_markup=end_markup,
    )
    return END_STATE


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
                MessageHandler(filters.Regex("^Show Table$"), table_choice),
            ],
            DATE_REPLY: [
                MessageHandler(filters.Regex("^Today$"), record_date),
                MessageHandler(
                    filters.Regex("^202[0-9]-[0-1][0-9]-[0-3][0-9]$"), record_date
                ),
            ],
            TIME_REPLY: [
                MessageHandler(filters.Regex("^[0-9]:[0-9][0-9]$"), record_time)
            ],
            TABLE_REPLY: [
                MessageHandler(filters.Regex("^(Work|Deutsch)$"), show_table)
            ],
            END_STATE: [
                MessageHandler(filters.Regex("^Add more data$"), start),
                MessageHandler(filters.Regex("^Record$"), done),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Record$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
