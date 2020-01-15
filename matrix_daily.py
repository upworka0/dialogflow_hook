from sqlalchemy import create_engine,extract
from sqlalchemy.orm import sessionmaker
from models import Course, Base, Question, Answer, Matrix
import requests
import logging
from datetime import datetime, timedelta
import pandas as pd
from os import path
import csv

from config import *


logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

engine = create_engine(DB_URL)
engine.connect()
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def write_csv(lines, filename):
    """
    Write lines to csv named as filename
    """
    file_path = "/home/user/ftp/files/%s" % filename
    with open(file_path, 'w', encoding='utf-8', newline='') as writeFile:
        writer = csv.writer(writeFile, delimiter=',')
        writer.writerows(lines)

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


def get_months_matrix():
    start_year = 2019
    end_year = datetime.today().year
    end_month = datetime.today().month    
    _matrix_rows = []
    _header = ["Year", "Month"]
    courses = session.query(Course).all()
    for course in courses:
        _header.append(str(course.title) + "_month_num_total")
        _header.append(str(course.title) + "_month_num_replied")

    for year in range(start_year, end_year+1):        
        for month in range(1, 13):
            if year == end_year and month > end_month:
                break
            row = [year, month]
            for course in courses:
                total = session.query(Question).filter_by(course_id=course.id).filter(
                    extract('year', Question.created) == year).filter(
                    extract('month', Question.created) == month).count()
                replied = session.query(Question).filter_by(replied=True, course_id=course.id).filter(
                    extract('year', Question.created) == year).filter(
                    extract('month', Question.created) == month).count()
                # print(year, month, course.id, total, replied)
                # row.append(course.id)
                row.append(total)
                row.append(replied)
            _matrix_rows.append(row)
    write_csv([_header] + _matrix_rows, 'monthly_results.csv')

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
    get_months_matrix()
    df = analysis()
    # if path.exists('/home/user/ftp/files/course_total_daily.csv'):
    #     df.to_csv('/home/user/ftp/files/course_total_daily.csv', mode='a', index=False, header=False)
    # else:
    df.to_csv('/home/user/ftp/files/course_total_daily.csv', mode='a', index=False, header=True)    
except Exception as e:
    logging.info("Error: %s" % str(e))
print("ENDED!")