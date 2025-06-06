from aiogram.enums import ParseMode
from aiogram_dialog import StartMode, Window
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Start
from aiogram_dialog.widgets.text import Const, Format

from app.callbacks.delete_subscribe import on_subscribing_deleted
from app.getters.subscribes_selector import get_subscribes
from app.states.danmenu import DanMenu

deleting_window = Window(
    Const("<b>Выберите подписку которую нужно удалить:</b>"),
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
        Const("Назад"),
        id="restart",
        state=DanMenu.main,
        mode=StartMode.NORMAL,
    ),
    getter=get_subscribes,
    state=DanMenu.delete,
    parse_mode=ParseMode.HTML,
)
