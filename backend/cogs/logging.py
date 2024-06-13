import logging
import colorlog
import os
from twitchio.ext import commands

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRIT": logging.CRITICAL,
}
LOG_LEVEL = LOG_LEVELS.get(os.getenv("LOG_LEVEL"), logging.INFO)


def setup_logger(name):
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(LOG_LEVEL)
    return logger


logger = setup_logger("beth-the-bot")


class TwitchLoggerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message):
        if not message.echo:
            logger.info(f"{message.author.name}: {message.content}")


def prepare(bot):
    bot.add_cog(TwitchLoggerCog(bot))
