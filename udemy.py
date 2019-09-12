from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer
import requests
from urllib.parse import urlencode
import json
from config import DB_URL, ACCESS_TOKEN
import logging
from pprint import pprint

logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


engine = create_engine(DB_URL)
engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

class Udemy:
    DB_CONFIG = 'mysql://root:password@localhost/udemy?charset=utf8mb4'
    BASE_URL = "https://www.udemy.com/instructor-api/v1/taught-courses/questions/?fields[question]=@all"

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

    def insert_db(self, dict):
        # insert course if not exists.
        course_id = dict['course']['id']
        course = session.query(Course).get(course_id)
        if not course:
            course_data = dict['course']
            course = Course(id=course_id, _class=course_data['_class'], title=course_data['title'], url=course_data['url'])
            session.add(course)
            session.commit()
            logging.info('new Course insertted! Course id is %s' % course_id)

        #insert question if not exists
        question_id = dict['id']
        question = session.query(Question).filter_by(question_id=question_id).first()

        if not question:
            question = Question(question_id=question_id, title=dict['title'], body=dict['body'], num_replies=dict['num_replies'],
                                num_follows=dict['num_follows'], num_reply_upvotes=dict['num_reply_upvotes'], created=dict['created'],
                                course=course)
            session.add(question)
            session.commit()
            self.total_count = self.total_count + 1
            # logging.info('new Question insertted! Question id is %s' % question_id)

    def get_request(self, dict={}):
        """
        get requests and insert into db
        :param dict: params of url
        :return: Boolean
        """
        url = self.BASE_URL + urlencode(dict) if self.next_url == '' else self.next_url
        logging.info("REQUEST to %s" % url)
        res = requests.get(url, headers=self.get_headers())
        response = res.json()
        if res.status_code > 200:
            logging.error("Error: %s " % response['detail'])
        else:
            try:
                self.next_url = response['next']
                for row in response['results']:
                    self.insert_db(row)
                if self.next_url:
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

    def start(self, dict={}):
        """
        Start function of Udemy
        :param dict: params of url
        :return: None
        """
        while self.get_request(dict=dict):
            print(self.next_url)

    def get_api_course_questions(self):
        URL = "https://www.udemy.com/instructor-api/v1/courses/950390/questions/"
        res = requests.get(URL, headers=self.get_headers())
        response = res.json()
        if res.status_code > 200:
            logging.error("Error: %s " % response['detail'])
        else:
            print("------------------ Course Questions ---------------------------")
            pprint(response)

    def get_api_taught_course_questions(self):
        URL = "https://www.udemy.com/instructor-api/v1/taught-courses/questions/?course=950390&ordering=recency&page=2&page_size=12&status=unread&fields[question]=@all"
        res = requests.get(URL, headers=self.get_headers())
        response = res.json()
        if res.status_code > 200:
            logging.error("Error: %s " % response['detail'])
        else:
            print("------------------ Taught Couse Questions ---------------------------")
            pprint(response)


    def get_api_answers(self, course_id, question_id):
        URL = "https://www.udemy.com/instructor-api/v1/%s/questions/%s/replies/" % (course_id, question_id)
        res = requests.get(URL, headers=self.get_headers())
        response = res.json()
        if res.status_code > 200:
            logging.error("Error: %s " % response['detail'])
        else:
            print("------------------ Replies ---------------------------")
            pprint(response)


client = Udemy(access_token=ACCESS_TOKEN)

# # testing with test.json file
# client.test_with_json('test.json')

# url params
# dict ={
#     "page_size": 100,
#     "status": "unread",
#     "course": 950390,
#     "ordering": "recency"
# }
# client.start(dict)

client.get_api_course_questions()
print("----------------------------------------------")
client.get_api_taught_course_questions()