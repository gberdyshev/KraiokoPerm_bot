import datetime, time
import sqlite3
import requests

from func.config import __db_path__, __cooldown__, superusers, start_text, load_config, create_tables
from func.utils import get_passp_from_user_id, get_update_interval
from func.kraioko_func import unpack_results, kraioko_check

from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject

router = Router()



@router.message(Command('monitor'))
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
    cur.execute('select unixtime from last_update')
    r = cur.fetchone()
    last_update = (datetime.datetime.fromtimestamp(int(r[0]), datetime.UTC) \
        + datetime.timedelta(hours=5, minutes=0)).strftime('%d-%m-%Y %H:%M:%S')
    await message.answer(f"Kraioko отвечает за {totaltime:.2f} мс\nПользователей: {len(users)}\nС уведомлениями: {len(notifiers)}\n\
        \nПоследнее обновление системы отслеживания: {last_update}")
    
""" @router.message(Command('forced_update'))
async def forced_update(message: types.Message):
    if not (str(message.from_user.id) in superusers):
        return await message.answer("Недостаточно прав для выполнения команды!")
    await check_results()
    await message.answer("[root] Принудительное обновление результатов выполнено") """

@router.message(Command('change_update_interval'))
async def change_update_interval(message: types.Message, command: CommandObject):
    if not (str(message.from_user.id) in superusers):
        return await message.answer("Недостаточно прав для выполнения команды!")
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('update config set update_interval = ?', (int(command.args),))
    conn.commit()
    await message.answer(f"[root] Установлен новый интервал обновления: {int(command.args)} с.")