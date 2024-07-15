import requests
import lxml
import sqlite3

from func.utils import get_user_agent
from func.config import __db_path__
from bs4 import BeautifulSoup

KRAIOKO_URL = 'https://kraioko.perm.ru/?oper=presults'
KRAIOKO_RES_SCRIPT_URL = 'https://kraioko.perm.ru/utils/results/loadstudentresults.php'



# Основная функция проверки результатов по паспортным данным
def kraioko_check(passp):
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': get_user_agent()})
        cur = sqlite3.connect(__db_path__).cursor()
        cur.execute('select computerid from computerid')
        res = cur.fetchone()
        if res is None:
            return 400
        compid_cookies = {'computerid': res[0]}
        r = s.get(KRAIOKO_URL, timeout=7, cookies=compid_cookies)
        compid_cookies |= s.cookies.get_dict()       
        params = {'ds': passp[:4], 'dn':passp[4:], 'rhash': '', 'computerid': res[0]}
        r = s.post(KRAIOKO_RES_SCRIPT_URL, data=params, timeout=7, cookies=compid_cookies)
        if r.status_code != 200:
            return 400
        
        result = r.content
    
        soup = BeautifulSoup(result, 'xml', from_encoding='utf-8')
        msg = soup.find('resultmsg').text
        if msg != 'OK':
            get_computerid_firstrun()
            return kraioko_check(passp)
        k = soup.find('tabletext')
        k = str(k).replace('&lt;', '<').replace('&gt;', '>')

        soup = BeautifulSoup(k, 'lxml')
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

# Функция распаковки результатов из списка
def unpack_results(data) -> str:    
    text = ''
    for row in data:
        subj, mark, status, date = row
        text = text + "\n" + f"📗 <b>{subj}</b>: {mark} ({status}) {date}"
    return text

# Получение ComputerID из cookies при первом запуске
def get_computerid_firstrun():
    s = requests.Session()
    s.headers.update({'User-Agent': get_user_agent()})
    r = s.get(KRAIOKO_URL, timeout=15)
    cookies = s.cookies.get_dict()
    computerid = cookies['computerid']
    conn = sqlite3.connect(__db_path__)
    cur = conn.cursor()
    cur.execute('select computerid from computerid')
    res = cur.fetchone()
    if res is None:
        cur.execute('insert into computerid VALUES (?)', (computerid, ))
    else:
        cur.execute('update computerid set computerid = ?', (computerid, ))
    conn.commit()
    print("Получение ComputerID выполнено успешно")