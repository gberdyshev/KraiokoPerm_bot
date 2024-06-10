import asyncio
import requests
import lxml
import sqlite3
import hashlib
import json
import time

from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject

__db_path__ = './db/users.db'
__cooldown__ = 60
superusers = ['847454186']
#logging.basicConfig(level=logging.INFO)

def load_config():
    """Загрузка конфигурации из JSON"""
    json_config_file = './db/config.json'
    with open(json_config_file, 'r') as file:
        return json.load(file)

jsonconfig = load_config()

bot = Bot(token=jsonconfig['TOKEN'])
dp = Dispatcher()
cooldown_data = dict()
cooldown_subscribe = dict()


def kraioko_check(passp):
    try:
        s = requests.get('https://kraioko.perm.ru/presults/', timeout=7).text
        index_1 = s.find('rhash')
        rhash = s[index_1+7:index_1+7+44]

        params = {'ds': passp[:4], 'dn':passp[4:], 'rhash': rhash}
        r = requests.get('https://kraioko.perm.ru/utils/results/loadstudentresults.php', params=params, timeout=7)
        if r.status_code != 200:
            return 400
        result = r.content
    
        soup = BeautifulSoup(result, 'lxml')
        data = []
        table = soup.find('table')
        if table is None:
            return False
        rows = table.find_all('tr')

        for row in range(1, len(rows)):
            new_row = []
            for td in rows[row].find_all('td'):
                new_row.append(td.text.strip())
            if len(new_row) > 1:
                data.append(new_row)
        return data
    except:
        return 400

def unpack_results(data) -> str:
    text = ''
    for row in data:
        subj, mark, status, date = row
        text = text + "\n" + f"📗 <b>{subj}</b>: {mark} ({status}) {date}"
    return text

def get_hash_user_id(id):
    w = str(id).encode(encoding='UTF-8')  
    hash_id = hashlib.sha256(w).hexdigest()
    return hash_id

def get_passp_from_user_id(id):
    hash_id = get_hash_user_id(id)
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select passport from users where tlg_id = ?', (hash_id, ))
    res = cur.fetchone()
    if res is None: return 0
    return res[0] # возвращаем паспортные данные

async def check_results():
    notify_users = []
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select * from notify')
    res = cur.fetchall()
    for row in res:
        user_id, state, last_len, message_id = row
        passp = get_passp_from_user_id(user_id)
        if passp != 0:
            data = kraioko_check(passp)
            if data != False and data != 400:
                if len(data) != last_len:
                    cur.execute('update notify set last_len = ? where user = ?', (len(data), user_id))
                    conn.commit()
                    text_res = unpack_results(data)
                    await bot.send_message(chat_id=message_id, text="✅ Изменения в результатах!"+ text_res, parse_mode=ParseMode.HTML)
                    
    
                    

async def periodic(interval):
    while True:
        await check_results()
        await asyncio.sleep(interval)
        print("Запрос выполнен")
        


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    helps = """Приветствую!
Это бот для получения результатов с Kraioko.
Перед началом использования необходимо добавить номер и серию паспорта командой /passport XXXXXXXXXX
Затем для получения результатов используется команда /check"""
    buttons = [[types.KeyboardButton(text='/check')]]
    kb = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer(helps, reply_markup=kb)


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
    cur.execute('select state from notify where user = ?', (str(message.from_user.id), ))
    res2 = cur.fetchone()
    if res2 is None: status = False
    else: status = True
    await message.answer(f"Пользователь: {message.from_user.full_name}\nПаспорт: {res[0]}\nПодписка: {status}")

@dp.message(Command('subscribe'))
async def subscribe(message: types.Message):
    if str(message.from_user.id) in cooldown_subscribe:
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
        if doc == 0: return await message.answer("Вы еще не ввели паспортные данные!")
        data = kraioko_check(doc)
        if data == 400 or data == False: return message.answer("На текущий момент нет возможности подписаться на уведомления!")

        cur.execute('insert into notify VALUES (?,?,?,?)', (user_id, 1, len(data), str(message.chat.id)))
        await message.answer("Вы успешно подписались на уведомления!")
    else:
        cur.execute('delete from notify where user = ?', (user_id, ))
        await message.answer("Вы успешно отписались от уведомлений!")

    cooldown_subscribe[str(message.from_user.id)] = int(time.time())
    conn.commit()
    





@dp.message(Command('check'))
async def check(message: types.Message):
    if str(message.from_user.id) in cooldown_data:
        delay = int(time.time()) - cooldown_data[str(message.from_user.id)]
        if delay < __cooldown__:
            return await message.answer(f"Следующий запрос результатов можно будет выполнить через {__cooldown__-delay} с.")
    button_check = types.KeyboardButton(text='/check')
    kb = types.ReplyKeyboardMarkup(keyboard=[[button_check]], resize_keyboard=True)
    w = str(message.from_user.id).encode(encoding='UTF-8')  
    hash_id = hashlib.sha256(w).hexdigest()
    
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select passport from users where tlg_id = ?', (hash_id, ))
    res = cur.fetchone()
    if res is None:
        await message.answer("Данные вашего паспорта не найдены. Добавьте их командой /passport")
    text = f"📖·<b>Результаты</b>·\n"
    data = kraioko_check(res[0])
    if data is False:
        return await message.answer("Данные не найдены!")
    if data == 400:
        return await message.answer("Kraioko не отвечает.")
    text = text + unpack_results(data)

    cooldown_data[str(message.from_user.id)] = int(time.time()) 
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.message(Command('monitor'))
async def monitor(message: types.Message):
    if not (str(message.from_user.id) in superusers):
        return await message.answer("Недостаточно прав для выполнения команды!")
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select * from users')
    users = cur.fetchall()
    cur.execute('select * from notify')
    notifiers = cur.fetchall()
    resp = requests.get('https://kraioko.perm.ru', timeout=7)
    totaltime = resp.elapsed.total_seconds()*1000
    await message.answer(f"Kraioko отвечает за {totaltime} мс\nПользователей: {len(users)}\nС уведомлениями: {len(notifiers)}\n")
    




async def main():
    task = asyncio.create_task(periodic(600))
    await dp.start_polling(bot)

def create_tables():
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('CREATE TABLE if not exists users (tlg_id TEXT, passport TEXT)')
    cur.execute('CREATE TABLE if not exists notify (user TEXT, state INTEGER, last_len INTEGER, message_id TEXT, PRIMARY KEY(user))')
    conn.commit()

if __name__ == "__main__":
    create_tables()
    asyncio.run(main())
