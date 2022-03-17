import nextcord
from nextcord.ext import commands

import gunibot

from .hub import HubManager, Hub

class Rolelink(commands.Cog):
    def __init__(self, bot: gunibot.Gunibot):
        self.bot = bot
        self.bot.configuration.add_guilds(self.hub)
        
        self.hub_manager = HubManager(self.bot)
    
    @nextcord.slash_command(
        name="hub",
        guild_ids=[],
    )
    async def hub(self, inter: nextcord.Interaction):
        pass
    
    @hub.subcommand(
        name="create",
        description="Permet de créer un hub de serveurs.",
    )
    async def hub_create(
        self,
        inter: nextcord.Interaction,
        name: str = nextcord.SlashOption(
            description="Le nom du hub de serveurs.",
            required=True,
        ),
        description: str = nextcord.SlashOption(
            description="La description du hub de serveur si nécessaire.",
            required=False,
        )
    ):
        hub = self.hub_manager.create_hub(name, inter.user, description)
        await inter.send(
            "Le hub a bien été créé !",
            embed=await hub.get_embed(self.bot),
            view=hub.get_view(),
        )
    
    @hub.subcommand(
        name="show",
        description="Affiche un hub."
    )
    async def hub_show(
        self,
        inter: nextcord.Interaction,
        hub_name: str = nextcord.SlashOption(
            name="hub",
            description="Le nom du hub à afficher",
            autocomplete=True,
            required=True,
        ),
    ) -> None:
        hub = self.hub_manager.get_hub_by_name(hub_name)
        if hub is None:
            if hub_name == gunibot.EMPTY_AUTOCOMPLETE:
                await inter.send(
                    "Je n'ai pas trouvé de hub correspondant à ta recherche... Utilise `/hub create` pour en créer un !",
                    ephemeral=True,
                )
            else:
                await inter.send(
                    "Je n'ai pas trouvé de hub avec ce nom ! Étrange... :thinking:"
                )
            return
        embed = await hub.get_embed(self.bot)
        await inter.send(
            embed=embed,
            view=hub.get_view(),
            ephemeral=True,
        )
    
    @hub_show.on_autocomplete('hub_name')
    async def hub_autocomplete(
        self,
        inter: nextcord.Interaction,
        focused_value: str,
    ) -> None:
        hub_names = [hub.name for hub in self.hub_manager.get_hubs(inter.user, focused_value)]
        if len(hub_names) == 0:
            return [gunibot.EMPTY_AUTOCOMPLETE]
        return hub_names

    @commands.Cog.listener()
    async def on_interaction(self, inter: nextcord.Interaction):
        if inter.type == nextcord.InteractionType.component:
            custom_id = inter.data['custom_id']
            
            if not custom_id.startswith('persistent:hub:'):
                return
            
            custom_id = custom_id[15:]
            hub = self.hub_manager.get_hub(custom_id.split(':')[-1])

            if custom_id.startswith('delete'):
                self.hub_manager.delete_hub(hub)

                view = hub.get_view()

                for item in view.children: # disable all buttons
                    if isinstance(item, nextcord.ui.Button):
                        item.disabled = True

                await inter.response.edit_message(
                    embed=await hub.get_embed(self.bot),
                    view=view,
                )

            elif custom_id.startswith('edit'):
                await inter.response.send_modal(
                    hub.get_modal(),
                )

def setup(bot: gunibot.Gunibot):
    bot.add_cog(Rolelink(bot))