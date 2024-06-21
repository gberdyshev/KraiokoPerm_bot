import json
import sqlite3

__db_path__ = './db/users.db' # Путь до файла с БД
__cooldown__ = 60 # КД для команд подписки и проверки результато
superusers = ['847454186'] # Пользователи-администраторы, имеющие доступ к административным командам
__json_config_file__ = './db/config.json' # Путь до файла с токеном
start_text = """Приветствую!
Это бот для получения результатов с Kraioko.
Перед началом использования необходимо добавить номер и серию паспорта командой /passport XXXXXXXXXX
Затем для получения результатов используется команда /check

/subscribe - Подписаться на уведомления об изменении результатов""" # Приветственный текст (для команды /start)



# Загрузка токена из JSON
def load_config():  
    json_config_file = __json_config_file__
    with open(json_config_file, 'r') as file:
        return json.load(file)

# Создание таблиц в БД
def create_tables():
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('CREATE TABLE if not exists users (tlg_id TEXT, passport TEXT)')
    cur.execute('CREATE TABLE if not exists notify (user TEXT, state INTEGER, last_len INTEGER, message_id TEXT, last_hash TEXT, PRIMARY KEY(user))')
    cur.execute('CREATE TABLE if not exists last_update (unixtime text)')
    cur.execute('select * from last_update')
    if cur.fetchone() is None:
        cur.execute('insert into last_update VALUES (0)')
    cur.execute('CREATE TABLE if not exists config (update_interval INTEGER)')
    cur.execute('select update_interval from config')
    if cur.fetchone() is None:
        cur.execute('insert into config VALUES (600)')
    conn.commit()