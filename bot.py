import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from questions import questions

TIME_LIMIT = 30
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    qs = questions.copy()
    random.shuffle(qs)
    user_data[user_id] = {"questions": qs, "index": 0, "score": 0, "task": None}
    await send_question(context, user_id)

async def send_question(context, user_id):
    data = user_data[user_id]
    if data["index"] >= len(data["questions"]):
        await context.bot.send_message(
            chat_id=user_id,
            text=f"خلصت 👍\nنتيجتك: {data['score']} / 60"
        )
        return

    q = data["questions"][data["index"]]
    buttons = [
        [InlineKeyboardButton(f"{k}) {v}", callback_data=k)]
        for k, v in q["options"].items()
    ]
    await context.bot.send_message(
        chat_id=user_id,
        text=f"سؤال {data['index']+1}:\n{q['q']}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    data["task"] = asyncio.create_task(timer(context, user_id))

async def timer(context, user_id):
    await asyncio.sleep(TIME_LIMIT)
    if user_id in user_data:
        await context.bot.send_message(chat_id=user_id, text="الوقت خلص ❌")
        user_data[user_id]["index"] += 1
        await send_question(context, user_id)

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = user_data[user_id]
    if data["task"]:
        data["task"].cancel()
    q = data["questions"][data["index"]]
    if query.data == q["answer"]:
        data["score"] += 1
        await query.message.reply_text("صح ✅")
    else:
        await query.message.reply_text(
            f"غلط ❌\nالإجابة الصح: {q['answer']}) {q['options'][q['answer']]}"
        )
    data["index"] += 1
    await send_question(context, user_id)

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(answer))
app.run_polling()
