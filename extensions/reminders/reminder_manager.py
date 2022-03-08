from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Optional, Union
import base64

import nextcord
import sqlalchemy
from crontab import CronTab

from .reminder import Reminder

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

    def get_reminder_by_id(self, raw_reminder_id: str) -> int:
        bytes = base64.b64decode(raw_reminder_id)
        return int.from_bytes(bytes, byteorder='little')

    def get_reminder(self, raw_reminder_id: str) -> Reminder:
        reminder_id = self.get_reminder_by_id(raw_reminder_id)
        try:
            return self.bot.database.session.query(
                Reminder
            ).filter(Reminder.id==reminder_id).one()
        except sqlalchemy.exc.NoResultFound:
            return None

    def get_reminder_by_name(
        self,
        name: str,
    ) -> Optional[Reminder]:
        try:
            reminder = self.bot.database.session.query(
                Reminder
            ).filter(
                Reminder.name == name
            ).one()
            
            return reminder
        except sqlalchemy.orm.exc.NoResultFound:
            return None
    
    
    def delete_reminder(self, reminder: Reminder) -> None:
        self.bot.database.session.delete(reminder)
