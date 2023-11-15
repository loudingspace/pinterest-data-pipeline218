import requests
from time import sleep
from datetime import datetime, date, time
import random
from multiprocessing import Process
import boto3
import json
import sqlalchemy
from sqlalchemy import text

'''
Milestone 5, Step 1

Modify the user_posting_emulation.py to send data to your Kafka topics using your API Invoke URL. You should send data from the three tables to their corresponding Kafka topic.
'''


random.seed(100)


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


def datetime_handler(obj):
    if isinstance(obj, (datetime, date, time)):
        return str(obj)


def send_to_kafka(my_dict, topic):
    ''' Sends the dict to Kafka

    Parameter: dict
    '''

    example_df1 = {
        "ind": 7528,
        "first_name": "Abigail",
        "last_name": "Ali",
        "age": 20,
        "date_joined": "2015-10-24 11:23:51",
    }

    INVOKE_URL = "https://fi8pwye1ta.execute-api.us-east-1.amazonaws.com/test/topics/0af8d0adfd13."

    '''    
    user = "0af8d0adfd13.user"
    pin = "0af8d0adfd13.pin"
    geo = "0af8d0adfd13.geo"
    '''

    # create value dict from supplied my_dict dictionary

    keys_list = my_dict.keys()
    values_dict = {}
    for k in keys_list:
        values_dict[k] = my_dict[k]

    print('values_dict: :\t', values_dict)

    # To send JSON messages you need to follow this structure
    payload = json.dumps({
        "records": [
            {
                # Data should be send as pairs of column_name:value, with different columns separated by commas

                # "value": {"index": example_df["index"], "name": example_df["name"], "age": example_df["age"], "role": example_df["role"]}
                # {"ind": my_dict["ind"], "first_name": my_dict["first_name"], "last_name": my_dict["last_name"], "age": my_dict["age"], "date_joined": my_dict["date_joined"]}
                "value": values_dict
            }
        ]
    }, default=datetime_handler)  # we use the datetime_handler function we defined earlier to make sure datetime objects are strings

    headers = {"Content-Type": "application/vnd.kafka.json.v2+json",
               "Accept": "application/vnd.kafka.v2+json; q=0.9, application/json; q=0.5",
               "Access-Control-Allow-Origin": "*"}

    response = requests.request(
        "POST", INVOKE_URL + topic, headers=headers, data=payload)


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

            send_to_kafka(user_result, "user")
            send_to_kafka(pin_result, "pin")
            send_to_kafka(geo_result, "geo")

            print(pin_result)
            print(geo_result)
            print(user_result)


if __name__ == "__main__":
    run_infinite_post_data_loop()
    print('Working')
