# Журнал сесій

## 2026-11-01
- Старого коду в папці не було — бота написано з нуля на aiogram 3 + SQLAlchemy async.
- Зроблено: меню-хаб, автоприйом заявок у канал, база юзерів, /admin (стрім з картинкою,
  пост, налаштування, статистика), фонова розсилка з лімітом.
- Перевірено smoke-тестом з фейковим Telegram на SQLite і на справжньому Postgres (Docker) — 22/22.
- Гілка: `feature/async-bot`, не змерджено в `main`, не запушено.
- Залишилось: подивитись старий бот на Railway (чи є там база юзерів для переносу),
  вирішити хостинг, отримати токен і юзернейми адмінів, налаштувати канал, задеплоїти.
- Аудит старого бота на Railway (docs/old-bot-audit-2026-11-01.md): бот уже був на aiogram,
  справжня причина збоїв — дві копії з одним токеном (TelegramConflictError) + привітання
  після схвалення заявки. Бази юзерів не було. Railway на Trial (~18 днів).
- railway.json замінено на Procfile (config-as-code на Railway застарів).
- З дозволу користувача зупинено (Remove) деплой-дубль у Railway-проєкті kind-education.
  У discerning-sparkle о 15:19 UTC — "Connection established", конфлікти припинились.
  Сервіс kind-education лишився (без активного деплою), але все ще підключений до GitHub
  з автодеплоєм — наступний push у main знову його запустить.
- gh залогінений як voicemakerbot-sketch: до retrograd361/kirpich-bot є лише read, push немає.
- Користувач отримав write-доступ до retrograd361/kirpich-bot (акаунт voicemakerbot-sketch).
  Локальне репо підвʼязане до origin; новий бот закомічений у `feature/async-bot` ПОВЕРХ історії
  старого бота (стара локальна гілка перейменована в `draft/async-bot`). Нічого не запушено.
  План деплою — docs/deploy-plan-2026-11-01.md.
- Тест на @vasyl_my_bot: 21 апдейт, без помилок. Користувач сам додав у discerning-sparkle
  Postgres (з volume) і змінні DATABASE_URL (посилання на Postgres) та ADMIN_USERNAMES (3 адміни).
- `feature/async-bot` запушено на GitHub (з дозволу). У main ще НЕ змерджено.
- kind-education: вимкнено автодеплой з GitHub (Auto deploy is disabled), щоб merge у main не оживив дубль.
