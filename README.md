
# Kraioko Perm Telegram Bot
**[@kraioko_results_bot](https://t.me/kraioko_results_bot)**

Данный бот предназначен для получения результатов ГИА с сайта Kraioko.

## Возможности
- Просмотр результатов экзаменов;
- Подписка на уведомления об изменении результатов;
- Сохранение анонимности пользователей (используется хеширование telegram id, за исключением подписок на уведомления).

Основные используемые библиотеки: aiogram, sqlite3, BeautifulSoup, requests, asyncio.

Пользовательские команды:
```
/passport <серия и номер паспорта без разделителей> - добавить паспортные данные
/my_passport - просмотр сведений о пользователе
/check - проверить результаты на Kraioko (в текущий момент)
/subscribe - подписаться на уведомления (или отписаться от уведомлений, в замисимости от состояния подписки) об обновлении результатов
```
## Установка (self-hosted)
Для исключительной приватности предлагается инструкция по самостоятельной установке (для Unix-подобных ОС):

1. Клонирование репозитория, настройка виртуального окружения и установка зависимостей;
```bash
git clone https://github.com/gberdyshev/KraiokoPerm_bot.git
cd KraiokoPerm_bot
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r req.txt
```
2. Создание файла конфигурации;
```bash
mkdir db
echo '{"TOKEN" : "<YOUR_TELEGRAM_TOKEN>"}' > db/config.json
```
Получить токен и создать бота необходимо через @BotFather.

3. Запуск;
```bash
python3 bot.py
```
Для опытных пользователей - возможно использование Docker в связке с Jenkins или отдельно.
Настройка некоторых параметров - `func/config.py` в соответствии с комментариями.

Административные команды:
```
/monitor - сведения о времени ответа Kraioko, количестве пользователей, последнем обновлении системы отслеживания
/change_update_interval <время (с)> - изменение интервала обновления системы отслеживания
```