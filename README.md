# 🤖 Бот Кірпіч

Telegram-бот який надсилає посилання на всі соцмережі при старті.

---

## 🚀 Запуск

### 1. Отримай токен
Відкрий [@BotFather](https://t.me/BotFather) → `/newbot` → скопіюй токен

### 2. Встанови залежності
```bash
pip install -r requirements.txt
```

### 3. Налаштуй `.env` файл
Скопіюй `.env.example` → перейменуй у `.env` → встав свої дані:
```
BOT_TOKEN=твій_токен_від_BotFather
INSTAGRAM_URL=https://www.instagram.com/твій_нікнейм
TIKTOK_URL=https://www.tiktok.com/@твій_нікнейм
TELEGRAM_CHANNEL_URL=https://t.me/твій_канал
```

### 4. Запусти бота
```bash
python bot.py
```

---

## 📁 Структура

```
бот Кірпіч/
├── bot.py              # основний файл бота
├── .env                # твої секрети (не ділись!)
├── .env.example        # приклад конфігу
└── requirements.txt    # залежності
```
