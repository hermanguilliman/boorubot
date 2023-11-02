from sys import stdout

from loguru import logger


def logger_setup():
    logger.remove()
    logger.add("logs/bot.log", level="DEBUG", rotation="10 MB")
    logger.add(
        stdout,
        colorize=True,
        format="<green>{time}</green> <level>{message}</level>",
        level="DEBUG",
    )
