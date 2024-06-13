import asyncio
import os
from twitchio.ext import commands
from cogs.logging import logger, prepare as prepare_logging_cog
from cogs.tts_guest import TTSGuestCog
from cogs.vtube_studio import VTubeStudioCog

ACCESS_TOKEN = os.getenv("TWITCH_BOT_ACCESS_TOKEN")
TWITCH_CHANNELS = os.getenv("TWITCH_CHANNELS").split(",")
_bot = None


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=ACCESS_TOKEN, prefix="!", initial_channels=TWITCH_CHANNELS
        )

    async def event_ready(self):
        logger.info(f"Logged in as {self.nick}")
        logger.info(f"User id is {self.user_id}")

    async def event_message(self, message):
        if message.echo:
            return

        await self.handle_commands(message)

    @commands.command()
    async def help(self, ctx):
        commands = [cmd.name for cmd in self.commands.values()]
        await ctx.send(f"Available commands: {', '.join(commands)}")


def get_bot():
    global _bot
    if _bot is None:
        _bot = Bot()
        prepare_logging_cog(_bot)

    return _bot


def run_bot(socketio):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = get_bot()
    bot.tts_guest = TTSGuestCog(bot, socketio)
    bot.add_cog(bot.tts_guest)
    bot.vtube_studio = VTubeStudioCog(bot)
    bot.add_cog(bot.vtube_studio)

    loop.run_until_complete(bot.start())
