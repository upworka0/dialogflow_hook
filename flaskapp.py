from flask import Flask, request, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer, BotSession
from config import *
import os

# Sqlalchemy Configuration
# engine = create_engine(DB_URL) # Sqlite Connection
engine = create_engine(DB_URL)  ## Mysql Connection

engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Logging configuration

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)


@app.route('/')
def index():
    """
    Return all answers as JSON format
    """
    data = []
    try:
        res = session.query(Answer).all()
        for row in res:
            row_data = {
                "question": row.id,
                "session": row.session.session,
                "answer": row.response,
                "created": row.created
            }
            data.append(row_data)
    except Exception as e:
        print(e)
        session.rollback()

    return jsonify(data)


@app.route('/questions')
def questions():
    data = []
    try:
        res = session.query(Question).all()
        for row in res:
            row_data = {
                "question": row.question_id,
                "title": row.title,
                "body": row.body,
                "created": row.created
            }
            data.append(row_data)
    except Exception as e:
        print(e)
        session.rollback()

    return jsonify(data)


def extract_session(sess):
    return sess.split('/')[len(sess.split('/')) - 1]


def adjust_question(text):
    text = text.replace('<p>', ' ')
    text = text.replace('</p>', '                                  ')
    text = text.replace('<br/>', '                                  ')
    text = text.replace('<br>', '                                  ')
    text = text.replace('&nbsp;', ' ')
    print(text)
    return text


def check_bot_session(sess):
    res = session.query(BotSession).filter_by(session=sess).first()
    print(res)
    if res:
        return True
    return False


def get_question_by_session(sess):
    try:
        sess = session.query(BotSession).filter_by(session=sess).first()
        question_id = sess.question_id
        ques = session.query(Question).get(question_id)
        return ques
    except Exception as e:
        print(e)
        session.rollback()
        return None


def update_session(sess):
    try:
        sess_obj = session.query(BotSession).filter_by(session=sess).first()
        if sess_obj:
            sess_obj.question_id = sess_obj.question_id + 1
        else:
            sess_obj = BotSession(session=sess, question_id=1)
            session.add(sess_obj)
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()
        return None


def store_answer(ans_text, sess):
    """
    Store answer and return BotSession
    """
    try:
        que_obj = get_question_by_session(sess)
        botsess = session.query(BotSession).filter_by(session=sess).first()

        if que_obj and botsess:
            # create new answer object
            answer_obj = Answer(response=ans_text, question=que_obj, session=botsess)
            session.add(answer_obj)
            session.commit()
    except Exception as e:
        print(e)
        session.rollback()


# function for responses
def results():
    req = request.get_json(force=True)
    print(req)

    sess = extract_session(req.get('session'))
    logging.info('Session is %s' % sess)

    if check_bot_session(sess):
        ans_text = req.get('queryResult').get('parameters').get('any')
        store_answer(ans_text=ans_text, sess=sess)
        logging.info('Answer for session %s is %s' % (sess, ans_text))

    update_session(sess=sess)
    ques_obj = get_question_by_session(sess=sess)
    if ques_obj:
        # logging.info('Next Question for session %s is %s' % (sess, ques_obj.body))
        res = {
            'fulfillmentText': adjust_question(ques_obj.body) if ques_obj.body != "" else adjust_question(
                ques_obj.title)
        }
    else:
        res = {
            "outputContexts": [
                {
                    "name": "%s/%s" % (req.get('session'), "contexts/awaiting_questions"),
                    "lifespanCount": 0
                }
            ],
            'fulfillmentText': "There is no any question remaining! Thank you!"
        }
    print(res)
    return res


# create a route for web hook
@app.route('/webhook', methods=['POST'])
def webhook():
    return make_response(jsonify(results()))


# run the app
if __name__ == '__main__':
    app.run()
