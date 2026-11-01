"""Тексти, посилання і кнопки меню.

Значення тут — це ДЕФОЛТИ. Адмін може змінити будь-яке з них через /admin,
тоді нове значення зберігається в БД і має пріоритет.
"""
from dataclasses import dataclass

DEFAULTS: dict[str, str] = {
    "kick": "https://kick.com/kirpich-7",
    "tiktok": "https://www.tiktok.com/@kirpichnik7",
    "instagram": "https://www.instagram.com/danya_kirpichnik7",
    "telegram": "https://t.me/+deEhcg5BZvFlMzZi",
    "donatello": "https://donatello.to/DanielKyrpychnyk",
    "monobank": "https://send.monobank.ua/jar/rpRzAmNiq",
    "card": "4874 1000 3461 1692",
    "welcome_text": (
        "👋 Всім привіт, на звʼязку <b>Кірпіч</b>!\n\n"
        "Приєднуйтесь до моїх соцмереж — там буде 🔥 двіж!"
    ),
    "welcome_photo": "",  # file_id картинки; порожньо = без картинки
    "stream_text": "🔴 <b>Кірпіч вже на стрімі!</b>\n\nЗалітай, буде 🔥 двіж!",
}


@dataclass(frozen=True)
class SettingMeta:
    title: str
    kind: str  # "url" | "text" | "photo" | "plain"


# Що показуємо в /admin → Налаштування (порядок = порядок кнопок)
EDITABLE: dict[str, SettingMeta] = {
    "kick": SettingMeta("🟢 Kick", "url"),
    "tiktok": SettingMeta("🎵 TikTok", "url"),
    "instagram": SettingMeta("📸 Instagram", "url"),
    "telegram": SettingMeta("✈️ Telegram канал", "url"),
    "donatello": SettingMeta("💸 Donatello", "url"),
    "monobank": SettingMeta("🏦 Монобанка", "url"),
    "card": SettingMeta("💳 Номер картки", "plain"),
    "welcome_text": SettingMeta("👋 Текст привітання", "text"),
    "welcome_photo": SettingMeta("🖼 Фото привітання", "photo"),
    "stream_text": SettingMeta("🔴 Шаблон тексту стріму", "text"),
}


@dataclass(frozen=True)
class MenuButton:
    key: str          # ключ посилання в DEFAULTS / settings
    text: str
    row: int          # кнопки з однаковим row стають в один рядок
    style: str | None = None  # "success" / "primary" / "danger" — колір кнопки


# Головне меню. Щоб додати нову соцмережу: додай посилання в DEFAULTS,
# в EDITABLE і рядок сюди. Кнопки з порожнім посиланням автоматично ховаються.
MENU_BUTTONS: list[MenuButton] = [
    MenuButton("kick", "🟢 Стріми на Kick", row=0, style="success"),
    MenuButton("instagram", "📸 Instagram", row=1),
    MenuButton("tiktok", "🎵 TikTok", row=1),
    MenuButton("telegram", "✈️ Telegram канал", row=2),
    MenuButton("donatello", "💸 Підтримати донатом (Donatello)", row=3, style="primary"),
    MenuButton("monobank", "🏦 Підтримати донатом (Монобанка)", row=4, style="primary"),
]

CARD_BLOCK = "💳 Підтримати донатом на карту можна сюди:\n<code>{card}</code>"
MENU_FOOTER = "⬇️ Обирай де зустрінемось:"

# Платформи для анонсу стріму
STREAM_PLATFORMS: dict[str, tuple[str, ...]] = {
    "kick": ("kick",),
    "tiktok": ("tiktok",),
    "both": ("kick", "tiktok"),
}
