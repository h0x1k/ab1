from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# import json
# with open("config.json", "r") as f:
#     config = json.load(f)
# URL_OPLATA = config["URL_OPLATA"]

from database.database import get_settings_value
from config import get_config_info

def main_menu():
    url_oplata = get_config_info("config.json")["URL_OPLATA"]
    """Главное меню пользователя."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статус подписки", callback_data="check_sub")],
            [InlineKeyboardButton(text="💰 Приобрести", url=url_oplata)]
        ]
    )
    return kb

def admin_menu():
    """Меню для администратора."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕒 Настройки парсинга", callback_data="parser_settings")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="send")],
        [InlineKeyboardButton(text="✅ Выдать доступ", switch_inline_query_current_chat="grant")],
        [InlineKeyboardButton(text="❌ Закрыть доступ", switch_inline_query_current_chat="restrict")],
        [InlineKeyboardButton(text="🔒 Включить/выключить подписку", switch_inline_query_current_chat="enabled")],
        [InlineKeyboardButton(text="👑 Выдать/забрать админку", switch_inline_query_current_chat="admin")],
        [InlineKeyboardButton(text="📡 Каналы", callback_data="channels")],
        [InlineKeyboardButton(text="👤 Контактное лицо", callback_data="contact")]
    ])
    return kb

def parsing_settings_menu():
    """Меню настройки парсинга"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⌛ Частота парсинга", callback_data="parsing=frequency")],
        [InlineKeyboardButton(text="📅 Интервалы в течении дня", callback_data="parsing=dates")],
        [InlineKeyboardButton(text="🌍 Часовая зона", callback_data="parsing=timezone")],
        [InlineKeyboardButton(text="➗ Разница", callback_data="parsing=diff")],
        [InlineKeyboardButton(text="⚖️ Интервалы БК", callback_data="parsing=bk_intervals")],
        [InlineKeyboardButton(text=f"{'▶️ Возобновить' if get_settings_value('parsing') == 'False' else '⏸️ Пауза'}", callback_data="parsing=pause")],
        [InlineKeyboardButton(text=f"📊 Аналитика {'❌' if get_settings_value('analytics') == 'False' else '✔️'}", callback_data="parsing=analytics")],
        [InlineKeyboardButton(text="🔑 Авторизация", callback_data="parsing=authorization")],
        [InlineKeyboardButton(text="🏅 Виды спорта", callback_data="parsing=sports")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    return kb

def autorization_menu():
    """Меню авторизации"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="АллБестБетс", callback_data="autorization=allbestbets")]
        # [InlineKeyboardButton(text="Line4Bet", callback_data="autorization=line4bet")]
    ])
    return kb

def sport_settings_menu():
    """Меню настройки видов спорта"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚽ Футбол {'❌' if get_settings_value('football') == 'False' else '✔️'}", callback_data="sport=football")],
        [InlineKeyboardButton(text=f"🏀 Баскетбол {'❌' if get_settings_value('basketball') == 'False' else '✔️'}", callback_data="sport=basketball")],
        [InlineKeyboardButton(text=f"🎾 Теннис {'❌' if get_settings_value('tennis') == 'False' else '✔️'}", callback_data="sport=tennis")],
        [InlineKeyboardButton(text=f"🏒 Хоккей {'❌' if get_settings_value('hockey') == 'False' else '✔️'}", callback_data="sport=hockey")],
        [InlineKeyboardButton(text=f"🏐 Волейбол {'❌' if get_settings_value('volleyball') == 'False' else '✔️'}", callback_data="sport=volleyball")],
        [InlineKeyboardButton(text=f"🐉 Dota 2 {'❌' if get_settings_value('dota2') == 'False' else '✔️'}", callback_data="sport=dota2")],
        [InlineKeyboardButton(text=f"🔫 CS {'❌' if get_settings_value('cs') == 'False' else '✔️'}", callback_data="sport=cs")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="sport=back")]
    ])
    return kb

def channels_settings_menu():
    """Меню настройки каналов"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📃 Список каналов", callback_data="channels=list")],
        # [InlineKeyboardButton(text="➕ Подключить канал", callback_data="channels=connect")],   # нужен, если бот был не активен в момент добавления его в группу
        [InlineKeyboardButton(text="🔕 Возобновить/пауза", callback_data="channels=pause")],
        [InlineKeyboardButton(text="🔌 Отключить канал", callback_data="channels=disconnect")], # нужен, если бот был не активен в момент удаления его из группы
        [InlineKeyboardButton(text="🔙 Назад", callback_data="channels=back")]
    ])
    return kb

def bk_intervals_menu():
    """Меню интервалов для БК"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Pinnacle", callback_data="bk_intervals=pinnacle")],
        [InlineKeyboardButton(text="Остальные БК", callback_data="bk_intervals=others")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="bk_intervals=back")]
    ])
    return kb