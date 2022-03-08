from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Optional, Union

import nextcord

from .reminder import Reminder
from crontab import CronTab

if TYPE_CHECKING:
    from gunibot import Gunibot

class ReminderManager:
    def __init__(self, bot: Gunibot) -> None:
        self.bot = bot
        
        bot.add_orm(Reminder)
    
    def create_reminder(
        self,
        user: Union[int, nextcord.User, nextcord.Member],
        name: str,
        scheduled: Union[datetime.datetime, str],
        description: Optional[str] = None,
        notification: bool = True,
        author: Union[int, nextcord.User, nextcord.Member] = None,
    ) -> Reminder:
        if isinstance(user, (nextcord.User, nextcord.Member)):
            user = user.id
        if isinstance(author, (nextcord.User, nextcord.Member)):
            author = author.id
        
        check_duplicate = self.bot.database.session.query(
            Reminder
        ).filter(
            Reminder.user == user,
            Reminder.name == name,
        ).all()
        if len(check_duplicate):
            raise ValueError("The name is already used")
        
        if isinstance(scheduled, datetime.datetime):
            reminder = Reminder(
                user=user,
                name=name,
                description = description,
                time=scheduled,
                author=author,
                notification=notification,
            )
        else:
            try:
                cron = CronTab(scheduled)
            except ValueError:
                raise SyntaxError("The specified cron scheme is invalid")
            else:
                reminder = Reminder(
                    user=user,
                    name=name,
                    description = description,
                    time=datetime.datetime.utcnow(),
                    scheduled=scheduled,
                    author=author,
                    notification=notification,
                )
                self.bot.database.session.add(
                    reminder,
                )
                self.bot.database.session.commit()
                return reminder
