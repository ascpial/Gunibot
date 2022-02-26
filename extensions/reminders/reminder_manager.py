from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Optional, Union

import nextcord

from .reminder import Reminder

if TYPE_CHECKING:
    from gunibot import Gunibot

class ReminderManager:
    def __init__(self, bot: Gunibot) -> None:
        self.bot = bot

        Reminder.metadata.create_all(self.bot.database.engine)
    
    def create_reminder(
        self,
        user: Union[int, nextcord.User, nextcord.Member],
        name: str,
        scheduled: Union[datetime.datetime, str],
        description: Optional[str] = None,
    ) -> Reminder:
        if isinstance(user, (nextcord.User, nextcord.Member)):
            user = user.id
        if isinstance(scheduled, datetime.datetime):
            reminder = Reminder(
                user=user,
                name=name,
                description = description,
                time=scheduled,
            )
        else:
            reminder = Reminder(
                user=user,
                name=name,
                description = description,
                time=datetime.datetime.utcnow(),
                scheduled=scheduled,
            )
        self.bot.database.session.add(
            reminder,
        )
        self.bot.database.session.commit()
        return reminder