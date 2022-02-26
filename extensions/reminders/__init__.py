from __future__ import annotations
from typing import TYPE_CHECKING

import datetime
import base64

import nextcord
from nextcord.ext import commands
from nextcord.ext import tasks
import sqlalchemy

from .reminder_manager import ReminderManager
from .reminder import Reminder

if TYPE_CHECKING:
    from gunibot import Gunibot

EMPTY_AUTOCOMPLETE = "Il n'y a rien à voir ici..."

class Reminders(commands.Cog):
    def __init__(self, bot: Gunibot) -> None:
        self.bot = bot
        self.reminder_manager = ReminderManager(self.bot)
        self.bot.configuration.add_guilds(self.reminder)
        self.bot.configuration.add_guilds(self.create_timestamp)
    
    @nextcord.slash_command(
        name="reminder",
        description="Permet de gérer des rappels.",
        guild_ids=[],
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
        ),
        notification: bool = nextcord.SlashOption(
            description="Indique si le bot doit envoyer un message de rappel.",
            required=False,
        )
    ) -> None:
        if scheduled.isdigit():
            scheduled = datetime.datetime.fromtimestamp(int(scheduled))
        try:
            reminder = self.reminder_manager.create_reminder(
                user if user is not None else inter.user,
                name,
                scheduled,
                description,
                notification,
                inter.user if user is not None else None,
            )
        except ValueError:
            await inter.send(
                "Vous avez déjà un rappel avec ce nom. Utilisez en un autre !",
                ephemeral=True,
            )
        except SyntaxError:
            await inter.send(
                "Il y a une erreur dans la syntaxe crontab.",
                ephemeral=True,
            )
        else:
            await inter.send(
                "Le rappel a bien été créé !",
                embed=await reminder.get_embed(self.bot),
                view=reminder.get_view(),
                ephemeral=True,
            )
    
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
        try:
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
        except sqlalchemy.orm.exc.NoResultFound:
            if reminder == EMPTY_AUTOCOMPLETE:
                await inter.send(
                    "Tu n'as pas de rappels. Utilises `/reminder create` pour en créer un !",
                    ephemeral=True,
                )
            else:
                await inter.send(
                    f"Le rappel {reminder} n'a pas été trouvé...",
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
            Reminder.name.startswith(focused_option_value),
            Reminder.user == inter.user.id
        ).all()
        
        if len(reminders) > 0:
            return [reminder.name for reminder in reminders[:25]]
        else:
            return [EMPTY_AUTOCOMPLETE]
        
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
        try:
            if inter.type == nextcord.InteractionType.component:
                custom_id = inter.data['custom_id']
                if custom_id.startswith('delete_reminder_'):
                    reminder = self.get_reminder(custom_id[16:])
                    self.bot.database.session.delete(reminder)
                    view = reminder.get_view()
                    for item in view.children:
                        if isinstance(item, nextcord.ui.Button):
                            item.disabled = True
                    await inter.response.edit_message(
                        embed=await reminder.get_embed(self.bot),
                        view=view,
                    )
                elif custom_id.startswith('notification_reminder_'):
                    reminder = self.get_reminder(custom_id[22:])
                    reminder.notification = not reminder.notification
                    await inter.response.edit_message(
                        embed=await reminder.get_embed(self.bot),
                        view=reminder.get_view(),
                    )
                elif custom_id.startswith('edit_reminder_'):
                    await inter.send('Not implemented yet.', ephemeral=True)
        except sqlalchemy.exc.NoResultFound:
            await inter.send("Le rappel n'existe plus.", ephemeral=True)
    
    @nextcord.slash_command(
        name="timestamp",
        description="Génère un timestamp unix en fonction de la date et l'heure indiquée.",
        guild_ids=[941014823574061087],
    )
    async def create_timestamp(
        self, 
        inter: nextcord.Interaction,
        year: int = nextcord.SlashOption(min_value=1970),
        month: int = nextcord.SlashOption(min_value=1, max_value=12),
        day: int = nextcord.SlashOption(min_value=1, max_value=31),
        hour: int = nextcord.SlashOption(required=False, min_value=1, max_value=24, default=0),
        minute: int = nextcord.SlashOption(required=False, min_value=1, max_value=60, default=0),
        second: int = nextcord.SlashOption(required=False, min_value=1, max_value=60, default=0),
    ) -> None:
        try:
            timestamp = int(datetime.datetime(
                year, month, day,
                hour, minute, second
            ).timestamp())
            await inter.send(
                f"Le timestamp de la date <t:{timestamp}> est `{timestamp}`."
            )
        except ValueError:
            await inter.send(
                "La date indiquée est invalide.",
                ephemeral=False,
            )

def setup(bot: Gunibot) -> None:
    bot.add_cog(Reminders(bot))