from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import logging

import nextcord
from nextcord.ext import commands

from .configuration import Configuration
from .database import Database


__all__ = [
    "Gunibot",
]

class Gunibot(commands.Bot):
    def __init__(self) -> None:
        self.configuration = Configuration()
        super().__init__(
            self.configuration.prefix,
            description=self.configuration.description
        )
        self.database = Database(self)
    
    def get_logger(self, name: str = ...) -> logging.Logger:
        return logging.getLogger(name)
    
    def run(self) -> None:
        self.database.connect()
        
        super().run(self.configuration.token)
    
    async def get_or_fetch_user(
        self,
        user_id: int,
    ) -> Optional[nextcord.User]:
        user = self.get_user(user_id)
        if user is None:
            return await self.fetch_user(user_id)
        return user
    
    async def close(self) -> None:
        await super().close()
        self.database.session.commit()
        self.database.close()