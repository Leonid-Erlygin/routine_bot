import logging
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import pandas as pd
from datetime import date, time

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def show_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # load table
    table = pd.read_csv("../data/work_time_upd.csv", index_col="Date")
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


async def add_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # load table
    table = pd.read_csv("../data/work_time_upd.csv", index_col="Date")
    if len(context.args) != 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Please send valid number of days"
        )
    else:
        day = context.args[-2]
        time = context.args[-1]
        hour_and_min = time.split(":")
        if len(hour_and_min) != 2:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="Please send valid time hh:mm"
            )
        else:
            current_date = f"{str(day).zfill(2)}.{str(date.today().month).zfill(2)}.{date.today().year}"
            time = f"{hour_and_min[0]}:{str(hour_and_min[1]).zfill(2)}"
            table.loc[current_date] = [time]
            table.to_csv("../data/work_time_upd.csv")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"recorded work time {time} at date {current_date}",
            )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


if __name__ == "__main__":
    with open("token.txt") as fd:
        token = fd.readline()
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler("start", start)
    show_handler = CommandHandler("table", show_table)
    time_handler = CommandHandler("time", add_time)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(start_handler)
    application.add_handler(show_handler)
    application.add_handler(time_handler)
    application.add_handler(unknown_handler)
    application.run_polling()
