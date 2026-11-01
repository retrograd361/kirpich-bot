"""Інлайн-клавіатури."""
from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup

from bot.content import EDITABLE, MENU_BUTTONS


def main_menu(settings: dict[str, str]) -> InlineKeyboardMarkup:
    rows: dict[int, list[InlineKeyboardButton]] = {}
    for b in MENU_BUTTONS:
        url = settings.get(b.key)
        if not url:
            continue  # порожнє посилання = кнопку ховаємо
        rows.setdefault(b.row, []).append(InlineKeyboardButton(text=b.text, url=url, style=b.style))
    keyboard = [rows[r] for r in sorted(rows)]
    if settings.get("card"):
        # кнопка, яка копіює номер картки в буфер обміну
        keyboard.append([InlineKeyboardButton(
            text="💳 Скопіювати номер картки",
            copy_text=CopyTextButton(text=settings["card"].replace(" ", "")),
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def tiktok_live_url(tiktok_url: str) -> str:
    tiktok_url = tiktok_url.rstrip("/")
    return tiktok_url if tiktok_url.endswith("/live") else tiktok_url + "/live"


def stream_buttons(platforms: tuple[str, ...], settings: dict[str, str]) -> InlineKeyboardMarkup:
    row = []
    if "kick" in platforms and settings.get("kick"):
        row.append(InlineKeyboardButton(text="🟢 Дивитись на Kick", url=settings["kick"], style="success"))
    if "tiktok" in platforms and settings.get("tiktok"):
        row.append(InlineKeyboardButton(text="🎵 Дивитись у TikTok", url=tiktok_live_url(settings["tiktok"])))
    return InlineKeyboardMarkup(inline_keyboard=[[b] for b in row])


def parse_buttons(text: str) -> InlineKeyboardMarkup | None:
    """Рядки виду "Назва | https://посилання" -> кнопки (кожна в окремому рядку)."""
    keyboard = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        title, url = (part.strip() for part in line.split("|", 1))
        if title and url.startswith(("http://", "https://", "tg://")):
            keyboard.append([InlineKeyboardButton(text=title, url=url)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None


def _btn(text: str, data: str, style: str | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data, style=style)


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("🔴 Стрім почався", "adm:stream", "danger")],
        [_btn("📢 Новий пост", "adm:post")],
        [_btn("🔗 Посилання і тексти", "adm:settings"), _btn("📊 Статистика", "adm:stats")],
        [_btn("👀 Як бачать підписники", "adm:preview")],
        [_btn("✖️ Закрити", "adm:close")],
    ])


def back_to_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("⬅️ Назад", "adm:menu")]])


def stream_platforms() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("🟢 Kick", "stream:kick"), _btn("🎵 TikTok", "stream:tiktok")],
        [_btn("🔥 Kick + TikTok", "stream:both")],
        [_btn("❌ Скасувати", "adm:cancel")],
    ])


def cancel_only() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("❌ Скасувати", "adm:cancel")]])


def skip(data: str, text: str = "⏭ Пропустити") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn(text, data)], [_btn("❌ Скасувати", "adm:cancel")]])


def confirm_broadcast(count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn(f"✅ Розіслати ({count} чол.)", "bc:go", "success")],
        [_btn("❌ Скасувати", "adm:cancel")],
    ])


def settings_list(settings: dict[str, str]) -> InlineKeyboardMarkup:
    keyboard = []
    for key, meta in EDITABLE.items():
        mark = "" if settings.get(key) else " (порожньо)"
        keyboard.append([_btn(meta.title + mark, f"set:{key}")])
    keyboard.append([_btn("⬅️ Назад", "adm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
