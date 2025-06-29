from aiogram.filters.state import State, StatesGroup


class DanMenu(StatesGroup):
    main = State()
    sub_list = State()
    add = State()
    delete = State()
