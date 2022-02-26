from __future__ import annotations
from typing import TYPE_CHECKING

import datetime
import re
import base64

import nextcord
from nextcord.ext import commands
from nextcord.ext import tasks

from .reminder_manager import ReminderManager
from .reminder import Reminder

if TYPE_CHECKING:
    from gunibot import Gunibot

class Reminders(commands.Cog):
    def __init__(self, bot: Gunibot) -> None:
        self.bot = bot
        self.reminder_manager = ReminderManager(self.bot)
    
    @nextcord.slash_command(
        name="reminder",
        description="Permet de gérer des rappels.",
        guild_ids=[941014823574061087],
    )
    async def reminder(self, inter: nextcord.Interaction) -> None:
        pass
    
    @reminder.subcommand(
        name="create",
        description="Créé un rappel à la date indiquée",
    )
    async def create_reminder(
        self,
        inter: nextcord.Interaction,
        name: str = nextcord.SlashOption(
            description="Le nom du rappel (nécessaire).",
            required=True,
        ),
        scheduled: str = nextcord.SlashOption(
            description="L'heure programmée (syntaxe cron)."
        ),
        description: str = nextcord.SlashOption(
            description="La description complémentaire du rappel.",
            required=False,
        ),
        user: nextcord.User = nextcord.SlashOption(
            description="L'utilisateur à qui ajouter le rappel.",
            required=False,
        )
    ) -> None:
        if scheduled.isdigit():
            scheduled = datetime.datetime.fromtimestamp(int(scheduled))
        reminder = self.reminder_manager.create_reminder(
            inter.user,
            name,
            scheduled,
            description
        )
        await inter.send(
            "Le rappel a bien été créé !",
            embed=await reminder.get_embed(self.bot),
            view=reminder.get_view(),
            ephemeral=True,
        )

    @reminder.subcommand(
        name="list",
        description="Liste tous les rappels ajoutés à ton compte."
    )
    async def reminder_list(self, inter: nextcord.Interaction) -> None:
        pass
    
    @reminder.subcommand(
        name="show",
        description="Affiche un rappel particulier.",
    )
    async def reminder_show(
        self,
        inter: nextcord.Interaction,
        reminder: str = nextcord.SlashOption(
            description="Le nom du rappel à afficher",
            required=True,
            autocomplete=True,
        )
    ) -> None:
        reminder = self.bot.database.session.query(
            Reminder
        ).filter(
            Reminder.name == reminder
        ).one()
        
        await inter.send(
            embed = await reminder.get_embed(self.bot),
            view=reminder.get_view(),
            ephemeral=True,
        )

    @reminder_show.on_autocomplete('reminder')
    async def reminder_show_reminder_autocomplete(
        self,
        inter: nextcord.Interaction,
        focused_option_value: str,
    ) -> None:
        reminders = self.bot.database.session.query(
            Reminder
        ).filter(
            Reminder.name.startswith(focused_option_value)
        ).all()
        
        return [reminder.name for reminder in reminders[:25]]
        
    def get_reminder_id(self, raw_reminder_id: str) -> int:
        bytes = base64.b64decode(raw_reminder_id)
        return int.from_bytes(bytes, byteorder='little')

    def get_reminder(self, raw_reminder_id: str) -> Reminder:
        reminder_id = self.get_reminder_id(raw_reminder_id)
        return self.bot.database.session.query(
            Reminder
        ).filter(Reminder.id==reminder_id).one()
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.refresh.start()
    
    @tasks.loop(minutes=1)
    async def refresh(self) -> None:
        for reminder in self.bot.database.session.query(Reminder):
            await reminder.refresh(self.bot)
    
    @commands.Cog.listener()
    async def on_interaction(self, inter: nextcord.Interaction):
        if inter.type == nextcord.InteractionType.component:
            custom_id = inter.data['custom_id']
            if custom_id.startswith('delete_reminder_'):
                reminder = self.get_reminder(custom_id[16:])
                self.bot.database.session.delete(reminder)
                view = reminder.get_view()
                for item in view.children:
                    if isinstance(item, nextcord.ui.Button):
                        item.disabled = True
                await inter.edit_original_message(
                    embed=await reminder.get_embed(self.bot),
                    view=view,
                )
            elif custom_id.startswith('notification_reminder_'):
                reminder = self.get_reminder(custom_id[22:])
                reminder.notification = not reminder.notification
                await inter.edit_original_message(
                    embed=await reminder.get_embed(self.bot),
                    view=reminder.get_view(),
                )
            elif custom_id.startswith('notification_edit_'):
                await inter.send('Not implemented yet.', ephemeral=True)

def setup(bot: Gunibot) -> None:
    bot.add_cog(Reminders(bot))