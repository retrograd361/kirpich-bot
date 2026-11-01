# План деплою нового бота — 2026-11-01

Railway автоматично деплоїть гілку `main` репо `retrograd361/kirpich-bot` у проєкт `discerning-sparkle`.
Тому порядок важливий: спершу інфраструктура, потім код.

## Кроки
1. **Тест на живому Telegram** (рекомендовано): створити в @BotFather тестового бота,
   вписати його токен у локальний `.env`, запустити `python -m bot`, пройти /start і /admin.
   Прод-бот при цьому не зачіпається (інший токен).
2. **kind-education** — відключити від GitHub (Settings → Source → Disconnect) або видалити проєкт,
   інакше push у main запустить його знову → конфлікт.
3. **discerning-sparkle** — додати PostgreSQL (New → Database → PostgreSQL).
4. **Змінні сервісу worker:**
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
   - `ADMIN_USERNAMES` = юзернейми адмінів
   - `CHANNEL_ID` — необовʼязково
   - старі `*_URL` новому боту не потрібні (посилання в коді + /admin), можна лишити.
5. Тариф: Trial закінчується (~18 днів) → перейти на Hobby ($5).
6. Push `feature/async-bot` → merge у `main` (лише після "можна в main" + перепитування) → push `main`.
7. Перевірити логи деплою, /start, /admin, заявку в канал.

## Відкат
Якщо щось не так — у Railway на попередньому деплої «Redeploy» (старий bot.py), або `git revert` у main.

## Статус
- [x] Код у гілці `feature/async-bot` поверх історії старого бота (локально, не запушено)
- [ ] Кроки 1–7
