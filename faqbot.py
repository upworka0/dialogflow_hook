import dialogflow
import os
from config import *
from models import Course, Base, Question, Answer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

    def __init__(self, project_id):
        self.project_id = project_id

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
            # create new answer object
            answer_obj = Answer(response=answer, question=que)
            session.add(answer_obj)
            session.commit()
        except:
            session.rollback()

    def run(self):
        """
        Running instance for all questions
        :return: None
        """

        ques = session.query(Question).all()
        for row in ques:
            que_text = ""
            if row.body == '':
                que_text = row.title
            else:
                que_text = row.body

            response = self.detect_intent_texts(que_text)
            self.store_answer(response, row)
            print("Question is `%s`" % que_text)
            print("Answer is `%s`\n" % response)


if __name__ == '__main__':
    bot = AnswerBot(project_id=DIALOGFLOW_PROJECT_ID)
    bot.run()
    print("ENDED!")