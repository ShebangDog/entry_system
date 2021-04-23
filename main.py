import datetime
import sqlite3
import time

import nfc
import requests

from EntryLocalDatabase import EntryLocalDatabase, Entry, Student, AccessData

# 学生証のサービスコード
service_code = 0x120B


# LINENotifyのBot
class LINENotifyBot:
    API_URL = 'https://notify-api.line.me/api/notify'

    def __init__(self, access_token):
        self.__headers = {'Authorization': 'Bearer ' + access_token}

    def send(self, message):
        payload = {'message': message}

        response = requests.post(
            LINENotifyBot.API_URL,
            headers=self.__headers,
            data=payload,
        )


# 学生番号の読み取り
def on_connect_nfc(tag):
    if isinstance(tag, nfc.tag.tt3.Type3Tag):
        try:
            sc = nfc.tag.tt3.ServiceCode(service_code >> 6, service_code & 0x3f)
            bc = nfc.tag.tt3.BlockCode(0, service=0)
            data = tag.read_without_encryption([sc], [bc])
            sid = data[0:8].decode()
            global student_id
            student_id = sid
        except Exception as e:
            print("error: %s" % e)
    else:
        print("error: tag isn't Type3Tag")


def main():
    local_database = EntryLocalDatabase()
    clf = nfc.ContactlessFrontend('usb')

    while True:
        dt_now = datetime.datetime.now()
        clf.connect(rdwr={'on-connect': on_connect_nfc})
        student = Student(student_id, "yamada")
        access_data = AccessData(student, dt_now)
        try:
            local_database.registry(student, Entry.IsEntry)
        except sqlite3.IntegrityError:
            print(student.id, " is already registered")

        local_database.save_log(access_data)
        is_entry = local_database.get_is_entry(student)

        if is_entry == Entry.IsEntry:
            info = "退室しました"
            local_database.exit(access_data)
        else:
            info = "入室しました"
            local_database.entry(access_data)

        # XXXXの部分は取得したAPI keyを貼り付けてください
        bot = LINENotifyBot(access_token='XXXX')
        bot.send(message=student_id + info)

        print(dt_now)
        print(student_id + info)
        time.sleep(5)


if __name__ == "__main__":
    main()
