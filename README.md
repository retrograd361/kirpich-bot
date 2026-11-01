# Бот Кірпіча — хаб для підписників

Асинхронний Telegram-бот (aiogram 3): меню з усіма соцмережами й донатами,
автоприйом заявок у закритий канал, база підписників, розсилки про стріми, адмінка.

## Що вміє
- **/start** — меню: Kick, TikTok, Instagram, Telegram-канал, Donatello, Монобанка,
  номер картки + кнопка «Скопіювати номер картки».
- **Автоприйом заявок у канал** — бот пише людині меню в особисті (вона потрапляє в базу) і схвалює заявку.
- **/admin** (тільки для `ADMIN_USERNAMES`):
  - 🔴 Стрім почався → Kick / TikTok / обидва → картинка → текст або шаблон → превʼю → розсилка всім;
  - 📢 Новий пост → будь-яке повідомлення + кнопки → превʼю → розсилка;
  - 🔗 Посилання і тексти → змінити будь-яке посилання, картку, привітання, фото привітання;
  - 📊 Статистика; 👀 як бачать меню підписники.
- `/cancel` — вийти з будь-якого кроку адмінки.

## Запуск локально
```bash
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env      # і заповни BOT_TOKEN та ADMIN_USERNAMES
.venv\Scripts\python -m bot
```
⚠️ Один токен = один запущений бот. Перед запуском нового **вимкни старого**, інакше
Telegram видасть помилку `Conflict: terminated by other getUpdates request`.

## Налаштування каналу для автоприйому заявок
1. Додай бота в канал адміністратором з правом **«Додавати підписників / Запрошувати користувачів»**.
2. Посилання-запрошення в канал має бути з увімкненим **«Заявки на вступ»** (Request admin approval).
3. (Необовʼязково) впиши `CHANNEL_ID` у змінні — тоді бот приймає заявки тільки в цей канал.

## Деплой на Railway
1. New Project → Deploy from GitHub repo (або `railway up`).
2. В тому ж проєкті: New → Database → **PostgreSQL**.
3. У сервісі бота → Variables:
   - `BOT_TOKEN`, `ADMIN_USERNAMES`
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
4. Старт-команда береться з `Procfile` (`worker: python -m bot`). Якщо Railway її не підхопить —
   Settings → Deploy → Custom Start Command: `python -m bot`.

## Перевірка
```bash
.venv\Scripts\python -m tests.smoke_test
```
Тест підміняє Telegram фейком і проганяє: меню, 300 одночасних /start, заявку в канал,
доступ до адмінки, анонс стріму з розсилкою (з заблокованими юзерами і flood-limit),
пост з кнопками, зміну посилань, статистику.
На Postgres: `set TEST_DATABASE_URL=postgresql://...` перед запуском.

## Структура
```
bot/
  __main__.py      запуск
  config.py        змінні оточення
  content.py       тексти, посилання за замовчуванням, кнопки меню
  db.py            база (юзери + налаштування)
  menu.py          відправка меню-хабу
  keyboards.py     кнопки
  broadcast.py     фонова розсилка з лімітом швидкості
  middlewares.py   запис юзерів у базу
  filters.py       перевірка адміна
  handlers/        start, join_requests, admin
```
Нова соцмережа в меню = рядок у `DEFAULTS`, `EDITABLE` і `MENU_BUTTONS` у `content.py`.
