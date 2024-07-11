import requests
import lxml

from bs4 import BeautifulSoup

KRAIOKO_URL = 'https://kraioko.perm.ru/presults/'
KRAIOKO_RES_SCRIPT_URL = 'https://kraioko.perm.ru/utils/results/loadstudentresults.php'

# Основная функция проверки результатов по паспортным данным
def kraioko_check(passp):
    try:
        s = requests.get(KRAIOKO_URL, timeout=7).text
        index_1 = s.find('rhash')
        rhash = s[index_1+7:index_1+7+44]

        params = {'ds': passp[:4], 'dn':passp[4:], 'rhash': rhash}
        r = requests.get(KRAIOKO_RES_SCRIPT_URL, params=params, timeout=7)
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

# Функция распаковки результатов из списка
def unpack_results(data) -> str:    
    text = ''
    for row in data:
        subj, mark, status, date = row
        text = text + "\n" + f"📗 <b>{subj}</b>: {mark} ({status}) {date}"
    return text