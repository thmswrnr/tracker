import datetime
import sqlite3
from dataclasses import dataclass

import pandas as pd

from log_helper import log_func


def generate_db_handler(db_name):
    return SqliteHandler(db_name)


@dataclass
class Record(object):
    date: datetime.datetime
    activity: str
    reps: int
    weight: float
    distance: float
    time: datetime.time


class SqliteHandler(object):
    @log_func()
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name + ".sqlite", check_same_thread=False)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    @log_func()
    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records(
                date DATETIME,
                activity TEXT,
                reps INTEGER,
                weight FLOAT,
                time TIME,
                distance FLOAT)
            """
        )

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS activities(activity TEXT, UNIQUE(activity))"
        )

    def save_tables(self):
        pass

    @log_func()
    def add_record(self, record):
        self.cursor.execute(
            f"""
            INSERT INTO records VALUES(
                '{record.date}',
                '{record.activity}',
                '{record.reps}',
                '{record.weight}',
                '{record.time}',
                '{record.distance}')
            """
        )
        self.connection.commit()

    @log_func()
    def add_activity(self, activity, act_type):
        self.cursor.execute(
            f"INSERT OR IGNORE INTO activities VALUES('{activity}', '{act_type}')"
        )
        self.connection.commit()

    @log_func()
    def get_records(self):
        return pd.read_sql_query("SELECT * from records", self.connection).sort_values(
            "date"
        )

    @log_func()
    def get_activities(self):
        return pd.read_sql_query(
            "SELECT * from activities", self.connection
        ).sort_values("activity")
