import asyncio
import logging
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

__db_path__ = 'db/users.db'
logging.basicConfig(level=logging.INFO)

def load_config():
    """Загрузка конфигурации из JSON"""
    json_config_file = './db/config.json'
    with open(json_config_file, 'r') as file:
        return json.load(file)

jsonconfig = load_config()

bot = Bot(token=jsonconfig['TOKEN'])
dp = Dispatcher()
cooldown_data = dict()


def kraioko_check(passp):
    s = requests.get('https://kraioko.perm.ru/presults/').text
    index_1 = s.find('rhash')
    rhash = s[index_1+7:index_1+7+44]

    params = {'ds': passp[:4], 'dn':passp[4:], 'rhash': rhash}
    r = requests.get('https://kraioko.perm.ru/utils/results/loadstudentresults.php', params=params)
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

    w = str(message.from_user.id).encode(encoding='UTF-8')  
    hash_id = hashlib.sha256(w).hexdigest()
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select passport from users where tlg_id = ?', (hash_id, ))
    res = cur.fetchone()
    if res is None:
        cur.execute('insert into users VALUES (?,?)', (hash_id, command.args))
    else:
        cur.execute('update users set passport = ? where tlg_id = ?', (command.args, hash_id))
    conn.commit()
    conn.close()
    await message.answer("Данные успешно добавлены!")



@dp.message(Command('check'))
async def check(message: types.Message):
    delay = cooldown_data[str(message.from_user.id)] - int(time.time())
    if delay < 60:
        return await message.answer(f"Следующий запрос результатов можно будет выполнить через {60-delay} секунд")
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
    text = ""
    data = kraioko_check(res[0])
    if data is False:
        return await message.answer("Данные не найдены!")
    if data == 400:
        return await message.answer("Kraioko не отвечает.")
    for row in data:
        subj, mark, status, date = row
        text = text + "\n" + f"📗 <b>{subj}</b>: {mark} ({status}) {date}"

    cooldown_data[str(message.from_user.id)] = int(time.time())
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
