import asyncio
from secrets import token_hex
import sqlite3
from aiogram import Router, F
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.fsm.context import FSMContext

from database.database import DB_NAME, remove_subscription, update_enabled, update_subscription, get_settings_value, get_user_days
from kb import admin_menu
from states import AdminStates
from handlers.start import bot
from config import config, edit_config_info

admin_ids: list = config["ADMIN_IDS"]

query_router = Router()


async def get_users_and_access_end_time_grant(query: str):
    """Получает пользователей и дату окончания подписки по запросу (поиск по username или tg_id)."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if query is None:
        query = ''
    # Определяем, искать по `tg_id` (число) или `username` (строка)
    if query.isdigit():
        cursor.execute("SELECT username, tg_id, sub_end_date FROM users WHERE tg_id LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT username, tg_id, sub_end_date FROM users WHERE username LIKE ?", (f"%{query}%",))

    users = cursor.fetchall()
    conn.close()

    if not users:
        return []

    # Создаём задачи для вычисления даты окончания подписки
    # tasks = [asyncio.create_task(get_access_end_time(user[1], user[2])) for user in users]
    # descriptions = await asyncio.gather(*tasks)

    results = []
    for user in users:
        random_id = token_hex(2)
        link = "https://telegra.ph/file/94e091455317d26d5c5c1.jpg"
        days_left = get_user_days(user[1])
        description = f"Подписка до: {user[2]}" if days_left > 0 else "Подписка не активирована"

        results.append(InlineQueryResultArticle(
            id=random_id,
            title=f"{user[0]} -- {days_left}",  # username -- tg_id
            description=f"{description}",
            thumbnail_url=link,
            hide_url=True,
            input_message_content=InputTextMessageContent(
                message_text=f"grant {user[1]}",  # Команда для выдачи подписки
                parse_mode="HTML"
            )
        ))

    return results


async def get_users_and_access_end_time_restrict(query: str):
    """Получает пользователей и дату окончания подписки по запросу (поиск по username или tg_id)."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Определяем, искать по `tg_id` (число) или `username` (строка)
    if query is None:
        query = ''
    if query.isdigit():
        cursor.execute("SELECT username, tg_id, sub_end_date FROM users WHERE tg_id LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT username, tg_id, sub_end_date FROM users WHERE username LIKE ?", (f"%{query}%",))

    users = cursor.fetchall()
    conn.close()

    if not users:
        return []

    # Создаём задачи для вычисления даты окончания подписки
    # tasks = [asyncio.create_task(get_access_end_time(user[1], user[2])) for user in users]
    # descriptions = await asyncio.gather(*tasks)
    
    results = []
    for user in users:
        random_id = token_hex(2)
        link = "https://telegra.ph/file/94e091455317d26d5c5c1.jpg"
        days_left = get_user_days(user[1])
        description = f"Подписка до: {user[2]}" if days_left > 0 else "Подписка не активирована"

        results.append(InlineQueryResultArticle(
            id=random_id,
            title=f"{user[0]} -- {days_left}",  # username -- tg_id
            description=f"{description}",
            thumbnail_url=link,
            hide_url=True,
            input_message_content=InputTextMessageContent(
                message_text=f"restrict {user[1]}",  # Команда для выдачи подписки
                parse_mode="HTML"
            )
        ))

    return results


async def get_users_and_access_end_time_enabled(query: str):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Определяем, искать по `tg_id` (число) или `username` (строка)
    if query is None:
        query = ''
    if query.isdigit():
        cursor.execute("SELECT username, tg_id, enabled FROM users WHERE tg_id LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT username, tg_id, enabled FROM users WHERE username LIKE ?", (f"%{query}%",))

    users = cursor.fetchall()
    conn.close()

    if not users:
        return []

    results = []
    for user in users:
        random_id = token_hex(2)
        link = "https://telegra.ph/file/94e091455317d26d5c5c1.jpg"

        results.append(InlineQueryResultArticle(
            id=random_id,
            title=f"{user[0]} -- {user[1]}",  # username -- tg_id
            description=f'{"Включена" if user[2] == 1 else "Отключена"}',
            thumbnail_url=link,
            hide_url=True,
            input_message_content=InputTextMessageContent(
                message_text=f"enabled {user[1]}",  # Команда для выдачи подписки
                parse_mode="HTML"
            )
        ))

    return results


@query_router.inline_query(F.query.startswith("grant") & F.from_user.id.in_(admin_ids))
async def admin_grant_access(iquery: InlineQuery):
    data = iquery.query.split("grant")[-1].strip()
    if data == "":
        data = None
    results = await get_users_and_access_end_time_grant(data)
    await iquery.answer(results, cache_time=1, is_personal=True)


@query_router.inline_query(F.query.startswith("restrict") & F.from_user.id.in_(admin_ids))
async def admin_restrict_access(iquery: InlineQuery):
    data = iquery.query.split("restrict")[-1].strip()
    if data == "":
        data = None
    results = await get_users_and_access_end_time_restrict(data)
    await iquery.answer(results, cache_time=1, is_personal=True)

@query_router.inline_query(F.query.startswith("enabled") & F.from_user.id.in_(admin_ids))
async def admin_enabled_access(iquery: InlineQuery):
    data = iquery.query.split("enabled")[-1].strip()
    if data == "":
        data = None
    results = await get_users_and_access_end_time_enabled(data)
    await iquery.answer(results, cache_time=1, is_personal=True)

@query_router.message(F.via_bot & F.text.startswith("grant"))
async def admin_grant_access(msg: Message, state: FSMContext):
    user_id = int(msg.text.split("grant")[-1].strip())
    data = await state.get_data()
    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.Time)
    await msg.answer(f"✔ Выдача доступа для {user_id}\n\nНапишите на сколько дней выдать подписку")
    
@query_router.message(F.via_bot & F.text.startswith("enabled"))
async def admin_enabled_access(msg: Message, state: FSMContext):
    user_id = int(msg.text.split("enabled")[-1].strip())
    # data = await state.get_data()
    now = update_enabled(user_id)
    await msg.answer(f'✅ Доступ был {"выключен" if now == 0 else "включен"}')
    await bot.send_message(chat_id=user_id, text=f"{'❌ Ваша подписка отключена' if now == 0 else '✔ Ваша подписка включена'}")
    
@query_router.message(AdminStates.Time)
async def admin_grant_access_time(msg: Message, state: FSMContext):
    time = int(msg.text)
    data = await state.get_data()
    user_id = data['user_id']
    update_subscription(user_id, time)
    await msg.answer("✔ Доступ успешно выдан!")

    try:
        await bot.send_message(chat_id=user_id, text=f'✔ Вам выдан доступ к боту на {time} дней!')
    except:
        pass
    await state.clear()

@query_router.message(F.via_bot & F.text.startswith("restrict"))
async def restrict_access(msg: Message, state: FSMContext):
    user_id = int(msg.text.replace("restrict", ""))
    remove_subscription(user_id)
    await msg.answer("✔ Доступ успешно закрыт!", reply_markup=admin_menu())
    try:
        await bot.send_message(chat_id=user_id, text='❌ У вас закрыли доступ!')
    except:
        pass

# UPD

async def get_users_and_admins(query: str):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Определяем, искать по `tg_id` (число) или `username` (строка)
    if query is None:
        query = ''
    if query.isdigit():
        cursor.execute("SELECT username, tg_id FROM users WHERE tg_id LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT username, tg_id FROM users WHERE username LIKE ?", (f"%{query}%",))

    users = cursor.fetchall()
    conn.close()

    if not users:
        return []

    results = []
    for user in users:
        random_id = token_hex(2)
        link = "https://telegra.ph/file/94e091455317d26d5c5c1.jpg"
        results.append(InlineQueryResultArticle(
            id=random_id,
            title=f"{user[0]} -- {user[1]}",  # username -- tg_id
            description=f'{"Админ" if user[1] in admin_ids else "Юзер"}',
            thumbnail_url=link,
            hide_url=True,
            input_message_content=InputTextMessageContent(
                message_text=f"admin {user[1]}",  # Команда для выдачи подписки
                parse_mode="HTML"
            )
        ))
    return results

@query_router.inline_query(F.query.startswith("admin") & F.from_user.id.in_(admin_ids))
async def admin_enabled_access(iquery: InlineQuery):
    data = iquery.query.split("admin")[-1].strip()
    if data == "":
        data = None
    results = await get_users_and_admins(data)
    await iquery.answer(results, cache_time=1, is_personal=True)

@query_router.message(F.via_bot & F.text.startswith("admin"))
async def update_admins(msg: Message, state: FSMContext):
    user_id = int(msg.text.split("admin")[-1].strip())
    if user_id in admin_ids:
        admin_ids.remove(user_id)
        config["ADMIN_IDS"] = admin_ids
        edit_config_info(config)
        admin_status = False
    else:
        admin_ids.append(user_id)
        config["ADMIN_IDS"] = admin_ids
        edit_config_info(config)
        admin_status = True
    
    await msg.answer(f'✅ Права админа были {"забраны" if not admin_status else "выданы"}')
    await bot.send_message(chat_id=user_id, text=f"{'❌ У вас забрали права администратора' if not admin_status else '✔ Вам выданы права администратора'}")