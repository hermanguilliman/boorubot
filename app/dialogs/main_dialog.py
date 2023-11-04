from aiogram_dialog import Dialog

from app.windows.adding_window import adding_window
from app.windows.deleting_window import deleting_window
from app.windows.main_window import main_window

dialog = Dialog(
    main_window,
    adding_window,
    deleting_window,
)
