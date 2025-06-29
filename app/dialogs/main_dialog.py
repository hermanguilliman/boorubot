from aiogram_dialog import Dialog

from app.windows.adding_window import adding_window
from app.windows.delete_sub import deleting_window
from app.windows.main_window import main_window
from app.windows.sublist_window import sublist_window

dialog = Dialog(main_window, sublist_window, adding_window, deleting_window)
