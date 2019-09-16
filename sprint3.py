from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer
from urllib.parse import urlencode
import json
import requests
from pprint import pprint

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
    """
        https://www.udemy.com/developers/instructor/methods/post-api-course-question-replies-list/
        POST /instructor-api/v1/courses/{course_id}/questions/{question_id}/replies/
    """

    BASE_URL = "https://www.udemy.com/instructor-api/v1/courses/{0}/questions/{1}/replies/"
    access_token = ""

    def __init__(self, access_token):
        self.access_token = access_token

    def get_headers(self):
        return {
            "Authorization": "bearer %s" % self.access_token,
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "application/json, text/plain, */*"
        }

    def _answer(self, course_id, question_id, user_id, answer_text):
        payload = {
            "body": answer_text
        }

        url = self.BASE_URL.format(course_id, question_id)
        logging.info("REQUEST to %s " % url)
        logging.info("REQUEST payload : %s" % json.dumps(payload))
        print(url)
        print(payload)
        res = requests.post(url, data=payload, headers=self.get_headers())
        response = res.json()
        if res.status_code > 400:
            logging.error("Error: %s " % response['detail'])
        else:
            logging.info("Response : %s" % json.dumps(response))
        pprint(response)


if __name__ == '__main__':
    udemy = UdemyAnswer(access_token=ACCESS_TOKEN)
    # udemy._answer(1,1,1,"test")
    udemy._answer("x01qeGSHjE7B-Vi7kqfXvCTlw==", "x01RuwcQJm4bPC3ngSsPSv0kg==", 1, "test")

    """
        Testing:
            >>>            
            course = "x01qeGSHjE7B-Vi7kqfXvCTlw=="
            question_id = "x01RuwcQJm4bPC3ngSsPSv0kg=="
            answer = "Attribute Error is no problem"
            user_id = None
            udemy._answer(course, question_id, user_id, answer)
    """