from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer
from urllib.parse import urlencode
import json
from config import DB_URL, ACCESS_TOKEN
import logging
logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

engine = create_engine(DB_URL)
engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


class UdemyAnswer:
    DB_CONFIG = 'mysql://root:password@localhost/udemy?charset=utf8mb4'
    BASE_URL = "https://www.udemy.com/instructor-api/v1/courses/{course_id}/questions/{question_id}/replies/"
    access_token = ""

    def __init__(self, access_token):
        self.access_token = access_token

