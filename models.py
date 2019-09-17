from config import DB_URL
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


class Course(Base):
    __tablename__ = 'courses'
    # Here we define columns for the table courses
    # Notice that each column is also a normal Python instance attribute.
    id = Column(String(250), primary_key=True)
    _class = Column(String(50), nullable=False)
    title = Column(String(250), nullable=False)
    url = Column(String(250), nullable=False)

    def __str__(self):
        return self.id


class Question(Base):
    __tablename__ = 'questions'
    # Here we define columns for the table questions.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String(250), unique=True)
    title = Column(String(250), nullable=False)
    body = Column(Text())
    num_replies = Column(Integer, nullable=True)
    num_follows = Column(Integer, nullable=True)
    num_reply_upvotes = Column(Integer, nullable=True)
    created = Column(String(20))
    course_id = Column(String(250), ForeignKey('courses.id'))
    course = relationship(Course)
    replied = Column(Boolean, default=False)

    def __str__(self):
        return self.title


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    response = Column(Text())
    question_id = Column(Integer, ForeignKey('questions.id'))
    question = relationship(Question)
    created = Column(DateTime, onupdate=datetime.datetime.now)

    def __str__(self):
        return self.response

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file. 'sqlite:///sqlalchemy_example.db'
engine = create_engine(DB_URL)
engine.connect()
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)