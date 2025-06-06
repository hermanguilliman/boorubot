from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram_dialog import StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Start
from aiogram_dialog.widgets.text import Const, Format

from app.callbacks.delete_subscribe import on_subscribing_deleted
from app.getters.subscribes_selector import get_subscribes
from app.handlers.subscribes import search_subscribes
from app.states.danmenu import DanMenu

deleting_window = Window(
    # Если не задан поисковый запрос и есть подписки
    Const(
        "<b>📖 Перед вами все имеющиеся подписки</b>\n",
        when=~F["dialog_data"]["search_query"] & F["subscriptions"],
    ),
    # Если задан поисковый запрос и есть результат поиска
    Format(
        "<b>🔎 Перед вами все подписки по запросу: {dialog_data[search_query]}</b>\n",
        when=F["dialog_data"]["search_query"] & F["subscriptions"],
    ),
    # Если есть список результатов, но нет поискового запроса
    Const(
        "<b>👇 Выберите подписку, которую нужно удалить, либо используйте поисковый запрос для фильтрации</b>",
        when=F["subscriptions"] & ~F["dialog_data"]["search_query"],
    ),
    # Если есть список результатов по поисковому запросу
    Const(
        "<b>👇 Выберите подписку, которую нужно удалить, либо используйте другой поисковый запрос</b>",
        when=F["subscriptions"] & F["dialog_data"]["search_query"],
    ),
    # Если есть поисковый запрос, но нет результатов
    Const(
        "<b>🔎 По вашему запросу ничего не найдено</b>",
        when=~F["subscriptions"] & F["dialog_data"]["search_query"],
    ),
    # Если нет результатов и нет поискового запроса
    Const(
        "<b>🤷 В данный момент в базе данных нет подписок</b>",
        when=~F["subscriptions"] & ~F["dialog_data"]["search_query"],
    ),
    MessageInput(search_subscribes, content_types=[ContentType.TEXT]),
    ScrollingGroup(
        Select(
            Format("{item[1]}"),  # Текст кнопки — тег подписки
            items="subscriptions",  # Список кортежей (id, tag)
            item_id_getter=lambda x: x[0],  # ID как callback_data
            id="select_subscriptions",
            on_click=on_subscribing_deleted,
        ),
        width=2,
        height=10,
        id="scrolling_tags",
        when="subscriptions",  # Показывать, если есть подписки
    ),
    Start(
        Const("👈 Назад"),
        id="restart",
        state=DanMenu.main,
        mode=StartMode.NORMAL,
    ),
    getter=get_subscribes,
    state=DanMenu.delete,
    parse_mode=ParseMode.HTML,
)
