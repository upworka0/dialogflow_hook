from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer, Matrix
import requests
import logging
from datetime import datetime, timedelta
import pandas as pd
from os import path

from config import *


logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

engine = create_engine(DB_URL)
engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def get_headers():
    global ACCESS_TOKEN
    return {
        "Authorization": "bearer %s" % ACCESS_TOKEN,
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json, text/plain, */*"
    }


def get_total_counts():
    courses = session.query(Course).all()
    counts = {}
    for course in courses:
        response = requests.get(
            'https://www.udemy.com/instructor-api/v1/courses/%s/questions/' % course.id,
            params={'q': 'requests+language:python',
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json;charset=utf-8"},
            headers=get_headers())
        res = response.json()
        counts[course.title] = res['count']
    return counts


def get_matrix(delta):
    """
        Matrix function
    """
    courses = session.query(Course).all()
    _matrix = {}
    for course in courses:
        _date = datetime.now().strftime("%Y-%m-%d")
        total = session.query(Question).filter_by(course_id=course.id).filter(
            Question.created > (datetime.now() - timedelta(delta))).count()

        replied = session.query(Question).filter_by(replied=True, course_id=course.id).filter(
            Question.created > (datetime.now() - timedelta(delta))).count()
        _matrix.update({course.title: {
            "num_replied": replied,
            "num_total": total,
            "id": course.id
        }})
    return _matrix


def analysis():
    analysis_data = {}
    today_data = get_matrix(delta=1)
    analysis_data.update({"today": today_data})

    # Analysis this week's Data
    week_data = get_matrix(delta=7)
    analysis_data.update({"week": week_data})

    # Analysis this month's Data
    month_data = get_matrix(365 / 12)
    analysis_data.update({"month": month_data})

    # Total counts for each course
    counts_data = get_total_counts()
    analysis_data.update({"total": counts_data})

    real_row = {}
    for key, val in today_data.items():
        real_row.update({
            key + "_today_num_replied": [val['num_replied']],
            key + "_today_num_total": [val['num_total']],
        })
    for key, val in week_data.items():
        real_row.update({
            key + "_week_num_replied": [val['num_replied']],
            key + "_week_num_total": [val['num_total']],
        })
    for key, val in month_data.items():
        real_row.update({
            key + "_month_num_replied": [val['num_replied']],
            key + "_month_num_total": [val['num_total']],
        })
    for key, val in counts_data.items():
        real_row.update({
            key + "_question_total": [val]
        })

    real_row.update({
        "Date": [pd.Timestamp.now()]
    })

    df = pd.DataFrame(real_row)
    return df

try:
    df = analysis()
    if path.exists('course_total_daily.csv'):
        df.to_csv('course_total_daily.csv', mode='a', index=False, header=False)
    else:
        df.to_csv('course_total_daily.csv', mode='a', index=False, header=True)
except Exception as e:
    logging.info("Error: %s" % str(e))
print("ENDED!")