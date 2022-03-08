from __future__ import annotations
from typing import TYPE_CHECKING
import sqlalchemy
import sqlalchemy.orm

if TYPE_CHECKING:
    from .bot import Gunibot

__all__ = [
    "Database",
    "Base",
]

Base = sqlalchemy.orm.declarative_base()

class Database:
    def __init__(self, bot: Gunibot) -> None:
        self.bot = bot
        self.models = []
        self.Base = Base
        self.engine = sqlalchemy.create_engine(
            f"{self.bot.configuration.database_type}://{self.bot.configuration.database_location}/{self.bot.configuration.database_path}"
        )
        
    def connect(self) -> None:
        self.Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session: sqlalchemy.orm.Session = self.Session()
    
    def close(self) -> None:
        self.session.close()

    def add(self, object: Base) -> None:
        if not issubclass(object, Base):
            raise ValueError("object must be a subclass of Base")
        if object not in self.models:
            self.models.append(object)
    
    def create_all(self) -> None:
        for object in self.models:
            object.metadata.create_all(self.engine)