from aiogram import Dispatcher, F
from bot import bot
import asyncio
import sqlite3
from handlers.group_handler import group_router
from handlers.private_handler import user_private_router

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sponsors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, group_id INTEGER, link TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT)")
    conn.commit()
    conn.close()

dp = Dispatcher()

dp.include_routers(group_router, user_private_router)



async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    init_db()

print('Бот запущен')
asyncio.run(main())