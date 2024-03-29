import dialogflow
import os
from config import *
from models import Course, Base, Question, Answer, Matrix
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re
import requests
import json
import time
from datetime import datetime, timedelta
from pprint import pprint

import logging
logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Sqlalchemy Configuration
# engine = create_engine(DB_URL) # Sqlite Connection
engine = create_engine(DB_URL)  ## Mysql Connection

engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# ENV configuration
os.environ['DIALOGFLOW_PROJECT_ID'] = DIALOGFLOW_PROJECT_ID
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS


class AnswerBot:
    project_id = None
    session_id = "unique"
    language_code = "en"
    BASE_URL = "https://www.udemy.com/instructor-api/v1/courses/{0}/questions/{1}/replies/"
    access_token = ""
    course_num = 0


    def __init__(self, project_id, access_token=None, course_num=0):
        self.project_id = project_id
        self.access_token = access_token
        self.course_num = course_num

    def get_headers(self):
        return {
            "Authorization": "bearer %s" % self.access_token,
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "application/json, text/plain, */*"
        }

    def _answer(self, course_id, question_id, answer_text):
        payload = {
            "body": answer_text
        }

        url = self.BASE_URL.format(course_id, question_id)
        logging.info("REQUEST to %s " % url)
        logging.info("REQUEST payload : %s" % json.dumps(payload))
        print(url)

        res = requests.post(url, data=json.dumps(payload), headers=self.get_headers())
        response = res.json()
        if res.status_code > 400:
            logging.error("Error: %s " % response['detail'])
            # raise Exception('Error was occurred in answer to Udemy')
            return False
        elif res.status_code == 400:
            logging.error('Error: %s' % res.text)
        else:
            logging.info("Answer was sent to Udemy successfully, Answer id is %s" % response['id'])
        print("Answer was sent to Udemy successfully, Answer id is %s" % response['id'])
        return True

    def adjust_question(self, text):
        text = text.replace('<p>', ' ')
        text = text.replace('</p>', ' ')
        text = text.replace('<br/>', ' ')
        text = text.replace('<br>', ' ')
        text = text.replace('&nbsp;', ' ')
        text = text.replace('<pre>', ' ')
        text = text.replace('</pre>', ' ')

        while len(re.findall(r'\  ', text)) > 0:
            text = text.replace('  ', ' ')
        text = text.strip()

        return text.strip()

    def detect_intent_texts(self, text):
        """
        Send question and get answer from Dialogflow FAQBot
        :param text - string: question text
        :return: string
        """

        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(self.project_id, self.session_id)

        if text:
            text_input = dialogflow.types.TextInput(
                text=text, language_code=self.language_code)
            query_input = dialogflow.types.QueryInput(text=text_input)
            response = session_client.detect_intent(
                session=session, query_input=query_input)

            return response.query_result.fulfillment_text

    def store_answer(self, answer, que):
        """
        Store answer for each question
        :param answer: response from bot
        :param que: question object
        :return: None
        """
        try:
            # send answer to api endpoint
            status = self._answer(que.course.id, que.str_id, answer)

            if status:
                # create new answer object
                que.replied = True
                answer_obj = Answer(response=answer, question=que)
                session.add(answer_obj)
                session.commit()
        except:
            session.rollback()

    def unit(self, course_id):
        unexpected_answers = [
            "I didn't get that. Can you say it again?",
            "I missed what you said. What was that?",
            "Sorry, could you say that again?",
            "Sorry, can you say that again?",
            "Can you say that again?",
            "Sorry, I didn't get that. Can you rephrase?",
            "Sorry, what was that?",
            "One more time?",
            "What was that?",
            "Say that one more time?",
            "I didn't get that. Can you repeat?",
            "I missed that, say that again?"
        ]
        _date = datetime.now().strftime("%Y-%m-%d")
        ques = session.query(Question).filter_by(replied=False, course_id=course_id).filter(Question.timestamp.contains(_date)).all()

        cnt = 0

        for row in ques:
            if cnt > 80:
                cnt = 0
                time.sleep(60)

            que_text = ""
            if row.body == '':
                que_text = row.title
            else:
                que_text = row.body

            que_text = self.adjust_question(que_text)[0:255]
            response = self.detect_intent_texts(que_text)

            if response in unexpected_answers:
                response = "I'm sorry I didn't understand that! Can you please repeat the question and " \
                           "one of our TA's will respond shortly to assist <br> can we use that?"

            self.store_answer(response, row)
            print("Question is `%s`" % que_text)
            print("Answer is `%s`\n" % response)
            cnt = cnt + 1

    def run(self):
        """
        Running instance for all questions
        :return: None
        """
        courses = session.query(Course).all()
        for course in courses:
            self.unit(course.id)

        self.store_matrix() # store matrix
        analysis_data = self.analysis() # analysis matrix for today, weekly, monthly
        pprint(analysis_data)

    def store_matrix(self):
        """
        Matrix function
        """
        courses = session.query(Course).all()
        for course in courses:
            _date = datetime.now().strftime("%Y-%m-%d")
            total = session.query(Question).filter_by(course_id=course.id).filter(
                Question.timestamp.contains(_date)).count()
            replied = session.query(Question).filter_by(replied=True, course_id=course.id).filter(
                Question.timestamp.contains(_date)).count()

            # rec = session.query(Matrix).filter_by(course_id=course.id).first()
            # if rec:
            #     rec.num_total = total
            #     rec.num_replied = replied
            # else:
            mat = Matrix(course_id=course.id, num_total=total, num_replied=replied)
            session.add(mat)
            session.commit()
            print("-------------------------------Anysis Results-----------------------------")
            print(" Couse %s : Total Questions: %s, Replied Question: %s" % (course.id, total, replied))

    def get_analysis_data(self, matrixs):
        # Analysis Matrix Data
        _matrixs = {}
        _total = 0
        _replied = 0
        for mat in matrixs:
            course_id = str(mat.course_id)
            if course_id in _matrixs:
                _matrixs[course_id]['num_total'] = _matrixs[course_id]['num_total'] + mat.num_total
                _matrixs[course_id]['num_replied'] = _matrixs[course_id]['num_replied'] + mat.num_replied
            else:
                _matrixs.update({ course_id: {
                    "num_replied": mat.num_replied,
                    "num_total": mat.num_total,
                }})

            _total = _total + mat.num_total
            _replied = _replied + mat.num_replied

        _data = {
            "num_total": _total,
            "num_replied": _replied,
            "matrix": _matrixs
        }
        return _data

    def analysis(self):
        analysis_data = {}
        today_matrixs = session.query(Matrix).filter(Matrix.created > (datetime.now() - timedelta(days=1))).all()
        today_data = self.get_analysis_data(today_matrixs)
        analysis_data.update({"today": today_data})

        # Analysis this week's Data
        week_matrixs = session.query(Matrix).filter(Matrix.created > (datetime.now() - timedelta(weeks=1))).all()
        week_data = self.get_analysis_data(week_matrixs)
        analysis_data.update({"week": week_data})

        # Analysis this month's Data
        month_matrixs = session.query(Matrix).filter(Matrix.created > (datetime.now() - timedelta(days=365/12))).all()
        month_data = self.get_analysis_data(month_matrixs)
        analysis_data.update({"month": month_data})

        return analysis_data