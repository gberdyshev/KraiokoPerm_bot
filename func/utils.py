import sqlite3
import hashlib
import random

from func.config import __db_path__
from func.useragents import useragents

# Получение интервала обновления из БД
def get_update_interval() -> int:
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select update_interval from config')
    res = cur.fetchone()
    return int(res[0])

# Получение хеша для id пользователя в Тг
def get_hash_user_id(id) -> str:
    w = str(id).encode(encoding='UTF-8')  
    hash_id = hashlib.sha256(w).hexdigest()
    return hash_id

# Получение паспортных данных из БД
def get_passp_from_user_id(id):
    hash_id = get_hash_user_id(id)
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select passport from users where tlg_id = ?', (hash_id, ))
    res = cur.fetchone()
    if res is None: return 0
    return res[0] # возвращаем паспортные данные

# Получить статус подписки у пользователя
def get_subscribe_status(user_id) -> bool:
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select state from notify where user = ?', (str(user_id), ))
    res = cur.fetchone()
    if res is None: status = False
    else: status = True
    return status

# Получить User-Agent из списка
def get_user_agent() -> str:
    return random.shuffle(useragents)
    
