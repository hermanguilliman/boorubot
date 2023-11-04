from aiogram.enums import ParseMode
from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from app.getters.main_window import main_window_getter
from app.states.danmenu import DanMenu

main_window = Window(
    Const("<u><b>boorubot</b></u> 👻"),
    Format("<b>Активных подписок: <u>{subs_counter}</u></b>", when="subs_counter"),
    Format(
        "<b>Минут до следующего обновления: <u>{minutes_until_next_update}</u></b>",
        when="minutes_until_next_update",
    ),
    Row(
        SwitchTo(Const("🍏 Добавить"), id="add", state=DanMenu.add),
        SwitchTo(Const("🍎 Удалить"), id="delete", state=DanMenu.delete),
    ),
    state=DanMenu.main,
    parse_mode=ParseMode.HTML,
    getter=main_window_getter,
    preview_data={
        "minutes_until_next_update": "Неизвестно",
        "subs_counter": "Неизвестно",
    },
)
