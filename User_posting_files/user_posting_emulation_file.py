import requests
from time import sleep
import random
from multiprocessing import Process
import boto3
import json
import sqlalchemy
from sqlalchemy import text
from datetime import datetime, date, time


random.seed(100)


def datetime_handler(obj):
    if isinstance(obj, (datetime, date, time)):
        return str(obj)


class AWSDBConnector:

    def __init__(self):

        self.HOST = "pinterestdbreadonly.cq2e8zno855e.eu-west-1.rds.amazonaws.com"
        self.USER = 'project_user'
        self.PASSWORD = ':t%;yCY3Yjg'
        self.DATABASE = 'pinterest_data'
        self.PORT = 3306

    def create_db_connector(self):
        engine = sqlalchemy.create_engine(
            f"mysql+pymysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DATABASE}?charset=utf8mb4")
        return engine


new_connector = AWSDBConnector()


def run_infinite_post_data_loop():
    while True:
        sleep(random.randrange(0, 2))
        random_row = random.randint(0, 11000)
        engine = new_connector.create_db_connector()

        with engine.connect() as connection:

            pin_string = text(
                f"SELECT * FROM pinterest_data LIMIT {random_row}, 1")
            pin_selected_row = connection.execute(pin_string)

            for row in pin_selected_row:
                pin_result = dict(row._mapping)

            geo_string = text(
                f"SELECT * FROM geolocation_data LIMIT {random_row}, 1")
            geo_selected_row = connection.execute(geo_string)

            for row in geo_selected_row:
                geo_result = dict(row._mapping)

            user_string = text(
                f"SELECT * FROM user_data LIMIT {random_row}, 1")
            user_selected_row = connection.execute(user_string)

            for row in user_selected_row:
                user_result = dict(row._mapping)

            # print(pin_result)
            # print(geo_result)
            # print(user_result)

            # date_joined_dt = user_result['date_joined']
            # # print(date_joined_dt, type(date_joined_dt))
            # user_result['date_joined'] = str(date_joined_dt)

            # print(pin_result)
            # print(geo_result)
            # print(user_result)

            # for thing in user_result.keys():
            #     print(thing, type(thing))

            with open('info/datatest.json', 'a') as f:
                f.write("{result: pin }\n")
                json.dump(pin_result, f)
                f.write("{result: geo }\n")
                json.dump(geo_result, f, default=datetime_handler)
                f.write("{result: user }\n")
                json.dump(user_result, f, default=datetime_handler)


if __name__ == "__main__":
    run_infinite_post_data_loop()
    print('Working')
