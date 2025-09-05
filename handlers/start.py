import asyncio
import json
import sqlite3
from aiogram import Bot, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.fsm.context import FSMContext
from validators.validators import validate_time_interval, validate_secounds, validate_login, validate_float, validate_timezone, validate_koef_interval
from database.database import DB_NAME, add_user, get_user_days, update_settings, get_settings_value, add_channel, get_channels_list, udpate_channels, delete_channel, add_match, get_matches, get_allowed_users, get_allowed_channels
from parser.parser import parse, login_allbestbets, get_sub_status_allbestbets
from kb import *
from states import AdminStates
from config import *
from logger import logger

BOT_TOKEN = config["BOT_TOKEN"]
url_oplata = config["URL_OPLATA"]

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
handlers_router = Router()

parser_task: asyncio.Task = None

@handlers_router.message(CommandStart())
async def start_handler(message: Message):
    """Обработчик команды /start"""
    add_user(message.from_user.id, message.from_user.username,
             message.from_user.full_name)
    text = "👋 Привет! Я бот для ставок. Используй кнопки ниже."
    await message.answer(text, reply_markup=main_menu())


@handlers_router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    """Проверка подписки"""
    days = get_user_days(callback.from_user.id)
    text = f"📅 Оставшиеся дни подписки: {days}" if days > 0 else "⛔ Подписка не активирована!"
    try:
        await callback.message.edit_text(text, reply_markup=main_menu())
    except:
        pass


@handlers_router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    """Панель администратора"""
    admin_ids = config["ADMIN_IDS"]
    await state.clear()
    if message.from_user.id in admin_ids:
        await message.answer("🔧 Панель управления", reply_markup=admin_menu())
    else:
        await message.answer("⛔ У вас нет доступа.")


@handlers_router.callback_query(F.data == "send")
async def sending(call, state):
    await state.set_state(AdminStates.Sending)
    await call.message.edit_text("👇 Отправьте сообщения для рассылки:")


@handlers_router.message(AdminStates.Sending)
async def sending_finish(msg, state):
    await msg.answer("⌛ Рассылаю...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor = conn.execute("SELECT tg_id FROM users")
    users = cursor.fetchall()
    for user in users:
        try:
            await bot.copy_message(user[0], msg.from_user.id, msg.message_id)
            logger.info(f"Отправлено юзеру {user[0]}...")
        except Exception as e:
            logger.error(e)
        await asyncio.sleep(3)
    await msg.answer("✅ Разослано!...")
    await state.clear()


@handlers_router.callback_query(F.data == "parser_settings")
async def parser_settings(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Выберите настройку", reply_markup=parsing_settings_menu())


@handlers_router.callback_query(F.data == "back")
async def back_to_admin_panel(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🔧 Панель управления", reply_markup=admin_menu())


@handlers_router.callback_query(F.data.startswith("parsing="))
async def parsing_settings(call: CallbackQuery, state: FSMContext):
    """Парсинг настроек"""
    act = call.data.split("=")[1]
    match act:
        case "frequency":
            await call.message.edit_text(f"🕒 Введите частоту парсинга(в секундах)\n\nК примеру, чтобы раз в минуту, то 60с, если раз в 2 минуты то 120с и т.д\n\n<b>Текущее значение:</b>  {get_settings_value('frequency')}")
            await state.set_state(AdminStates.Frequency)
        case "dates":
            await call.message.edit_text(f"📆 Введите временные интервалы работы парсера в течение дня(Формат: 15:00-20:00, 13:00-21:00)\n\n<b>Текущее значение:</b>  {get_settings_value('dates')}")
            await state.set_state(AdminStates.Dates)
        case "timezone":
            await call.message.edit_text(f"🌍 Введите часовую зону, в которой будет работать расписание для парсера(Формат: America/Los_Angeles, Asia/Almaty, Australia/Canberra, Europe/Minsk, Europe/Kyiv)\n\n<b>Текущее значение:</b>  {get_settings_value('timezone')}")
            await state.set_state(AdminStates.Timezone)
        case "diff":
            diff = get_settings_value('diff')
            await call.message.edit_text(f"➗ Введите значение разницы в процентах (%)\n\n<b>Текущее значение:</b>  {diff}")
            await state.set_state(AdminStates.Difference)
        case "bk_intervals":
            await call.message.edit_text("⚖️ Выберите БК", reply_markup=bk_intervals_menu())
        case "authorization":
            await call.message.edit_text("🔑 Выберите платформу", reply_markup=autorization_menu())
        case "sports":
            await call.message.edit_text("Выберите спорт", reply_markup=sport_settings_menu())
            await state.set_state(AdminStates.Sports)
        case "pause":
            value = "True" if get_settings_value("parsing") == "False" else "False"
            update_settings("parsing", value)
            if value == "True":
                await start_task()
            else:
                await done_task()
            await call.message.edit_text("Выберите настройку", reply_markup=parsing_settings_menu())
        case "analytics":
            value = "True" if get_settings_value("analytics") == "False" else "False"
            update_settings("analytics", value)
            await call.message.edit_text("Выберите настройку", reply_markup=parsing_settings_menu())


@handlers_router.message(AdminStates.Frequency)
async def frequency(msg, state: FSMContext):
    if validate_secounds(msg.text):
        update_settings("frequency", msg.text if int(msg.text) >= 30 else "30")
        await msg.answer(f"✔ Успешно сохранено со значением {msg.text}!")
        await state.clear()
    else:
        await msg.answer("❗️ Время в секундах указано не верно, попробуйте ещё раз")

@handlers_router.message(AdminStates.Dates)
async def dates(msg, state: FSMContext):
    if validate_time_interval(msg.text):
        update_settings("dates", msg.text)
        await msg.answer(f"✔ Успешно сохранено со значением {msg.text}!")
        await state.clear()
    else:
        await msg.answer("❗️ Интервал в течении дня введён не верно, попробуйте ещё раз")

@handlers_router.message(AdminStates.Difference)
async def difference(msg, state: FSMContext):
    if validate_float(msg.text):
        update_settings("diff", msg.text)
        await msg.answer(f"✔ Успешно сохранено со значением {msg.text}!")
        await state.clear()
    else:
        await msg.answer("❗️ Значение разницы введено не верно, попробуйте ещё раз")

@handlers_router.message(AdminStates.Timezone)
async def timezone(msg, state: FSMContext):
    if validate_timezone(msg.text):
        update_settings("timezone", msg.text)
        await msg.answer(f"✔ Успешно сохранено со значением {msg.text}!")
        await state.clear()
    else:
        await msg.answer("❗️ Такая часовая зона не найдена, попробуйте ещё раз")

@handlers_router.callback_query(F.data.startswith("autorization="))
async def autorization_settings(call: CallbackQuery, state: FSMContext):
    platform = call.data.split("=")[1]
    with open("parser/login.json", "r") as f:
        data = json.load(f)
    allbestbets = data["allbestbets"]
    # line4bet = data["line4bet"]
    if platform == "allbestbets":
        await call.message.edit_text(f"🔑 Введите логин и пароль для allbestbets. \n\nЛогин и пароль должны быть в формате:\n\nlogin:password.\n\n<b>Текущие данные:</b>  {allbestbets}")
        await state.set_state(AdminStates.Allbestbets)
    # else:
    #     await call.message.edit_text(f"🔑 Введите логин и пароль для line4bet. \n\nЛогин и пароль должны быть в формате:\n\nlogin:password.\n\n<b>Текущие данные:</b>  {line4bet}")
    #     await state.set_state(AdminStates.Line4bets)
        
    
@handlers_router.message(AdminStates.Allbestbets)
async def allbestbets(msg, state):
    if validate_login(msg.text):
        await done_task()
        if await login_allbestbets(msg.text):
            await msg.answer("✔ Успешно сохранено!")
            if not await get_sub_status_allbestbets():
                await msg.answer("⚠️ Срок подписки на allbestbets истёк")
            else:
                await start_task()
            await state.clear()
        else:
            # await start_task()
            await msg.answer("❗️ Неудалось авторизоваться на allbestbets, повторите попытку")
    else:
        await msg.answer("❗️ Данные авторизации не соответствуют формату, попробуйте ещё раз")


# @handlers_router.message(AdminStates.Line4bets)
# async def line4bet(msg, state):
#     if validate_login(msg.text):
#         await done_task()
#         if await login_line4bet(msg.text):
#             await msg.answer("✔ Успешно сохранено!")
#             if not await get_sub_status_line4bet():
#                 await msg.answer("⚠️ Срок подписки на line4bet истёк")
#             else:
#                 await start_task()
#             await state.clear()
#         else:
#             # await start_task()
#             await msg.answer("❗️ Неудалось авторизоваться на line4bet, повторите попытку")
#     else:
#         await msg.answer("❗️ Данные авторизации не соответствуют формату, попробуйте ещё раз")


@handlers_router.callback_query(F.data.startswith("bk_intervals="))
async def bk_intervals_settings(call: CallbackQuery, state: FSMContext):
    act = call.data.split("=")[1]
    match act:
        case "pinnacle":
            await call.message.edit_text(f"Введите интервал кф для Pinnacle.\n\n Интревал должен быть в формате: 1.5:2.5, 1:3\n\n<b>Текущее значение:</b>  {get_settings_value('pinnacle_koef_interval')}")
            await state.set_state(AdminStates.BKIntervals)
            await state.set_data({"bk": "pinnacle"})
        case "others":
            await call.message.edit_text(f"Введите интервал кф для остальных бк.\n\n Интревал должен быть в формате: 1.5:2.5, 1:3\n\n<b>Текущее значение:</b>  {get_settings_value('others_koef_interval')}")
            await state.set_state(AdminStates.BKIntervals)
            await state.set_data({"bk": "others"})
        case "back":
            await call.message.edit_text("Выберите настройку", reply_markup=parsing_settings_menu())


@handlers_router.message(AdminStates.BKIntervals)
async def bk_intervals(msg, state: FSMContext):
    data = await state.get_data()
    if validate_koef_interval(msg.text):
        if data["bk"] == "pinnacle":
            update_settings("pinnacle_koef_interval", msg.text)
        else:
            update_settings("others_koef_interval", msg.text)
        await msg.answer("✔ Успешно сохранено!")
        await state.clear()
    else:
        await msg.answer("❗️ Введённый интервал не корректный, попробуйте ещё раз")


@handlers_router.callback_query(F.data.startswith("sport="))
async def sports_settings(call: CallbackQuery, state: FSMContext):
    sport = call.data.split("=")[1]
    if sport != "back":
        value = "True" if get_settings_value(sport) == "False" else "False"
        update_settings(sport, value)
        await call.message.edit_text("Выберите спорт", reply_markup=sport_settings_menu())
    else:
        await call.message.edit_text("Выберите настройку", reply_markup=parsing_settings_menu())


@handlers_router.callback_query(F.data == "channels")
async def channels(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Управление каналами", reply_markup=channels_settings_menu())


@handlers_router.callback_query(F.data.startswith("channels="))
async def channels_settings(call: CallbackQuery, state: FSMContext):
    option = call.data.split("=")[1]
    channels_list = get_channels_list()
    match option:
        case "list":
            text = ""
            if not channels_list:
                await call.message.edit_text("❗️ Список подключенных каналов пуст")
                return
            for channel in channels_list:
                text += f"{'🟢' if channel[2] else '🔴'} {channel[1]}\nid:  {channel[0]}\n\n"
            await call.message.edit_text("<b>Список каналов:</b>\n\n" + text)
        case "pause":
            await call.message.edit_text(f"✋ Введите id канала, чтоб поставить на паузу или включить: ")
            await state.set_state(AdminStates.Channels)
            await state.set_data({"method": "pause", "list": channels_list})
        case "disconnect":
            await call.message.edit_text(f"🔌 Введите id канала, чтоб отключить: ")
            await state.set_state(AdminStates.Channels)
            await state.set_data({"method": "disconnect", "list": channels_list})
        case "back":
            await call.message.edit_text("🔧 Панель управления", reply_markup=admin_menu())


@handlers_router.message(AdminStates.Channels)
async def channels_settings_applying(msg: Message, state: FSMContext):
    data = await state.get_data()
    method = data["method"]
    channels_list = data["list"]
    channel_id = int(msg.text)
    current_channel = None
    for channel in channels_list:
        if channel_id == channel[0]:
            current_channel = channel
            break
    if not current_channel:
        await msg.answer("❗️ Канал с таким id не найден, изменения не были внесены")
        await state.clear()
        return
    match method:
        case "pause":
            udpate_channels(channel_id)
            await msg.answer(f"Канал \"{current_channel[1]}\" {'поставлен на пузу' if current_channel[2] else 'включён'} \n\n✔ Состояние канала изменено!")
        case "disconnect":
            delete_channel(channel_id)
            await msg.answer(f"✔ Канал \"{current_channel[1]}\" отключен!")    
    await state.clear()


@handlers_router.callback_query(F.data == "contact")
async def contact(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(f"👤 <b>Укажите контактное лицо</b>\n\nВведите ссылку на контактное лицо, для связи по оплате подписки\n\n<b>Текущеё контактное лицо:</b> {url_oplata}")
    await state.set_state(AdminStates.Contact)


@handlers_router.message(AdminStates.Contact)
async def set_contact(msg: Message, state: FSMContext):
    global url_oplata
    import requests
    new_url = msg.text
    try:
        response = requests.get(new_url)
        if response.status_code == 200:
            url_oplata = new_url
            config['URL_OPLATA'] = new_url
            edit_config_info(config)
            await msg.answer("✔ Успешно сохранено!")
            await state.clear()
        else:
            await msg.answer("❗️ Не удалось сохранить, повторите попытку")
    except:
        await msg.answer("❗️ Ссылка не рабочая, введите другую")


@handlers_router.my_chat_member()
async def bot_member_status_changes(update: ChatMemberUpdated):
    admin_ids = config["ADMIN_IDS"]
    chat = (update.chat.id, update.chat.title)
    if update.from_user.id in admin_ids:
        match update.new_chat_member.status:
            case "administrator":
                add_channel(chat)
            case "left":
                delete_channel(update.chat.id)


async def start_task():
    global parser_task
    if parser_task == None or parser_task.done():
        parser_task = asyncio.create_task(parsing())


async def done_task():
    if parser_task != None and not parser_task.done():
        parser_task.cancel()
        try:
            await parser_task
        except asyncio.CancelledError:
            logger.info("Таска сдохла")

def is_time_in_range(start, end, now) -> bool:
    if start <= end:
        return start <= now <= end
    else:
        return now >= start or now <= end

async def parsing():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    admin_ids = config["ADMIN_IDS"]
    today = get_settings_value("last_date")
    pred_num = int(get_settings_value("last_num"))

    logger.info("Таска поднялась")
    try:
        while True:
            await asyncio.sleep(0)
            parse_ = get_settings_value("parsing")
            if parse_ == "False":
                break
            frequency = int(get_settings_value("frequency"))
            start_str, end_str = get_settings_value("dates").split("-")
            timezone = get_settings_value("timezone")
            now = datetime.now(ZoneInfo(timezone)).time()
            start = datetime.strptime(start_str, "%H:%M").time()
            end = datetime.strptime(end_str, "%H:%M").time()
            diff = float(get_settings_value("diff"))/100
            pint = get_settings_value("pinnacle_koef_interval")
            cint = get_settings_value("others_koef_interval")
            if is_time_in_range(start, end, now):

                try: 
                    logger.info("Проверка подписок...")
                    sub_status = await get_sub_status_allbestbets()
                    if sub_status == False:
                        for admin in admin_ids:
                            await bot.send_message(admin, "⚠️ Срок подписки на allbestbets истёк")
                        logger.warning("Подписка на allbestbets истекла")
                        break
                    elif sub_status == None:
                        raise Exception("не удалось залогиниться")
                    # if not await get_sub_status_line4bet():
                    #     for admin in ADMIN_IDS:
                    #         await bot.send_message(admin, "⚠️ Срок подписки на line4bet истёк")
                    #     logger.warning("Подписка на line4bet глекнулась")
                    #     break
                    logger.info("Подписки в порядке")
                except Exception as e:
                    logger.error(f"Ошибка при проверке подписок: {e}")
                    continue


                sports = {
                    "football": "Футбол",
                    "basketball": "Баскетбол",
                    "tennis": "Теннис",
                    "hockey": "Хоккей",
                    "volleyball": "Волейбол",
                    "dota2": "Dota 2",
                    "cs": "Counter-Strike"
                }
                allowed_sports = []
                for key in sports.keys():
                    if get_settings_value(key) == "True":
                        allowed_sports.append(sports[key])

                prev_matches = get_matches()
                users = get_allowed_users()
                channels = get_allowed_channels()
                
                logger.info("Парсинг начат")
                matches = await parse(prev_matches, diff, pint, cint)
                logger.info("Парсинг закончен")

                for match in matches:
                    if match['sport'] not in allowed_sports:
                        continue

                    curr_date = datetime.now(ZoneInfo(timezone)).date().isoformat()
                    if today != curr_date:
                        today = curr_date
                        pred_num = 1
                        update_settings("last_date", curr_date)
                        update_settings("last_num", f"{pred_num}")
                    else:
                        pred_num += 1
                        update_settings("last_num", f"{pred_num}")
                    
                    message = \
                        f"{datetime.now(ZoneInfo(timezone)).strftime('%d%b%y').lower()}#{pred_num}\n" \
                        f"Букмекерская контора: {match['bookmaker']}\n" \
                        f"Вид спорта: {match['sport']}\n" \
                        f"Дата: {match['date']}\n" \
                        f"Турнир: {match['league_ru'] if match['league_ru'] not in (None, '', ' ') else match['league']}\n" \
                        f"<b>Команды:</b> {match['name_ru'] if match['name_ru'] not in (None, '', ' ') else match['name']}\n" \
                        f"Прогноз: {match['market_name']}\n" \
                        f"Справедливый кф: {match['fair']}\n" \
                        f"КФ: {match['coefficient']}\n"
                    
                    for user in users:
                        if user in admin_ids and get_settings_value("analytics") == "True":
                            await bot.send_message(user, message + \
                                "\n<b>Аналитика:</b>\n"
                                f"Pinnacle: {match['p_row'][1:]}\n" \
                                f"{match['c_row'][0]}: {match['c_row'][1:]}\n" \
                                f"Разница: {format(match['difference'], '.2f')}\n" \
                                f"{match['url']}")
                        else:
                            await bot.send_message(user, message)
                        logger.info(f"Сообщение отправлено юзеру: {user}")

                    for channel in channels:
                        try: 
                            await bot.send_message(channel, message)
                            logger.info(f"Сообщение отправлено в канал: {channel}")
                        except Exception as e:
                            logger.error(f"Ошибка при попытке написать в канал: {e}")
                            delete_channel(channel)
                            logger.info("Канал удалён из списка")

                    add_match(match['id'])

                await asyncio.sleep(frequency)
    except asyncio.CancelledError:
        raise
    logger.info("Таска закончилась")

async def on_start():
    await start_task()