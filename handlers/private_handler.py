from aiogram import types, F, Router
from bot import bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import requests
import re
import sqlite3
from config import api, admin_us

# Initialize the bot and router
user_private_router = Router()

def keyboard():
    buttons = [
        [InlineKeyboardButton(text="Связь с админом", url=f'https://t.me/{admin_us}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Function to download video from the new API
def download(url):
    api_url = "https://tiktok-video-no-watermark2.p.rapidapi.com/"
    payload = {
        "url": url,
        "hd": "1"
    }
    headers = {
        "x-rapidapi-key": api,  # Replace with your actual RapidAPI key
        "x-rapidapi-host": "tiktok-video-no-watermark2.p.rapidapi.com"
    }
    
    response = requests.post(api_url, data=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'play' in data['data']:
            return data['data']['play']
    else:
        print("Failed to fetch video")  # Debugging: Print the error details
    
    return None

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sponsors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, group_id INTEGER, link TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT)")
    conn.commit()
    conn.close()



# Function to create the subscription keyboard
def sub_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Готово", callback_data="check_subscription"),
        ],
    ]
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, link FROM sponsors")
    data = cursor.fetchall()
    conn.close()
    for groups in data:
        buttons.insert(0, [InlineKeyboardButton(text="Подписаться", url=f'https://t.me/{groups[1]}')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Function to check if a user is subscribed to the channel
async def is_subscribed(user_id):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT group_id FROM sponsors")
    data = cursor.fetchall()
    
    conn.close()
    
    for group_id in data:

        member = await bot.get_chat_member(group_id[0], user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            return False
    return True

#

@user_private_router.message(Command('start'))
async def send_welcome(message: types.Message):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    init_db()
    conn.commit()
    conn.close()
    await message.reply(f"Привет! Чтобы скачать видео, просто отправь ссылку на видео TikTok.\nРеклама/Добавление спонсоров - @{admin_us}", reply_markup=keyboard())

@user_private_router.message(F.text)
async def process(message: types.Message):
    user_id = message.from_user.id
    
    # Always prompt the user to subscribe when they first interact with the bot
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    init_db()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        await message.reply("Вы не подписаны на каналы спонсоров.", reply_markup=sub_keyboard())
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, message.from_user.username or '0'))
        conn.commit()
        conn.close()
    else:
        if re.match(r'https://[a-zA-Z]+\.tiktok\.com/', message.text):
            m = await message.reply('Ожидайте..')
            video_url = download(message.text)
            if video_url:
                await bot.delete_message(message.chat.id, m.message_id)
                await message.answer_video(video_url, caption='Готово!')
                conn.close()
            else:
                await bot.delete_message(message.chat.id, m.message_id)
                await message.reply('Произошла ошибка при скачивании видео.')
                conn.close()

@user_private_router.callback_query(F.data == 'check_subscription')
async def process_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    if await is_subscribed(user_id):
        await bot.send_message(user_id, "Спасибо за подписку! Теперь вы можете отправить ссылку на видео TikTok.")
        # Update the user record to mark subscription verified
        conn = sqlite3.connect('database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (callback_query.from_user.username or '0', user_id))
        conn.commit()
        conn.close()
    else:
        await bot.send_message(user_id, "Вы все еще не подписаны на каналы спонсоров.", reply_markup=sub_keyboard())
