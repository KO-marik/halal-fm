# Telegram DJ Bot для видеочатов

DJ-бот для трансляции музыки в видеочат Telegram-группы с управлением для админа `@maekiz`.

## Файлы проекта:
- `main.py` - Логика бота и PyTgCalls
- `database.py` - База данных SQLite для медиатеки и настроек
- `requirements.txt` - Зависимости Python
- `Dockerfile` - Конфигурация с FFmpeg для деплоя на Render
- `.gitignore` - Исключения Git

## Инструкция по запуску на Render:
1. Загрузите все файлы из архива в ваш GitHub-репозиторий.
2. Перейдите на Render.com -> Создайте **Background Worker**.
3. Выберите среду **Docker**.
4. В разделе **Environment Variables** добавьте:
   - `BOT_TOKEN`: `8990033747:AAEX9JsuwmkpFvpuL-KPNoexL7GgMaeExpY`
   - `ADMIN_USERNAME`: `maekiz`
5. Нажмите **Create Background Worker**.
