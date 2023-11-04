from aiogram_dialog import DialogManager, ShowMode, StartMode
from loguru import logger

from app.states.danmenu import DanMenu


async def on_unknown_intent(event, dialog_manager: DialogManager):
    """Example of handling UnknownIntent Error and starting new dialog."""
    logger.error("Restarting dialog: %s", event.exception)
    await dialog_manager.start(
        DanMenu.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


async def on_unknown_state(event, dialog_manager: DialogManager):
    """Example of handling UnknownState Error and starting new dialog."""
    logger.error("Restarting dialog: %s", event.exception)
    await dialog_manager.start(
        DanMenu.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )
