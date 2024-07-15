import asyncio
import requests
import lxml
import sqlite3
import hashlib
import json
import time
import datetime

from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject

from func.config import __db_path__, __cooldown__, superusers, start_text, load_config, create_tables
from func.kraioko_func import kraioko_check, unpack_results, get_computerid_firstrun
from func.utils import get_update_interval, get_hash_user_id, get_passp_from_user_id, get_subscribe_status

from handlers import admin


cooldown_data = dict()
cooldown_subscribe = dict()

bot = Bot(token=load_config()['TOKEN'])
dp = Dispatcher()



async def check_results():
    notify_users = []
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select * from notify')
    res = cur.fetchall()
    for row in res:
        user_id, state, last_len, message_id, last_hash = row
        passp = get_passp_from_user_id(user_id)
        if passp != 0:
            data = kraioko_check(passp)
            w = str(data).encode(encoding='UTF-8')  
            hash_res = hashlib.sha256(w).hexdigest()
            if data != False and data != 400:
                if last_hash != hash_res:
                    cur.execute('update notify set last_hash = ? where user = ?', (hash_res, user_id))
                    conn.commit()
                    text_res = unpack_results(data)
                    await bot.send_message(chat_id=message_id, text="✅ Изменения в результатах!"+ text_res, parse_mode=ParseMode.HTML)
        await asyncio.sleep(1)
    cur.execute('update last_update set unixtime = ?', (int(time.time()), ))
    conn.commit()

async def periodic(interval):
    while True:
        await check_results()
        interval = get_update_interval()
        await asyncio.sleep(interval)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    buttons = [[types.KeyboardButton(text='/check')]]
    kb = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer(start_text, reply_markup=kb)


@dp.message(Command('passport'))
async def passport(message: types.Message, command: CommandObject):
    if command.args is None:
        return await message.answer("Укажите номер и серию паспорта без разделителей! Например: /passport 5700123456")
    if len(command.args) != 10:
        return await message.answer("Проверьте корректность введенных данных!")

    res = get_passp_from_user_id(message.from_user.id)
    hash_id = get_hash_user_id(message.from_user.id)
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    if res == 0:
        cur.execute('insert into users VALUES (?,?)', (hash_id, command.args))
    else:
        cur.execute('update users set passport = ? where tlg_id = ?', (command.args, hash_id))
    conn.commit()
    conn.close()
    if get_subscribe_status(message.from_user.id):
        await subscribe(message, False)
        return await message.answer("Обновлены паспортные данные. Подписка на уведомления отлючена. Включить снова /subscribe")

    await message.answer("Данные успешно добавлены!")

@dp.message(Command('my_passport'))
async def my_passport(message: types.Message):
    w = str(message.from_user.id).encode(encoding='UTF-8')  
    hash_id = hashlib.sha256(w).hexdigest()
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select passport from users where tlg_id = ?', (hash_id, ))
    res = cur.fetchone()
    if res is None:
        return await message.answer("Вы еще не ввели паспортные данные!")
    status = get_subscribe_status(message.from_user.id)
    await message.answer(f"Пользователь: {message.from_user.full_name}\nПаспорт: {res[0]}\nПодписка: {status}")

@dp.message(Command('subscribe'))
async def subscribe(message: types.Message, cooldown=True):
    if str(message.from_user.id) in cooldown_subscribe and cooldown is True:
        delay = int(time.time()) - cooldown_subscribe[str(message.from_user.id)]
        if delay < __cooldown__:
            return await message.answer(f"Следующие действия с подпиской можно будет выполнить через {__cooldown__-delay} с.")
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    user_id = message.from_user.id
    cur.execute('select state from notify where user = ?', (user_id, ))
    res = cur.fetchone()
    if res is None or res[0] == 0:      
        doc = get_passp_from_user_id(user_id)
        if doc == 0: 
            return await message.answer("Вы еще не ввели паспортные данные!")
        data = kraioko_check(doc)
        if data == 400: 
            return message.answer("На текущий момент нет возможности подписаться на уведомления!")
        w = str(data).encode(encoding='UTF-8')  
        hash_res = hashlib.sha256(w).hexdigest()
        cur.execute('insert into notify VALUES (?,?,?,?,?)', (user_id, 1, 0, str(message.chat.id), hash_res))
        await message.answer("Вы успешно подписались на уведомления!")
    else:
        cur.execute('delete from notify where user = ?', (user_id, ))
        await message.answer("Вы успешно отписались от уведомлений!")
    if cooldown:
        cooldown_subscribe[str(message.from_user.id)] = int(time.time())
    conn.commit()
    

@dp.message(Command('check'))
async def check(message: types.Message):
    if str(message.from_user.id) in cooldown_data:
        delay = int(time.time()) - cooldown_data[str(message.from_user.id)]
        if delay < __cooldown__:
            return await message.answer(f"Следующий запрос результатов можно будет выполнить через {__cooldown__-delay} с.")
    cooldown_data[str(message.from_user.id)] = int(time.time()) 

    button_check = types.KeyboardButton(text='/check')
    kb = types.ReplyKeyboardMarkup(keyboard=[[button_check]], resize_keyboard=True)
    w = str(message.from_user.id).encode(encoding='UTF-8')  
    hash_id = hashlib.sha256(w).hexdigest()
    
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select passport from users where tlg_id = ?', (hash_id, ))
    res = cur.fetchone()
    if res is None:
        return await message.answer("Данные вашего паспорта не найдены. Добавьте их командой /passport")
    text = f"📖·<b>Результаты</b>·\n"
    data = kraioko_check(res[0])
    if data is False:
        return await message.answer("Данные не найдены!")
    if data == 400:
        return await message.answer("Kraioko не отвечает.")
    text = text + unpack_results(data)
    #w = str(data).encode(encoding='UTF-8')  
    #hash_id = hashlib.sha256(w).hexdigest()
    #print(hash_id)

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.message(Command('refusal'))
async def refusal(message: types.Message):
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    user_id = message.from_user.id
    hash_user_id = get_hash_user_id(user_id)
    cur.execute('delete from notify where user = ?', (user_id, ))
    cur.execute('delete from users where tlg_id = ?', (hash_user_id, ))
    conn.commit()
    await message.answer("Ваши паспортные данные были удалены из базы данных.")
    



async def main():
    dp.include_router(admin.router)
    interval = get_update_interval()
    task = asyncio.create_task(periodic(interval))
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен")
    await dp.start_polling(bot)
    



if __name__ == "__main__":
    create_tables()
    get_computerid_firstrun()
    asyncio.run(main())
