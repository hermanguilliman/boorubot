from aiogram.enums import ParseMode
from aiogram_dialog import StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Row, Start, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from app.callbacks.popular_posts import on_popular_click
from app.callbacks.check_timer import on_check_timer
from app.callbacks.update_now import on_update_now
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
        SwitchTo(Const("💚 Добавить"), id="add", state=DanMenu.add),
        SwitchTo(Const("🗑 Удалить"), id="delete", state=DanMenu.delete),
    ),
    Row(
        Button(Const("📬 Проверить сейчас"), id="update_now", on_click=on_update_now),
        Button(Const("🤩Популярные посты"), id="popular", on_click=on_popular_click),
    ),
    Start(
        Const("⏲ Время следующего обновления"),
        id="restart",
        on_click=on_check_timer,
        state=DanMenu.main,
        mode=StartMode.NORMAL,
    ),
    state=DanMenu.main,
    parse_mode=ParseMode.HTML,
    getter=main_window_getter,
    preview_data={
        "minutes_until_next_update": "Неизвестно",
        "subs_counter": "Неизвестно",
    },
)
