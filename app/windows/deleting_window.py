from aiogram.enums import ParseMode
from aiogram_dialog import StartMode, Window
from aiogram_dialog.widgets.kbd import Group, Select, Start
from aiogram_dialog.widgets.text import Const, Format

from app.callbacks.delete_subscribe import on_subscibe_deleted
from app.getters.subscribes_selector import get_subscribes
from app.states.danmenu import DanMenu

deleting_window = Window(
    Const("<b>Выберите подписку которую нужно удалить:</b>"),
    Group(
        Select(
            Format("{item}"),
            items="tags",
            item_id_getter=lambda x: x,
            id="select_tags",
            on_click=on_subscibe_deleted,
        ),
        width=2,
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
