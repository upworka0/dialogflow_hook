from config import DB_URL
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean, TIMESTAMP, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy import func

Base = declarative_base()


class Course(Base):
    __tablename__ = 'courses'
    # Here we define columns for the table courses
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True, autoincrement=False)     # course id
    _class = Column(String(50), nullable=True)                     # class id
    title = Column(String(250), nullable=True)                     # title of course
    url = Column(String(250), nullable=True)                       # url of course
    str_id = Column(String(250), unique=True, nullable=True)        # course Id as string

    def __str__(self):
        return self.id


class Question(Base):
    __tablename__ = 'questions'
    # Here we define columns for the table questions.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True, autoincrement=True)
    str_id = Column(String(250), unique=True, nullable=True)    # id of question as string format
    title = Column(String(250), nullable=False)                 # title of question
    body = Column(Text())                                       # body of question
    num_replies = Column(Integer, nullable=True)                # count of replies
    num_follows = Column(Integer, nullable=True)                # count of follows
    num_reply_upvotes = Column(Integer, nullable=True)          # count of upvotes replied
    created = Column(String(20))                                # created date
    course_id = Column(Integer, ForeignKey('courses.id'))       # id of course table
    course = relationship(Course)                               # foreignkey of course
    replied = Column(Boolean, default=False)                    # flag for reply
    duplicated = Column(Integer, default=0)      # duplication count
    timestamp = Column(TIMESTAMP, nullable=False)  # created date

    def __str__(self):
        return self.title


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    response = Column(Text())                                   # Answer text
    question_id = Column(Integer, ForeignKey('questions.id'))   # id of qeustion
    question = relationship(Question)                           # foreignkey of question
    created = Column(DateTime(), nullable=False,
                        server_default=func.current_timestamp(),
                        server_onupdate=func.current_timestamp())  # created date

    def __str__(self):
        return self.response


class Matrix(Base):
    __tablename__ = 'matrix'

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'))       # id of course table
    course = relationship(Course)                               # foreignkey of course
    num_replied = Column(Integer, nullable=True)                # count of answered questions
    num_total = Column(Integer, nullable=True)                  # count of total obtained questions
    created = Column(DateTime(), nullable=False,
                     server_default=func.current_timestamp(),
                     server_onupdate=func.current_timestamp())  # created date


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file. 'sqlite:///sqlalchemy_example.db'
engine = create_engine(DB_URL)
engine.connect()
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)