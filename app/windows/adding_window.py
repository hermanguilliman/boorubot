from aiogram.enums import ContentType, ParseMode
from aiogram_dialog import Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back
from aiogram_dialog.widgets.text import Const

from app.handlers.subscribes import add_new_subscribe
from app.states.danmenu import DanMenu

adding_window = Window(
    Const("<b>Введите один или несколько Danbooru тэгов через пробел</b>"),
    MessageInput(add_new_subscribe, content_types=[ContentType.TEXT]),
    Back(
        Const("👈 Назад"),
    ),
    state=DanMenu.add,
    parse_mode=ParseMode.HTML,
)
