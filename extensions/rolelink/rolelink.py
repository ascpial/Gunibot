import sqlalchemy
from gunibot import Base

class Rolelink(Base):
    __tablename__="rolelink"
    
    id: int = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name: str = sqlalchemy.Column(sqlalchemy.String)
    
    roles = sqlalchemy.orm.relationship("Role", back_populates="rolelink")

class Role(Base):
    __tablename__="rolelink_role"
    
    rolelink: int = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("rolelink.id"))
    id: int = sqlalchemy.Column(sqlalchemy.BigInteger)
    guild: int = sqlalchemy.Column(sqlalchemy.BigInteger)
    
    rolelink: Rolelink = sqlalchemy.orm.relationship("Rolelink", back_populates="roles")