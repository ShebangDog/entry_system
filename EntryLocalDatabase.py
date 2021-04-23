import dataclasses
import sqlite3
from enum import Enum

import datetime as datetime


class Entry(Enum):
    IsExit = 0
    IsEntry = 1


@dataclasses.dataclass
class Student:
    id: str
    name: str


@dataclasses.dataclass
class AccessData:
    student: Student
    datetime: datetime


class EntryLocalDatabase:
    def __init__(self):
        self.name = 'nunomura-lab-students'
        self.conn = sqlite3.connect(self.name)
        self.cur = self.conn.cursor()
        self.member_table = MemberTable(self.cur, self.conn)
        self.access_table = AccessTable(self.cur, self.conn)
        self.log_table = LogTable(self.cur, self.conn)

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def registry(self, student, is_entry):
        self.member_table.registry(student)
        self.access_table.registry(student, is_entry)

    def entry(self, access_data):
        self.access_table.entry(access_data)

    def exit(self, access_data):
        self.access_table.exit(access_data)

    def save_log(self, access_data):
        is_entry = self.access_table.get_is_entry(access_data.student)
        self.log_table.save_log(access_data, Entry.IsEntry if is_entry == Entry.IsExit else Entry.IsExit)


class MemberTable:
    def __create_table(self):
        self.cur.execute(
            'CREATE TABLE {0}(student_id STRING PRIMARY KEY,name STRING)'
                .format(self.table_name)
        )

    def __init__(self, cur, conn):
        self.cur = cur
        self.conn = conn
        self.table_name = "member"

        try:
            self.__create_table()
        except Exception:
            pass

    def registry(self, student):
        self.cur.execute(
            'INSERT INTO {0}(student_id, name) VALUES("{1}", "{2}")'
                .format(self.table_name, student.id, student.name)
        )
        self.conn.commit()


class AccessTable:
    def __init__(self, cur, conn):
        self.cur = cur
        self.conn = conn
        self.table_name = "access"

        try:
            self.__create_table()
        except Exception:
            pass

    def __create_table(self):
        self.cur.execute(
            'CREATE TABLE {0}(student_id STRING PRIMARY KEY,is_entry INTEGER)'
                .format(self.table_name)
        )

    def registry(self, student, is_entry):
        self.cur.execute(
            'INSERT INTO {0}(student_id, is_entry) VALUES("{1}", "{2}")'.format(
                self.table_name,
                student.id,
                is_entry.value
            )
        )

    def entry(self, access_data):
        self.cur.execute(
            'UPDATE {0} SET is_entry = "{1}" WHERE student_id = "{2}"'
                .format(self.table_name, Entry.IsEntry.value, access_data.student.id)
        )
        self.conn.commit()

    def exit(self, access_data):
        self.cur.execute(
            'UPDATE {0} SET is_entry = "{1}" WHERE student_id = "{2}"'
                .format(self.table_name, Entry.IsExit.value, access_data.student.id)
        )
        self.conn.commit()

    def get_is_entry(self, student):
        try:
            for row in self.cur.execute(
                    'SELECT * FROM {0} WHERE student_id = "{1}"'.format(self.table_name, student.id)
            ):
                return Entry(row[1])

            raise Exception
        except Exception as e:
            print("error: on get_is_entry function => ", e)
            return Entry.IsExit


class LogTable:
    def __create_table(self):
        self.cur.execute(
            'CREATE TABLE {0}(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id STRING, is_entry INTEGER, datetime STRING)'
                .format(self.table_name)
        )

    def __init__(self, cur, conn):
        self.cur = cur
        self.conn = conn
        self.table_name = "log"

        try:
            self.__create_table()
        except Exception:
            pass

    def save_log(self, access_data, is_entry):
        self.cur.execute(
            'INSERT INTO {0}(student_id, is_entry, datetime) VALUES("{1}", "{2}", {3})'.format(
                self.table_name,
                access_data.student.id,
                is_entry.value,
                access_data.datetime.strftime('%Y%m%d')
            )
        )
        self.conn.commit()
