from flask import Flask, request, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer, BotSession
from config import *


# Sqlalchemy Configuration
engine = create_engine(DB_URL, connect_args={'check_same_thread': False})
engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Logging configuration
import logging
logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


app = Flask(__name__)

@app.route('/')
def index():
    """
    Return all answers as JSON format
    """
    res = session.query(Answer).all()
    session.rollback()
    data = []
    for row in res:
        row_data = {
            "question": row.id,
            "session": row.session.session,
            "answer": row.response,
            "created": row.created
        }
        data.append(row_data)
    return jsonify(data)


def check_bot_session(sess):
    if session.query(BotSession).get(sess):
        return True
    return False


def get_question_by_session(sess):
    sess = session.query(BotSession).get(sess)
    question_id = sess.question_id
    ques = Question.query.get(question_id)
    return ques


def update_session(sess):
    sess_obj = BotSession.query.get(sess)
    if sess_obj:
        sess_obj.question_id = sess_obj.question_id + 1
    else:
        sess_obj.question_id = 1
    session.commit()


def store_answer(ans_text, sess):
    """
    Store answer and return BotSession
    """
    que_obj = get_question_by_session(sess)
    botsess = BotSession.query.get(sess)

    # create new answer object
    answer_obj = Answer(response=ans_text, question=que_obj, session=botsess)
    session.add(answer_obj)
    session.commit()


# function for responses
def results():
    req = request.get_json(force=True)
    print(req)

    sess = req.get('session')
    logging.info('Session is %s' % sess)
    if check_bot_session(sess):
        ans_text = req.get('queryResult').get('parameters').get('any')
        store_answer(ans_text=ans_text, sess=sess)
        logging.info('Answer for session %s is %s' % (sess, ans_text))
    update_session(sess=sess)
    ques_obj = get_question_by_session(sess=sess)
    logging.info('Next Question for session %s is %s' % (sess, ques_obj.body))
    return {'fulfillmentText': ques_obj.body}


# create a route for webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    return make_response(jsonify(results()))


# run the app
if __name__ == '__main__':
    app.run(debug=True)
