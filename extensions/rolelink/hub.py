from __future__ import annotations
from typing import Iterable, List, Optional, Union

import base64

import sqlalchemy
import nextcord

from gunibot import Base, Gunibot, EMPTY_AUTOCOMPLETE

class HubModal(nextcord.ui.Modal):
    def __init__(self, hub: Hub):
        self.hub = hub
        super().__init__(
            "Modifier un hub de serveurs"
        )
        
        self.name = nextcord.ui.TextInput(
            "Nom",
            max_length=200,
            required=True,
            default_value=hub.name,
        )
        self.description = nextcord.ui.TextInput(
            "Description",
            style=nextcord.TextInputStyle.paragraph,
            required=False,
            default_value=hub.description,
        )
        self.add_item(self.name)
        self.add_item(self.description)
    
    async def callback(self, inter: nextcord.Interaction):
        if not self.hub.is_admin(inter.user):
            await inter.send(
                "Vous n'avez pas l'autorisation d'effectuer des modifications sur ce hub.",
                ephemeral=True,
            )
            return
        self.hub.name = self.name.value
        self.hub.description = self.description.value
        
        try:
            await inter.response.edit_message(
                embed=await self.hub.get_embed(inter.client),
                view=self.hub.get_view(),
            )
        except nextcord.NotFound:
            await inter.send(
                ":white_check_mark: Votre rappel a bien été modifié !",
                embed=await self.hub.get_embed(inter.client),
                view=self.hub.get_view(),
                ephemeral=True,
            )

class Hub(Base):
    __tablename__="rolelink_hubs"
    
    id: int = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: str = sqlalchemy.Column(sqlalchemy.String)
    description: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    admins: Iterable[Admin] = sqlalchemy.orm.relationship("Admin", back_populates="hub")
    
    @property
    def encoded_id(self) -> str:
        return base64.b64encode(self.id.to_bytes(4, byteorder='little')).decode('utf-8')
    
    def add_admin(
        self,
        bot: Gunibot,
        user: Union[nextcord.User, int]
    ) -> Admin:
        if isinstance(user, (nextcord.User, nextcord.Member)):
            user = user.id
        admin = Admin(hub_id=self.id, user=user)
        bot.database.session.add(admin)
        
        return admin

    async def get_embed(self, bot: Gunibot) -> nextcord.Embed:
        embed = nextcord.Embed(
            title=f"Hub de serveurs {self.name}",
            colour=0xF76000,
            description=self.description if self.description is not None else '',
        )
        admins = ""
        for admin in self.admins:
            user = await admin.get_user(bot)
            if len(admins) + len(user.mention) < 1023:
                admins += user.mention + "\n"
            else:
                admins += "…"
                break
        embed.add_field(
            name="Administrateurs",
            value=admins,
        )
        embed.set_thumbnail(url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/160/twitter/282/linked-paperclips_1f587-fe0f.png")
        
        return embed

    def get_view(self) -> nextcord.ui.View:
        view = nextcord.ui.View(timeout=0)
        
        view.add_item(
            nextcord.ui.Button(
                custom_id=f"persistent:hub:delete:{self.encoded_id}",
                style=nextcord.ButtonStyle.danger,
                label="Supprimer le hub",
                emoji="🗑",
            )
        )
        
        view.add_item(
            nextcord.ui.Button(
                custom_id=f"persistent:hub:edit:{self.encoded_id}",
                style=nextcord.ButtonStyle.secondary,
                label="Modifier le hub",
                emoji="✏",
            )
        )
        
        return view

    def get_modal(self):
        return HubModal(self)
    
    def is_admin(self, user: nextcord.User):
        for admin in self.admins:
            if admin.user == user.id:
                return True
        return False

class Admin(Base):
    __tablename__="rolelink_hub_admins"
    
    id: int = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )
    hub_id: int = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('rolelink_hubs.id'))
    user: int = sqlalchemy.Column(sqlalchemy.Integer)
    
    hub: Hub = sqlalchemy.orm.relationship("Hub", back_populates="admins")
    
    async def get_user(self, bot: Gunibot) -> nextcord.User:
        return await bot.get_or_fetch_user(self.user)

class HubManager:
    def __init__(
        self,
        bot: Gunibot,
    ) -> None:
        self.bot = bot
        
        self.bot.add_orm(Hub)
        self.bot.add_orm(Admin)
    
    def create_hub(
        self,
        name: str,
        author: Union[int, nextcord.Member, nextcord.User],
        description: str = None,
    ) -> Hub:
        
        hub = Hub(name=name, description=description)
        self.bot.database.session.add(hub)
        self.bot.database.session.commit()
        
        hub.add_admin(self.bot, author)
        self.bot.database.session.commit()
        
        return hub
    
    def get_hubs(
        self,
        user: Union[int, nextcord.Member, nextcord.User],
        startswith="",
    ) -> List[Hub]:
        if isinstance(user, (nextcord.Member, nextcord.User)):
            user = user.id
        
        hubs = []
        for admin in self.bot.database.session.query(
            Admin
        ).filter(
            Admin.user==user,
        ).all():
            if admin.hub.name.startswith(startswith):
                hubs.append(admin.hub)
        
        return hubs
    
    def get_hub_by_name(
        self, 
        name: str,
        user: int = None,
    ) -> Optional[Hub]:
        try:
            hubs = self.bot.database.session.query(
                Hub
            ).filter(
                Hub.name == name,
            ).all()
        except sqlalchemy.orm.exc.NoResultFound:
            raise None
        else:
            if user is not None:
                user_hubs = []
                admins = self.bot.database.session.query(
                    Admin
                ).filter(
                    Admin.user == user,
                ).all()
                for admin in admins:
                    if admin.hub in hubs:
                        user_hubs.append(admin.hub)
                hubs = user_hubs
            if len(hubs) > 0:
                return hubs[0]
            else:
                return None
    
    def get_hub_by_id(self, id: int) -> Hub:
        try:
            return self.bot.database.session.query(
                Hub
            ).filter(
                Hub.id==id,
            ).one()
        except sqlalchemy.exc.NoResultFound:
            return None
    
    def get_hub(self, raw_custom_id: str) -> Hub:
        custom_id = self.bot.get_int_from_base64(raw_custom_id)
        return self.get_hub_by_id(custom_id)

    def delete_hub(self, hub: Hub):
        self.bot.database.session.delete(hub)
