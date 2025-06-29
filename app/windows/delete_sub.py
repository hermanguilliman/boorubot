from aiogram.enums import ParseMode
from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Button, Row, SwitchTo
from aiogram_dialog.widgets.text import Const

from app.callbacks.delete_subscribe import on_delete_confirm
from app.states.danmenu import DanMenu

deleting_window = Window(
    Const("Подтвердить удаление?"),
    Row(
        SwitchTo(Const("👈 Назад"), state=DanMenu.sub_list, id="back"),
        Button(
            Const("👍 Да, удаляем"),
            id="delete_sub",
            on_click=on_delete_confirm,
        ),
    ),
    state=DanMenu.delete,
    parse_mode=ParseMode.HTML,
)
