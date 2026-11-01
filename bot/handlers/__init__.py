from aiogram import Router

from bot.handlers import admin, join_requests, start


def get_routers() -> list[Router]:
    # Порядок важливий: адмінка першою (її кроки мають пріоритет),
    # start останнім — він ловить усе інше і показує меню.
    return [admin.router, join_requests.router, start.router]
