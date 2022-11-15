# tg_bot_template

Template for telegram bot on python-telegram-bot

## Переменные окружения:

- `TG_BOT_TOKEN` - токен для телеграмм-бота

## Запуск бота

- `pip install -r requirements.txt`
- `python main.py`

## Установка зависимостей для разработки

- `pip install -r requirements-dev.txt`

## Запуск с помощью Docker

- `docker build -t train:latest .`
- `docker run --name=tictac --env-file={.env} --volume={data_path}:/app/data --restart=always -d train:latest`