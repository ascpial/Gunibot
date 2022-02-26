from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import datetime
import base64

import sqlalchemy
import nextcord
import crontab

from gunibot.database import Base

if TYPE_CHECKING:
    from gunibot import Gunibot

NOTIFICATION = [
    "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/60/twitter/282/bell-with-slash_1f515.png",
    "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/60/twitter/282/bell_1f514.png",
]

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        autoincrement=True,
        primary_key=True,
    )
    user: int = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    author: int = sqlalchemy.Column(sqlalchemy.Integer)
    name: str = sqlalchemy.Column(sqlalchemy.String)
    description: str = sqlalchemy.Column(sqlalchemy.String)
    time: Optional[datetime.datetime] = sqlalchemy.Column(sqlalchemy.DateTime)
    scheduled: Optional[str] = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    sended: bool = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False,
    )
    notification: bool = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=True,
    )
    
    def __init__(
        self,
        user: int,
        name: str,
        author: int = None,
        description: str = None,
        time: Optional[datetime.datetime] = None,
        scheduled: Optional[str] = None,
        sended: bool = False,
        notification: bool = True,
    ) -> None:
        self.user = user
        self.name = name
        self.author = author
        self.description = description
        self.time = time
        self.scheduled = scheduled
        self.sended = sended
        self.notification = notification
    
    @property
    def encoded_id(self) -> str:
        return base64.b64encode(self.id.to_bytes(4, byteorder='little')).decode('utf-8')
    
    async def get_user(self, bot: Gunibot) -> Optional[nextcord.User]:
        return await bot.get_or_fetch_user(self.user)
    
    async def get_author(self, bot: Gunibot) -> Optional[nextcord.User]:
        if self.author is not None:
            return await bot.get_or_fetch_user(self.author)
        else:
            return await self.get_user(bot)

    def next(self) -> datetime.datetime:
        if self.crontab is not None:
            if self.time is not None:
                return self.crontab.next(
                    self.time,
                    return_datetime=True,
                    default_utc=True,
                )
            else:
                return self.crontab.next(
                    return_datetime=True,
                    default_utc=True,
                )
        else:
            return self.time

    @property
    def crontab(self) -> Optional[crontab.CronTab]:
        if self.scheduled is not None:
            return crontab.CronTab(self.scheduled)
        return None

    async def refresh(self, bot: Gunibot) -> None:
        next = self.next()
        now = datetime.datetime.now()
        if now >= next:
            if not self.sended or self.scheduled is not None:
                if self.notification:
                    user = await self.get_user(bot)
                    await user.send(
                        embed=await self.get_embed(bot),
                        view=self.get_view(),
                    )
                
                if self.scheduled is None:
                    self.sended = True
                else:
                    crontab = self.crontab
                    time = self.time
                    while crontab.next(
                            time,
                            return_datetime=True,
                            default_utc=True,
                        ) < now:
                        time = crontab.next(
                            time,
                            return_datetime=True,
                            default_utc=True,
                        )
                    self.time = time
        
    async def get_embed(self, bot: Gunibot) -> nextcord.Embed:
        embed = nextcord.Embed(
            title=f"Rappel : {self.name}",
            color=0x2f3136,
            description=self.description if self.description is not None else "",
            timestamp=self.next(),
        )
        embed.set_footer(
            text=self.scheduled,
            icon_url=NOTIFICATION[self.notification]
        )
        author = await self.get_author(bot)
        if author is not None:
            embed.set_author(
                name=author.name,
                icon_url=author.avatar.url,
            )
        embed.set_thumbnail(
            url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/160/twitter/282/clipboard_1f4cb.png",
        )
        return embed

    def get_view(self) -> nextcord.ui.View:
        view = nextcord.ui.View(timeout=0.1)
        view.add_item(
            nextcord.ui.Button(
                custom_id=f'delete_reminder_{self.encoded_id}',
                style=nextcord.ButtonStyle.danger,
                emoji="🗑",
                label="Supprimer",
            )
        )
        view.add_item(
            nextcord.ui.Button(
                custom_id=f'notification_reminder_{self.encoded_id}',
                style=nextcord.ButtonStyle.secondary,
                emoji="🔔" if self.notification else "🔕",
                label=f"Notification {'activée' if self.notification else 'désactivée'}",
            )
        )
        view.add_item(
            nextcord.ui.Button(
                custom_id=f'edit_reminder_{self.encoded_id}',
                style=nextcord.ButtonStyle.secondary,
                emoji="✏",
                label=f"Modifier le rappel",
            )
        )
        return view

    def __repr__(self) -> str:
        return f"<Reminder id={repr(self.id)} name={repr(self.name)} time={repr(self.time)} scheduled={repr(self.scheduled)} next={self.next()} sended={self.sended}>"
