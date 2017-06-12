from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    instagram_id = Column(Integer, nullable=False, unique=True)
    instagram_username = Column(String(256), unique=True)


class UserImage(Base):
    __tablename__ = 'user_image'

    id = Column(Integer, primary_key=True)
    url = Column(String(2048), nullable=False)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


engine = create_engine('sqlite:///instagram_users.db')
Base.metadata.create_all(engine)
