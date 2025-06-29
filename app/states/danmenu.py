from aiogram.filters.state import StatesGroup, State


class DanMenu(StatesGroup):
    main = State()
    add = State()
    delete = State()
