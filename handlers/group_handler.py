from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from filters.group_filter import GroupIdFilter
import sqlite3
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from config import chat_id
from bot import bot

group_router = Router()
group_router.message.filter(GroupIdFilter([chat_id]))

class Sms(StatesGroup):
    text = State()

class Sponsor(StatesGroup):
    name = State()
    group_id = State()
    link = State()

class ChangeLink(StatesGroup):
    sponsor_id = State()
    link_change = State()
    group_sponsor_id = State()


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sponsors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, group_id INTEGER, link TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT)")
    conn.commit()
    conn.close()

def back_from_edit():
    buttons = [
        [InlineKeyboardButton(text='↩️Вернуться назад', callback_data='sponsors')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def main_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Спонсоры", callback_data="sponsors"),
        ],
        [
            InlineKeyboardButton(text="Рассылка", callback_data="mail"),
        ],
        [
            InlineKeyboardButton(text="Все пользователи", callback_data="users"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_button_only():
    buttons = [
        [InlineKeyboardButton(text='↩️Вернуться назад', callback_data='menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def sponsors_keyboard():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sponsors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, group_id INTEGER, link TEXT)")
    cursor.execute("SELECT name FROM sponsors")
    data = cursor.fetchall()
    conn.close()
    buttons = [
        [InlineKeyboardButton(text='➕Добавить спонсора', callback_data='add_sponsor')],

        [InlineKeyboardButton(text='↩️Вернуться назад', callback_data='menu')]
    ]

    for sponsor in data:
        buttons.insert(0, [InlineKeyboardButton(text=sponsor[0], callback_data=f'sponsor_{sponsor[0]}')])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sponsor_options(sponsor_name):
    buttons = [
        [InlineKeyboardButton(text='👀Изменить Chat_Id или Group_Id', callback_data=f'edit_sponsor_group_id_{sponsor_name}')],
        [InlineKeyboardButton(text='🔗Изменить ссылку', callback_data=f'edit_sponsor_link_{sponsor_name}')],
        [InlineKeyboardButton(text='🗑Удалить спонсора', callback_data=f'delete_sponsor_{sponsor_name}')],
        [InlineKeyboardButton(text='↩️Вернуться назад', callback_data='sponsors')]

    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_sponsors():
    buttons = [
        [InlineKeyboardButton(text='↩️Вернуться назад', callback_data='sponsors')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@group_router.message(Command('menu'))
async def menu(message: types.Message, state: FSMContext):
    await message.reply('Главное меню', reply_markup=main_keyboard())
    await state.clear()

@group_router.callback_query(F.data == 'menu')
async def menu(callback: types.CallbackQuery):
    await callback.message.edit_text('Главное меню', reply_markup=main_keyboard())

@group_router.callback_query(F.data == 'sponsors')
async def sponsors(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    init_db()
    cursor.execute("SELECT name, link FROM sponsors")
    data = cursor.fetchall()
    conn.close()
    await callback.message.edit_text(f'Все спонсоры:', reply_markup=sponsors_keyboard())

@group_router.callback_query(F.data == 'add_sponsor')
async def add_sponsor(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите имя спонсора', reply_markup=back_to_sponsors())
    await state.set_state(Sponsor.name)


@group_router.message(Sponsor.name, F.text)
async def sponsor_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Sponsor.group_id)
    await message.reply('Введите Group\_id или Chat\_id спонсора\n\n\n_взять ID группового чата: @LeadConverterToolkitBot _\n_взять ID Канала: https://telegramid.lavrynenko.com _', parse_mode='Markdown', reply_markup=back_to_sponsors())


@group_router.message(Sponsor.group_id, F.text)
async def sponsor_group_id(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(group_id=message.text)
        await state.set_state(Sponsor.link)
        await message.reply('Введите ссылку на спонсора без @ \n\n❌@lolz_guru\n✅lolz_guru',  reply_markup=back_to_sponsors())
    else:
        await message.reply('Некорректный Group_id, введите цифры', reply_markup=back_to_sponsors())

@group_router.message(Sponsor.link, F.text)
async def sponsor_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    group_id = data.get('group_id')
    link = message.text
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sponsors (name, group_id, link) VALUES (?, ?, ?)", (name,group_id, link))
    conn.commit()
    conn.close()
    await state.clear()
    await message.reply('Спонсор добавлен', reply_markup=sponsors_keyboard())

@group_router.callback_query(F.data == 'remove_sponsor')
async def remove_sponsor(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM sponsors")
    data = cursor.fetchall()
    conn.close()
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f'remove_{id}')] for id, name in data
    ]
    buttons.append([InlineKeyboardButton(text='↩️Вернуться назад', callback_data='menu')])
    await callback.message.edit_text('Выберите спонсора для удаления:', reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@group_router.callback_query(F.data.startswith('remove_'))
async def confirm_remove_sponsor(callback: types.CallbackQuery):
    sponsor_id = callback.data.split('_')[1]
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sponsors WHERE id = ?", (sponsor_id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text('Спонсор удален', reply_markup=main_keyboard())

@group_router.callback_query(F.data == 'users')
async def users(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users")
    data = cursor.fetchall()
    user_list = ""
    for user in data:
        user_id, username = user
        if username != 'None':
            user_list += f"{user_id} - @{username}\n"
        else:
            user_list += f"{user_id}\n"
    conn.close()
    try:
        await callback.message.edit_text(f'Все пользователи: \n{user_list}', reply_markup=back_button_only())
    except TelegramBadRequest:
        await callback.message.answer(f'Все пользователи: \n{user_list}', reply_markup=back_button_only())

@group_router.callback_query(F.data == 'mail')
async def mail(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Напишите текст рассылки', reply_markup=back_button_only())
    await state.set_state(Sms.text)

@group_router.message(Sms.text, F.text)
async def text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    text = message.text
    await state.clear()
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    data = cursor.fetchall()
    for user in data:
        await bot.send_message(user[0], text)
    conn.close()
    try:
        await message.edit_text('Рассылка выполнена', reply_markup=main_keyboard())
    except TelegramBadRequest:
        await message.answer('Рассылка выполнена', reply_markup=main_keyboard())



@group_router.callback_query(F.data.startswith('sponsor_'))
async def sponsor_options_handler(callback: types.CallbackQuery):
    sponsor_name = callback.data.split("_")[1]
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT link, group_id FROM sponsors WHERE name = ?", (sponsor_name,))
    data = cursor.fetchone()
    link = data[0]
    group_id = data[1]
    conn.close()
    text = (
            f"✨ Выберите действие для спонсора ✨\n\n"
            f"👤 Имя Спонсора: {sponsor_name}\n"
            f"🔗 Ссылка: @{link}\n"
            f"💬 Group ID: {group_id}"
        )
    try:
        await callback.message.edit_text(text=text, reply_markup=sponsor_options(sponsor_name))
    except TelegramBadRequest:
        await callback.message.answer(text=text, reply_markup=sponsor_options(sponsor_name))



@group_router.callback_query(F.data.startswith('delete_sponsor_'))
async def delete_sponsor(callback: types.CallbackQuery):
    sponsor_id = callback.data.split('_')[2]
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sponsors WHERE name = ?", (sponsor_id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text('Спонсор удален', reply_markup=sponsors_keyboard())

@group_router.callback_query(F.data.startswith('edit_sponsor_link_'))
async def edit_sponsor(callback: types.CallbackQuery, state: FSMContext):
    sponsor_id = callback.data.split('_')[3]
    await state.update_data(sponsor_id=sponsor_id)
    await state.set_state(ChangeLink.link_change)
    await callback.message.edit_text('Введите ссылку на спонсора без @ \n\n❌@lolz_guru\n✅lolz_guru',  reply_markup=back_to_sponsors())



@group_router.message(ChangeLink.link_change, F.text)
async def edit_link(message: types.Message, state: FSMContext):
    await state.update_data(link=message.text)
    data = await state.get_data()
    sponsor_id = data['sponsor_id']
    link = message.text
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE sponsors SET link = ? WHERE name = ?", (link, sponsor_id))
    conn.commit()
    conn.close()
    await message.answer(f'Ссылка для спонсора {sponsor_id} изменена', reply_markup=sponsors_keyboard())
    await state.clear()


@group_router.callback_query(F.data.startswith("edit_sponsor_group_id_"))
async def edit_group_id(callback: types.CallbackQuery, state: FSMContext):
    sponsor_id = callback.data.split('_')[4]
    await state.update_data(sponsor_id=sponsor_id)
    await state.set_state(ChangeLink.group_sponsor_id)
    await callback.message.edit_text('Введите Group\_id или Chat\_id спонсора\n\n\n_взять ID группового чата: @LeadConverterToolkitBot _\n_взять ID Канала: https://telegramid.lavrynenko.com _', parse_mode='Markdown', reply_markup=back_to_sponsors())



@group_router.message(ChangeLink.group_sponsor_id, F.text)
async def edit_group_id(message: types.Message, state: FSMContext):
    await state.update_data(group_id=message.text)
    data = await state.get_data()
    sponsor_id = data['sponsor_id']
    group_id = message.text
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE sponsors SET group_id = ? WHERE name = ?", (group_id, sponsor_id))
    conn.commit()
    conn.close()
    await message.answer(f'Группа для спонсора {sponsor_id} изменена', reply_markup=sponsors_keyboard())
    await state.clear()
