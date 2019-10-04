from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer
import requests
from urllib.parse import urlencode
import json
from config import DB_URL, ACCESS_TOKEN, COURSE_NUM
import logging
import time
import datetime

logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


engine = create_engine(DB_URL)
engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

class Udemy:
    QUE_URL = "https://www.udemy.com/instructor-api/v1/taught-courses/questions/?"

    max_page_size = 100
    next_url = ''
    access_token = ""
    total_count = 0

    def __init__(self, access_token):
        self.access_token = access_token

    def get_headers(self):
        return {
            "Authorization": "bearer %s" % self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def insert_db(self, dict, course_id):
        # insert course if not exists.
        # course_id = dict['course']['id']
        course = session.query(Course).get(course_id)
        if not course:
            course_data = dict['course']
            course = Course(id=course_id, _class=course_data['_class'], title=course_data['title'], url=course_data['url'], str_id=dict['course']['id'])
            session.add(course)
            session.commit()
            logging.info('new Course insertted! Course id is %s' % course_id)

        #insert question if not exists
        str_id = dict['id']
        question = session.query(Question).filter_by(str_id=str_id).first()

        if not question:
            question = Question(str_id=str_id, title=dict['title'], body=dict['body'], num_replies=dict['num_replies'],
                                num_follows=dict['num_follows'], num_reply_upvotes=dict['num_reply_upvotes'], created=dict['created'],
                                course=course, replied=False)
            self.total_count = self.total_count + 1
        else:
            question.timestamp = datetime.datetime.now()

        session.add(question)
        session.commit()
        logging.info('new Question insertted! Question id is %s' % str_id)

    def get_request(self, dict={}):
        """
        get requests and insert into db
        :param dict: params of url
        :return: Boolean
        """
        url = self.QUE_URL + urlencode(dict) if self.next_url == '' or self.next_url == None else self.next_url


        url = "%s&fields[question]=@all" % url
        logging.info("REQUEST to %s" % url)

        res = requests.get(url, headers=self.get_headers())
        response = res.json()
        if res.status_code > 200:
            logging.error("Error: %s " % response['detail'])
        else:
            logging.info("response: %s " % json.dumps(response))
            try:
                for row in response['results']:
                    self.insert_db(row, dict['course'])
                self.next_url = response['next']
                if self.next_url and self.next_url != "null" and self.next_url is not None:
                    return True
            except Exception as e:
                logging.error("Error in response parse: %s " % str(e))
        logging.info('Total new Question Count is %s' % self.total_count)
        return False

    def test_with_json(self, filepath):
        """
        Read Json from file and insert into db
        :param filepath: path of json file
        :return: Boolean
        """

        file = open('test.json', 'r')
        json_text = file.read()

        response = json.loads(json_text)
        self.next_url = response['next']
        for row in response['results']:
            self.insert_db(row)
        if self.next_url:
            return True
        return False

    def start(self):
        """
        Start function of Udemy
        :param dict: params of url
        :return: None
        """
        courses = session.query(Course).all()
        for course in courses:
            dict ={
                "page_size": 100,
                "status": "unresponded",
                "course": course.id,
                "ordering": "recency"
            }
            while self.get_request(dict=dict):
                time.sleep(1)
                print(self.next_url)


client = Udemy(access_token=ACCESS_TOKEN)

# # testing with test.json file
# client.test_with_json('test.json')

client.start()

# client.get_api_course_questions()
# print("----------------------------------------------")
# client.get_api_taught_course_questions()