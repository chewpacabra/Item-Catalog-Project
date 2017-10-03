from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Employee, Team, User

engine = create_engine('sqlite:///assets.db')
# Binds engine to metadata of Base class so declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Add 2 dummy users

user1 = User(name = "Robert Brenner", email = "rb3792@att.com")

session.add(user1)
session.commit()

# Building teams

team1 = Team(id = 1, name = "Brenner's Team", user_id = 1)

session.add(team1)
session.commit()

team2 = Team(id = 2, name = "Fonso's Team", user_id = 2)

session.add(team2)
session.commit()

team3 = Team(id = 3, name = "Matt's Team", user_id = 1)

session.add(team3)
session.commit()

# Add Employees

employee2 = Employee(name = "Robert Brenner", team_id = 1, level = 1, user_id = 1)

session.add(employee2)
session.commit()

employee3 = Employee(name = "Alfonso Saucedo", team_id = 2, level = 1, user_id = 2)

session.add(employee3)
session.commit()

employee4 = Employee(name = "Dyllon Barge", team_id = 2, level = 0, user_id = 2)

session.add(employee4)
session.commit()

employee5 = Employee(name = "Carlos Carreon", team_id = 2, level = 0, user_id = 2)

session.add(employee5)
session.commit()

employee6 = Employee(name = "Cory Conley", team_id = 2, level = 0, user_id = 2)

session.add(employee6)
session.commit()

employee7 = Employee(name = "Darren Coker", team_id = 1, level = 0, user_id = 1)

session.add(employee7)
session.commit()

employee8 = Employee(name = "Rodrick Cross", team_id = 1, level = 0, user_id = 1)

session.add(employee8)
session.commit()

employee9 = Employee(name = "Luis Flores", team_id = 1, level = 0, user_id = 1)

session.add(employee9)
session.commit()

employee9 = Employee(name = "Matthew Bolton", team_id = 3, level = 1, user_id = 1)

session.add(employee9)
session.commit()