import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = True)
	email = Column(String(250), nullable = True)
	picture = Column(String(250), nullable = True)

	@property
	def serialize(self):
	#Returns object data in easily serializable format
		return {
			'id': self.id,
			'name': self.name,
			'email': self.email,
			'picture': self.picture,
		}


class Team(Base):
	__tablename__ = 'team'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
	#Returns object data in easily serializable format
		return {
			'id': self.id,
			'name': self.name,
			'user_id': self.user_id,
		}

class Employee(Base):
	__tablename__ = 'employee'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=True)
	level = Column(Integer, nullable=True)
	team_id = Column((Integer), ForeignKey('team.id'))
	team = relationship(Team)


	@property
	def serialize(self):
	#Returns object data in easily serializable format
		return {
			'id': self.id,
			'name': self.name,
			'level': self.level,
			'team_id': self.team_id,
		}

engine = create_engine('sqlite:///assets.db')

Base.metadata.create_all(engine)