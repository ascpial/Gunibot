from __future__ import annotations
from typing import TYPE_CHECKING

import nextcord
from nextcord.ext import commands

if TYPE_CHECKING:
    from gunibot import Gunibot

class HelloWorld(commands.Cog):
    def __init__(self, bot: Gunibot) -> None:
        self.bot = bot
        self.logger = self.bot.get_logger("helloworld")
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f'Ready ! Connected as {self.bot.user.name}#{self.bot.user.discriminator}, {self.bot.user.id} !')

def setup(bot: Gunibot) -> None:
    bot.add_cog(HelloWorld(bot))